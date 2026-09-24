---
version: "22.0"
# == THE SCHEMA LANGUAGE ==
schema_language:
  shape:                "scalar | mapping | list_of_entries | open_map_of_entries — the term's on-bean form"
  attrs:                "{<attr>: {required?, in, meaning}} — THE ATTRIBUTES: one record each, saying what the attribute is a position IN, whether it is required, and what it means — once, for the gate and the reader both. They describe each ENTRY of a list, an open map or a faceted mapping, and otherwise the mapping itself. An entry holds only the attributes declared here. See `attr_domains` for what `in:` may say."
  default_from:         "{registry, keyed_by, take} — inside an attribute's record: when the entry is SILENT, the attribute's value is READ from a registry row, the row selected by another attribute of the same entry. The registry stays the one owner of the usual value (a protocol's transport), and an entry states the attribute only when it differs. Like an aspect's default, a value that came from here never counts as OCCUPYING a position."
  cells:                "[{when, verdict|requires|expects, why}] — COMBINATIONS of what an entry holds. `verdict: incoherent` is an ERROR (the positions cannot both hold, so one is mis-stated); `verdict: in_breach` a WARNING (all can hold, and the state needs action). `requires: [...]` is an error when the entry sits in the cell and lacks those attributes; `expects: [...]` the same as a warning. `when` maps an attribute to the value it holds, or to `{starts_with: …}`; an aspect attribute is read at its EFFECTIVE position, stated or defaulted."
  attr_domains:
    values:      "in: [a, b, c] — one of a closed list written here"
    registry:    "in: { registry: <name>, take: <field> } — a row of a registry, so the registry OWNS the enum and no term restates it. `where: { <field>: <value> | [<values>] }` narrows it to the rows that say so — a PLACE system, a TRANSPORT-layer protocol — so one registry serves attributes that may name only some of its rows. `registry_from: <attr>` instead of `registry`: the registry is NAMED by another attribute of the same entry"
    aspect:      "in: { aspect: <name>, default: <position> } — a position on an opposition; the default applies when the entry is silent, and a default never counts as occupying the position"
    type:        "in: { type: <value type> } — a row of `value_types`: its pattern, and for a time type its system and unit"
    form_of:     "in: { form_of: <registry>, keyed_by: <attr>, take: pattern } — a position in the system a SIBLING attribute names, written in that system's ONE form. A row declaring `pattern: none` has deliberately no canonical form"
    system:      "in: { system: <anchor system> } — a position in ONE named system, in that system's one form. `form_of` asks a sibling WHICH system; this names it, for an attribute that is only ever in one"
    key_of:      "in: { key_of: <term> } — a key of that term's mapping ON THIS BEAN, or `<bean>:<key>` on another: a PART of a being, resolved by the gate. Not an edge — the being is reached by the refs the bean already states"
    entries:     "in: { entries: { <attr>: {required?, in, meaning} } } — entries INSIDE an entry: a list of them, or one mapping. Each is judged as an entry, by the attributes written here and by every rule an entry answers to. A ref inside one is resolved and draws no edge. `keyed_by: <attr>` beside `entries` says the list holds ONE entry per value of that attribute, and that the order of its entries carries nothing: two entries for one value are refused, and a merge compares the list in that attribute's order"
    bean_id:     "in: bean_id — the bare id of a bean this garden holds: resolved by the gate, and not an edge (an edge is a `ref`). `in: { bean_id: { gene: [<genos>, ...] } }` holds it to a bean of one of those gene"
    any:         "in: any — DELIBERATELY any value, because its type is another attribute's business (a record's `value` is whatever the tracked field holds). A decision, where `untyped` is a debt"
    pattern:     "in: { pattern: '<regex>' } — a form the TERM owns. With `soft: true` and a `why` it WARNS instead of refusing: the form a value SHOULD take while a corpus is migrated onto it"
    quantity:    "in: { quantity: <name> } — a MEASURED VALUE, written { count, unit }: a speed, an acceleration, an area, a data rate, an amount of money. The unit must measure the quantity named; `count` is a whole number or a decimal written as a string, in the form `value_types[count]` declares, so that no float reaches a canonical form and every reader holds it exactly. A quantity whose row takes its units from a registry (`units_from`) holds a count with at most the row's `digits` decimal places. `in: { quantity: any }` takes any."
    extent:      "in: extent — a bounded region of an aspect's domain (`extent_form`)"
    recurrence:  "in: recurrence — a repetition over a sequence: every Nth neighbour, every N units, or the same place in each cell of a level (`recurrence_form`)"
    ref:         "in: ref — a {bean|mapping: <id>[, field: <key>]} ref; the gate RESOLVES it (dangling = error)"
    pointer:     "in: { pointer: bean_field_pointer } — '<section>.<key>' on this bean, {bean, field} on another, or 'file:<path>'"
    id:          "in: id — the id of a bean or mapping: a key of the ref FORM itself, on a term whose value `is_ref`"
    prose:       "in: prose — a reason, a description, a remark. DELIBERATELY not a position: `why`, `what`, `note`. The reason IS the fact, and a schema for it would launder an opinion into a field. `in: { prose: named }` — one text, or several under the names of what each says: a map of named sayings, each one text"
    untyped:     "in: untyped — a position whose domain nobody has declared yet. A standing debt, written down so that an oversight and a decision stop looking alike"
  is_ref:               "true — the value (or each entry) IS ITSELF a {bean|mapping: <id>[, field: <key>]} ref, which the gate resolves (13.0)"
  path:                 "<dotted path> — the term governs a NESTED field rather than a top-level key named after it (`identity.status`, `identity.anchors[].class`, `provenance.src`). Added at 2.0 for the five core grammar enums and never declared here until 11.3."
  alt_form:             "{key, ref_fields} — an ALTERNATIVE whole-value form: a mapping carrying `key` takes this form INSTEAD of the faceted one, and the per-key rules stand down for it (the inherited `owned_by: {via: …}`). In use since the first schema language; declared 11.3."
  required:             "true — EVERY bean must carry the term (the root-axiom case; stronger than required_on_<axis>s)"
  required_on_gene:     "[<genos>...] — a bean of this genos MUST carry the term, non-empty. Keyed on the registry the key names (`gene`), whose rows name the bean attribute that holds the axis (`genos`)"
  only_on_gene:         "[<genos>...] — ONLY a bean of these gene may carry the term: a record that is about one genos of being is refused on any other"
  must_equal_genos_attr: "<attr> — the term's value must equal the bean's genos's <attr> in the `gene` registry (e.g. nature == genos.of_nature)"
  required_on_natures:  "[<nature>...] — same, keyed on nature instead of genos (reserved for P3; the interpreter already honours it)"
  required_on_roles:    "[<role>...] — same, keyed on ROLE. It needed no new interpreter key: the axis has always been read from the vocabulary key rather than named in code. What it DID need (7.0, human-ratified) is that an axis may be MULTI-VALUED — a machine holds one genos and one nature but SEVERAL roles — so the mechanism now reads an axis carried as a scalar, as a list of scalars, or as a list of entries each naming it, and fires if ANY held value matches. That generality is the reason `router` could stop being a genos."
  values:               "[<enum>...] — shape:scalar, the allowed values; also the enum this term EXPORTS to values_from/key_form"
  values_from:          "<term> | registry:<name>[].<field> — reuse another term's `values`, or a REGISTRY's own column, instead of restating it. A registry is its own enum owner: no term keeps a copy of its rows, and a position in it is addressed `registry:<name>`"
  key_form:             "kebab | values | values_from:<term> | values_from:registry:<name>[].<field> — the rule the KEYS of a mapping/open_map must satisfy"
  entry_one_of:         "[<attr>...] — each entry must carry at least one of these"
  expiry:               "{attr, notice, why} — ONE of this term's attrs is the position at which the thing LAPSES if nothing is done, and a reader should be warned before it. `notice` is HOW LONG BEFORE, as an EXTENT on `time`. `why` is the CONSEQUENCE, printed with the warning, because a date alone does not say what is lost. Read by bin/dmstale.py, not by the gate: a check whose answer changes with the calendar would make the gate non-deterministic, and a gate that fails on a Tuesday for no committed reason is a gate people disable. Deliberately NOT derived from an attribute's type: most dates a bean carries are `observed` or `as_of`, the day a fact was READ rather than the day it runs out. A term that does not declare this is never warned about, which is why a garden's own term can buy the warning its Tier-0 neighbour has. On a term whose value is a list or an open map, the attribute is each ENTRY's, and each entry is warned about by itself. `repeats: <attr>` names a sibling attribute `in: recurrence`: the position falls due again at each occurrence after `attr`, and the reader is warned before the next. `unless: {<attr>: [<values>]}` names the entries that no longer lapse — a debt already met."
  sums:                 "{whole: <attr> | [<attr>, ...], parts: <attr>.<attr>} — the PARTS of a quantity add up to its WHOLE: the parts are the named attribute of each entry inside `parts`' first attribute, the whole is the first of `whole` the entry states. Checked exactly, in fractions, whenever every count is known, and the parts must be in the whole's unit. An entry holding one part that states no amount holds the whole."
  on_sequence:          "<aspect> — the term's value is a walk on that SEQUENCE aspect (10.1): prose lines in list order, or step entries {id, do, next: [{to, when?}]} whose neighbourhoods are CLOSED; the gate refuses a `to` that names no step, a step nothing reaches, a branch with no condition, a routine with no end, and a loop when the aspect declares acyclic"
  dag:                  "true — this term's edges are positions on the `walk` sequence aspect (9.2: `dag` is that aspect's `term_key`), and they join the acyclic check BECAUSE that aspect declares `acyclic: true`"
  required_on_targets_of: "<term> — a bean that is the TARGET of that relation must carry this term (e.g. anything lived in must say what kind of habitat it is)"
  entry_must_match:     "[{attr, registry, keyed_by, take}] — an entry attr must equal a registry row's attr, the row selected by a field on the bean (e.g. the crown branch is fixed by the bean's nature)"
  entry_form_from_genos_attr: "<attr> — a genos that names ONE form in this attr PINS it: every entry must use it. A genos that names a LIST ALLOWS those forms beside the ordinary ones. Either way a form some genos names is RESERVED to the gene that name it, so no other bean can short-circuit its chain to the axiom (only genos:person may pin `crown`; an agreement may choose it)."
  governs_anchor:       "<key> — this term governs the FORMAT of anchors carrying that key; pairs with value_pattern or value_form"
  value_pattern:        "<regex> — the canonical form an anchor value must match (with canonical_note as the human statement of it)"
  value_form:           "ip — a format needing real parsing rather than a pattern"
  canonical_note:       "<prose> — with value_pattern: the human statement of the canonical form, printed in the refusal and by bin/dmrules.py. Prose for a reader; the gate checks the pattern, never this."
  enforced_by:          "core | none — an explicit statement for a term with NO schema: either CORE already enforces it, or there is genuinely nothing to check and this says why"
  poles:                "one axis (a contradictory PAIR), or a LIST of axes — a figure may be 1-dimensional, 2, 3 or more, and the gate derives the count rather than assuming it"
  facet_parity_with:    "<term> — this term and that one must carry the SAME facet keys (two arcs of one loop); one present without the other is a loose end"
  values_add:           "[<value>...] — GARDEN overlay only: APPEND values to a Tier-0 term's enum instead of replacing it, so the garden accounts only for what it added (8.2)"
  compare_form:         "upper-trim — with governs_anchor: the anchor is compared in this form for uniqueness (whitespace removed, uppercased), and a stored value not already in it warns (9.0)"
  value_in_registry:    "{registry, take} — with governs_anchor: the anchor value must be a ROW of that registry (a code of a published classification, 9.1)"
  inverse_of:           "<term>, or {term, cardinality: one-to-one | many-to-one} — this relation mirrors another and the gate holds the pair consistent so the convenience edge cannot drift from the fact. A BARE NAME means one-to-one and the mirror is enforced BOTH ways. `many-to-one` enforces only the functional direction: many instances point at one type, and the type cannot point back at all of them through a single mapping. Declare the cardinality; assuming a bijection is how a rule becomes unsatisfiable without anyone noticing."
# == NATURES: the root axiom layer ==
# == THE CROWN ==
crown:
  - branch: theos
    root: true
    meaning: "θεός — the one substance: every chain terminates here. NOT nameable on a bean: a being reaches theos only through its branch."
  - branch: physis
    meaning: "φύσις — the terminus for beings of the nature soma, bodies with extension in space"
  - branch: logos
    meaning: "λόγος — the terminus for beings of the nature lekton, what exists by being said and agreed"
  - branch: agape
    meaning: "ἀγάπη, love that does not possess — the terminus for beings of the nature empsychon, while alive; life-bounded, lapses at death or teardown. This branch is what makes a person UNOWNABLE BY ANOTHER BEING: no bean may hold a person, only agape, and only while they live. That is a protection, not a formality — the gate enforces it via person.ownership_form."
identity_policy:
  keyed_by: nature
  registry: natures
  applies_at_identity_status: confirmed
  anchor_key: term
  establishing_family: enforced
  anchor_attrs: [key, value, class, establishing, observed, provenance]
  minted:
    qualified_by: garden_id
    pattern: '^[0-9a-f]{12}/.+$'
    form: '^[a-z][a-z0-9-]*:.+$'
    form_genos: gene
    meaning: "A term whose `anchor` says `minted: true` admits names a garden gives. A value of it is such a NAME when it is written in `form`, `<genos>:<name>`, and `<genos>` is a genos the garden knows (`form_genos`: the law's `gene` and the garden's `local_gene`). BARE (`contract:shared-purchase`) a name identifies only within the garden that minted it: two gardens that minted the same bare name are shown to a person as candidates, never fused. QUALIFIED by the garden that minted it (`<garden_id>/contract:shared-purchase`) it identifies everywhere. A name is qualified once, by the garden that recorded the thing first, when the thing is to be known in another garden; a garden that takes it in keeps it byte for byte, and the prefix must be the garden's own id, or the `garden_id` of a `garden` bean it holds. A value in ANY OTHER form — a package name, a registry number, the UID an invitation carries, an id a provider assigned — was assigned outside every garden: it identifies wherever it is written, fuses as every anchor does, and is never qualified, because an identifier someone else assigned is not a garden's to put its name on."
# == THE MANIFEST: GARDEN.md, judged as itself ==
manifest:
  path: GARDEN.md
  attrs:
    garden:         { required: true, in: { type: kebab }, meaning: "the garden's name, for people. A name, not an identity: two gardens may carry the same one, and a garden's identity is the commit it germinated from (`garden_id`)" }
    extends:        { required: true, in: any, meaning: "the standard it pins, `std-vocab@<version>` — judged by the pin check" }
    daftar_release: { in: { pattern: '^(v[0-9]+\.[0-9]+\.[0-9]+|untagged ([0-9a-f]{4,40}|unknown))$' }, meaning: "the release it runs: a release tag, or `untagged <commit>` for a garden grown from a checkout that is on no tag (`untagged unknown` from a copy with no history); bin/dmupgrade.py moves it" }
    gardener:       { in: { bean_id: { gene: [person, org] } }, meaning: "the person — or organisation — who keeps the garden: a bean of the garden. Required once the garden holds a bean. The gardener ratifies here what an agent may not decide, and nothing outside the garden writes in it" }
    test:           { in: prose, meaning: "present when the garden is a rehearsal or a test, saying what it rehearses. Its beans are not facts about the world, and a proposal from it says so" }
    origin:         { in: prose, meaning: "where the garden began, for a reader" }
    policy:         { in: { prose: named }, meaning: "standing rules the gardener sets for work in the garden, in prose: one text, or each rule under a name of its own" }
# == WHAT THE LAW RETIRED, so a refusal can say where it went ==
retired:
  - { name: scope,         at: anchor,   instead: "nothing: whether a value identifies beyond its garden is said by its term (`anchor.minted`) and by its own form (`<genos>:<name>`, qualified `<garden_id>/<genos>:<name>`)" }
  - { name: authority,     at: anchor,   instead: "`provenance: { src, by, as_of }` on the anchor, only where its source differs from the bean's (scanned → observed, operator-asserted → asserted-by-human)" }
  - { name: between,       at: bean,     instead: "`parties`: an open map of the parties, each with the day it accepted" }
  - { name: agreement_ref, at: bean,     instead: "`words`: whether the agreement was written, spoken or not yet put into words, and where its words are" }
  - { name: conflict_rule, at: bean,     instead: "a clause of `clauses`, stated so that anyone applying it reaches the same answer" }
  - { name: balance,       at: bean,     instead: "nothing: what is owed is READ from `transactions` and `clauses` (bin/dmledger.py), never stored beside them" }
  - { name: attributes,    at: bean,     instead: "`details:` — the one bag for a datum that fits no term yet" }
  - { name: facets,        at: term,     instead: "the `facets` registry; a garden adds a facet as a row under `registry_additions.facets`" }
  - { name: values_consistent_with, at: schema, instead: "nothing: a list stated once, as a registry, needs no guard against its own copies" }
  - { name: seeds_from,    at: manifest, instead: "nothing: what a garden took in from another is in its journal, and in the captures on that garden's `garden` bean" }
  - { name: created,       at: manifest, instead: "nothing: when a garden began is its first commit" }
  - { name: models,        at: manifest, instead: "nothing: who wrote here is in the journal and in git" }
  - { name: kind,          at: bean,     instead: "`genos`: which genos of being the bean records, a row of `gene`. A mapping, which records no being, keeps its `kind`" }
  - { name: kinds,         at: law,      instead: "`gene`: the registry of the gene a bean may be, one row `- genos: <name>` each, with its `of_nature`" }
  - { name: local_kinds,   at: vocab,    instead: "`local_gene`: the rows a garden adds to `gene`, each `- genos: <name>` with its `of_nature`" }
  - { name: kinds,         at: bean_id,  instead: "`gene`: `in: { bean_id: { gene: [<genos>, ...] } }`" }
  - { name: form_kind,     at: minted,   instead: "`form_genos`: the registry a minted name's `<genos>` is a row of — `gene`" }
  - { name: required_on_kinds,         at: schema, instead: "`required_on_gene`" }
  - { name: only_on_kinds,             at: schema, instead: "`only_on_gene`" }
  - { name: must_equal_kind_attr,      at: schema, instead: "`must_equal_genos_attr`" }
  - { name: entry_form_from_kind_attr, at: schema, instead: "`entry_form_from_genos_attr`" }
  - { name: physical,      at: nature,   instead: "`soma`, σῶμα: a body with extension in space" }
  - { name: metaphysical,  at: nature,   instead: "`lekton`, λεκτόν: what exists by being said and agreed" }
  - { name: living,        at: nature,   instead: "`empsychon`, ἔμψυχον: the ensouled, while alive" }
  - { name: god,           at: crown,    instead: "`theos`, θεός: the root, still nameable on no bean" }
  - { name: nature,        at: crown,    instead: "`physis`, φύσις: the branch for a being of the nature soma" }
  - { name: love,          at: crown,    instead: "`agape`, ἀγάπη: the branch for a being of the nature empsychon" }
# == PROVENANCE: the record every fact carries, declared ==
provenance_record:
  attrs: [src, by, as_of, from, garden]
  from_attrs: [src, by, as_of, at]
  meaning: "who said a fact and how they know — on a bean, an anchor or an entry. `from` names the records the fact was TAKEN or COMPUTED from — a map of name to record, or a list of records, each {src, by, as_of, at?} with `at` pointing at the input (`<section>.<key>`, {bean, field}, or `file:`); a generated fact weighs as the weakest of them. `garden` is the `garden_id` of the garden the record was made in, where that is not this one: stamped once, when a proposal carries the fact across, and never changed."
natures:
  - nature: soma
    meaning: "σῶμα, a body — a being with extension in space: machines, hardware, sites"
    crown: physis
    establishing_anchor_family: [hardware]
    min_establishing_anchors: 1
  - nature: lekton
    meaning: "λεκτόν, the sayable — a being that exists by being said and agreed, constituted by meaning or agreement: code, products, orgs, domains, designs, contracts"
    crown: logos
    establishing_anchor_family: [logical]
    min_establishing_anchors: 1
  - nature: empsychon
    meaning: "ἔμψυχον, the ensouled — a being that strives to persist as itself: persons, and running instances while alive"
    crown: agape
    establishing_anchor_family: [logical]
    min_establishing_anchors: 1
# == ANCHOR SYSTEMS: the systems a POSITION may be stated in ==
# == A SYSTEM KNOWS ITS OWN SHAPE ==
# == WHERE, BY COORDINATES: bodies and coordinate reference systems ==
bodies:
  - { body: earth, mean_radius_m: 6371008.8, authority: "IUGG / IERS", meaning: "the Earth" }
  - { body: moon,  mean_radius_m: 1737400.0, authority: "IAU WGCCRE",  meaning: "the Moon" }
  - { body: mars,  mean_radius_m: 3389500.0, authority: "IAU WGCCRE",  meaning: "Mars" }
reference_system_kinds:
  - { kind: geographic-2d, meaning: "latitude and longitude on a body's ellipsoid or sphere" }
  - { kind: geographic-3d, meaning: "latitude, longitude and height above the ellipsoid" }
  - { kind: geocentric,    meaning: "X, Y, Z from the body's centre of mass" }
  - { kind: projected,     meaning: "a plane: the body's curved surface flattened by a named projection, in metres" }
  - { kind: vertical,      meaning: "a height or depth alone, against a named surface" }
  - { kind: engineering,   meaning: "a local frame fixed to a structure or a vehicle, moving with it" }
  - { kind: compound,      meaning: "a horizontal system and a vertical one together" }
reference_frames:
  - { frame: static,  meaning: "fixed to a tectonic plate (or to a body with none): ground keeps its coordinates" }
  - { frame: dynamic, meaning: "fixed to the whole body: ground drifts in it, and a coordinate needs its epoch" }
reference_systems:
  - { crs: "EPSG:4326", body: earth, kind: geographic-2d, frame: dynamic, axes: [lat, lon],    meaning: "WGS 84, latitude and longitude in degrees — what a satellite receiver reports" }
  - { crs: "EPSG:4979", body: earth, kind: geographic-3d, frame: dynamic, axes: [lat, lon, h], meaning: "WGS 84 with ellipsoidal height in metres. Ellipsoidal height is NOT height above sea level" }
  - { crs: "EPSG:4978", body: earth, kind: geocentric,    frame: dynamic, axes: [x, y, z],     meaning: "WGS 84 geocentric: metres from the Earth's centre of mass" }
  - { crs: "EPSG:4258", body: earth, kind: geographic-2d, frame: static,  axes: [lat, lon],    meaning: "ETRS89: fixed to the Eurasian plate, so European ground keeps its coordinates. It and WGS 84 drift apart by about 2.5 cm a year" }
  - { crs: "EPSG:3857", body: earth, kind: projected,     frame: dynamic, axes: [x, y],        meaning: "Web Mercator: the plane nearly every web map is drawn on. For DRAWING; distances in it are wrong away from the equator" }
  - { crs: "EPSG:32639", body: earth, kind: projected,    frame: dynamic, axes: [e, n],        meaning: "WGS 84 / UTM zone 39N: metres on a plane, good within its six-degree zone. One of sixty; named because a projected system is where metres are honest" }
  - { crs: "EPSG:5773", body: earth, kind: vertical,      frame: static,  axes: [H],           meaning: "EGM96 height: metres above the geoid, which is what `above sea level` means" }
  - { crs: "IAU_2015:30100", body: moon, kind: geographic-2d, frame: static, axes: [lat, lon], meaning: "the Moon (2015), planetocentric latitude and longitude on a sphere" }
  - { crs: "IAU_2015:49900", body: mars, kind: geographic-2d, frame: static, axes: [lat, lon], meaning: "Mars (2015), planetocentric latitude and longitude on a sphere" }
system_shape:
  neighbours: [none, counted, metered]
  reckoning:  [arithmetic, astronomical, observational, tabulated]
  crosswalk:  [computed, table, observed, none]
  day_begins: [midnight, sunset, noon]
  checked_by: [ipaddress-v4, ipaddress-v6]
system_registries:
  - { registry: anchor_systems,    key: system }
  - { registry: knowledge_schemes, key: scheme }
anchor_systems:
  - system: unix-filesystem
    dimension: place
    levels: open
    neighbours: none
    meaning: "a position in ONE NAMED HOST's UNIX filesystem. The host is part of the position: /home/user/addin on laptop-a and on laptop-b are different positions that print identically."
    pattern: '^(root:[a-z0-9][a-z0-9-]*(/[^:]*)?|[a-z0-9][a-z0-9.-]*:/.*)$'
    form_note: "root:<logical root>[/<relative path>] — resolved per host through that host's OWN root map, which is the form that survives a second machine; or <host>:<absolute path> stated outright where there is no root to hang it on"
    establishes: false
    why: "a path is reassignable and a tree can be checked out anywhere, so it CORROBORATES a location and never fixes it — the same rule that keeps `hostname` and `ip` corroborating-only"
    scope_note: "UNIX-SHAPED ON PURPOSE, and named so rather than called `host-filesystem`. C:\\Users\\user\\source\\repos\\addin cannot satisfy this pattern, and bending it in would give one system two formats — the exact reinvention the pattern rule exists to stop. `windows-filesystem` is declared beside it as a SEPARATE system for exactly that reason."
  - system: git-object-graph
    dimension: place
    neighbours: counted
    meaning: "a position in a repository's object graph — REACHABLE-FROM, not CHECKED-OUT-AT. This is the system `staleness_key: git-head:<sha>` was reaching for and missing: it compared against whatever tree the reader happened to have checked out, which is a fact about the reader and not about the analysis."
    pattern: '^[a-z0-9][a-z0-9._-]*@[0-9a-f]{7,40}$'
    form_note: "<repo>@<object id> — ONE spelling, always. Not git-head:, not git-commit:, not a bare sha: a sha with no repository named is a position with no system."
    establishes: true
    why: "an object id is content-addressed — it names the same object in every clone that has it, and no two clones can disagree about what it contains"
  - system: guix-store
    dimension: place
    neighbours: none
    meaning: "an item in a GNU Guix store: a build output named by a hash of EVERYTHING that went into building it. With git-object-graph, the second place system here in which a position says what it holds — for a BUILT thing, where git's is for a written one."
    pattern: '^/gnu/store/[0-9a-df-np-sv-z]{32}-[A-Za-z0-9+._?=-]+(/.*)?$'
    form_note: "`/gnu/store/<32-character hash>-<name>[/<path within it>]`"
    example: "/gnu/store/abcdfghijklmnpqrsvwxyz0123456789-hello-2.12.1"
    establishes: true
    why: "the hash is computed from the inputs, so the same position names the same build on every machine that has it"
  - system: physical
    dimension: place
    meaning: "where a PHYSICAL COPY is: a printed listing on a shelf, a disk in a drawer, a machine in a room. Declared because a codebase is not always a tree on a host — this ledger's own first rule is that it must survive being printed on paper and rescanned, and a printed copy has an address like anything else."
    pattern: none
    pattern_why: "a shelf, a room and a building have no canonical form this garden could impose without inventing one. Stating `none` is the honest position: the address is prose, and prose is what a human reads to go and find it."
    establishes: false
    why: "a physical copy can be moved, and two copies can sit in two places — a location corroborates which artefact you are holding, never which being it is a copy of"
  # == A CALENDAR IS NOT TIME ==
  - system: gregorian-civil
    dimension: time
    calendar: gregory
    reckoning: arithmetic
    day_begins: midnight
    example: "2026-09-20 14:05+03:30"
    levels: [ { level: year }, { level: month }, { level: day, unit: day }, { level: hour, unit: hour },
              { level: minute, unit: minute }, { level: second, unit: second }, { level: millisecond, unit: millisecond } ]
    resolves_through: geographic
    neighbours: metered
    restrictions: { lines: 1, order: partial }
    meaning: "a calendar position with a stated offset. Civil time RESOLVES THROUGH a geographic position, which is why it does not establish on its own."
    pattern: '^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2}(\.\d{1,3})?)?([+-]\d{2}:\d{2}|Z)?)?$'
    form_note: "YYYY-MM-DD[THH:MM[:SS[.sss]][+HH:MM|Z]] — the RESOLUTION actually held is stated separately in `unit` and is never inferred from how many digits were typed"
    establishes: false
    why: "a wall-clock reading without its geographic frame is ambiguous. The estate's own case: a cutoff computed on a +03 host was applied to UTC logs, and the watch reported zero hits while a campaign was running."
  - system: iso-week
    dimension: time
    calendar: iso8601
    reckoning: arithmetic
    day_begins: midnight
    same_ground_as: [gregorian-civil]
    crosswalk: computed
    levels: [ { level: year }, { level: week }, { level: day, unit: day } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial }
    meaning: "the ISO 8601 week calendar: the SAME days as the Gregorian calendar, partitioned into weeks instead of months. A week does not nest in a month, so this is a second partition and not a level of the first — which is why it is its own system."
    pattern: '^-?\d{4}-W\d{2}-[1-7]$'
    form_note: "`2026-W38-7`, optionally followed by a clock reading and its offset exactly as gregorian-civil writes one"
    example: "2026-W38-7"
    establishes: false
    why: "a calendar reading corroborates when something happened and never fixes which being did it — as for gregorian-civil"
  - system: julian-calendar
    dimension: time
    calendar: julian
    reckoning: arithmetic
    day_begins: midnight
    same_ground_as: [gregorian-civil]
    crosswalk: computed
    levels: [ { level: year }, { level: month, count: 12 }, { level: day, unit: day }, { level: hour, unit: hour }, { level: minute, unit: minute }, { level: second, unit: second }, { level: millisecond, unit: millisecond } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial }
    meaning: "the Julian calendar: a leap year every fourth year, with no century rule. Not among CLDR's identifiers; declared because the Coptic, Ethiopic and Hijri epochs are stated in it, and because a historical date before a country's Gregorian reform IS in it."
    pattern: '^julian:-?\d+-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2}(\.\d{1,3})?)?([+-]\d{2}:\d{2}|Z)?)?$'
    form_note: "`julian:2026-09-07`, optionally followed by a clock reading and its offset exactly as gregorian-civil writes one"
    example: "julian:2026-09-07"
    establishes: false
    why: "a calendar reading corroborates when something happened and never fixes which being did it — as for gregorian-civil"
  - system: persian-calendar
    dimension: time
    calendar: persian
    reckoning: arithmetic
    day_begins: midnight
    same_ground_as: [gregorian-civil]
    crosswalk: computed
    levels: [ { level: year }, { level: month, count: 12 }, { level: day, unit: day }, { level: hour, unit: hour }, { level: minute, unit: minute }, { level: second, unit: second }, { level: millisecond, unit: millisecond } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial }
    meaning: "the Solar Hijri calendar, civil in Iran and Afghanistan: the year begins at the March equinox; six months of 31 days, five of 30, and Esfand of 29 or 30. The OFFICIAL calendar is astronomical; it is reckoned here by the published table of 33-year-cycle breaks, which reproduces it over the range the tool states and refuses outside it."
    pattern: '^persian:-?\d+-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2}(\.\d{1,3})?)?([+-]\d{2}:\d{2}|Z)?)?$'
    form_note: "`persian:1405-06-29`, optionally followed by a clock reading and its offset exactly as gregorian-civil writes one"
    example: "persian:1405-06-29"
    establishes: false
    why: "a calendar reading corroborates when something happened and never fixes which being did it — as for gregorian-civil"
  - system: hebrew-calendar
    dimension: time
    calendar: hebrew
    reckoning: arithmetic
    day_begins: sunset
    same_ground_as: [gregorian-civil]
    crosswalk: computed
    levels: [ { level: year }, { level: month, count: [12, 13] }, { level: day, unit: day }, { level: hour, unit: hour }, { level: minute, unit: minute }, { level: second, unit: second }, { level: millisecond, unit: millisecond } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial }
    meaning: "the Hebrew calendar: lunisolar, and reckoned WHOLLY BY RULE since the 4th century. A leap year has THIRTEEN months: months are numbered from Tishri as CLDR numbers them, month 6 (Adar I) exists only in a leap year, and two months vary in length to keep the new year off forbidden weekdays."
    pattern: '^hebrew:-?\d+-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2}(\.\d{1,3})?)?([+-]\d{2}:\d{2}|Z)?)?$'
    form_note: "`hebrew:5787-01-09`, optionally followed by a clock reading and its offset exactly as gregorian-civil writes one"
    example: "hebrew:5787-01-09"
    establishes: false
    why: "a calendar reading corroborates when something happened and never fixes which being did it — as for gregorian-civil"
  - system: islamic-civil-calendar
    dimension: time
    calendar: islamic-civil
    reckoning: arithmetic
    day_begins: sunset
    same_ground_as: [gregorian-civil]
    crosswalk: computed
    levels: [ { level: year }, { level: month, count: 12 }, { level: day, unit: day }, { level: hour, unit: hour }, { level: minute, unit: minute }, { level: second, unit: second }, { level: millisecond, unit: millisecond } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial }
    meaning: "the tabular Hijri calendar, civil epoch (Friday 16 July 622 Julian): alternating months of 30 and 29 days and eleven leap days in a thirty-year cycle. An ARITHMETIC approximation of a calendar that is properly observed — good for reckoning, never for saying when a month actually began."
    pattern: '^islamic-civil:-?\d+-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2}(\.\d{1,3})?)?([+-]\d{2}:\d{2}|Z)?)?$'
    form_note: "`islamic-civil:1448-04-07`, optionally followed by a clock reading and its offset exactly as gregorian-civil writes one"
    example: "islamic-civil:1448-04-07"
    establishes: false
    why: "a calendar reading corroborates when something happened and never fixes which being did it — as for gregorian-civil"
  - system: islamic-tbla-calendar
    dimension: time
    calendar: islamic-tbla
    reckoning: arithmetic
    day_begins: sunset
    same_ground_as: [gregorian-civil]
    crosswalk: computed
    levels: [ { level: year }, { level: month, count: 12 }, { level: day, unit: day }, { level: hour, unit: hour }, { level: minute, unit: minute }, { level: second, unit: second }, { level: millisecond, unit: millisecond } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial }
    meaning: "the tabular Hijri calendar, astronomical epoch (Thursday 15 July 622 Julian): the same rule as islamic-civil, one day earlier."
    pattern: '^islamic-tbla:-?\d+-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2}(\.\d{1,3})?)?([+-]\d{2}:\d{2}|Z)?)?$'
    form_note: "`islamic-tbla:1448-04-08`, optionally followed by a clock reading and its offset exactly as gregorian-civil writes one"
    example: "islamic-tbla:1448-04-08"
    establishes: false
    why: "a calendar reading corroborates when something happened and never fixes which being did it — as for gregorian-civil"
  - system: islamic-calendar
    dimension: time
    calendar: islamic
    reckoning: observational
    day_begins: sunset
    same_ground_as: [gregorian-civil]
    crosswalk: observed
    levels: [ { level: year }, { level: month, count: 12 }, { level: day, unit: day }, { level: hour, unit: hour }, { level: minute, unit: minute }, { level: second, unit: second }, { level: millisecond, unit: millisecond } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial }
    meaning: "the Hijri calendar as OBSERVED: a month begins when the new crescent is sighted, so its length is known only once it has been seen, and two places may begin it on different days."
    pattern: '^islamic:-?\d+-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2}(\.\d{1,3})?)?([+-]\d{2}:\d{2}|Z)?)?$'
    form_note: "`islamic:1448-04-08`, optionally followed by a clock reading and its offset exactly as gregorian-civil writes one"
    example: "islamic:1448-04-08"
    establishes: false
    why: "a calendar reading corroborates when something happened and never fixes which being did it — as for gregorian-civil"
  - system: islamic-rgsa-calendar
    dimension: time
    calendar: islamic-rgsa
    reckoning: observational
    day_begins: sunset
    same_ground_as: [gregorian-civil]
    crosswalk: observed
    levels: [ { level: year }, { level: month, count: 12 }, { level: day, unit: day }, { level: hour, unit: hour }, { level: minute, unit: minute }, { level: second, unit: second }, { level: millisecond, unit: millisecond } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial }
    meaning: "the Hijri calendar by the sighting announced in Saudi Arabia."
    pattern: '^islamic-rgsa:-?\d+-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2}(\.\d{1,3})?)?([+-]\d{2}:\d{2}|Z)?)?$'
    form_note: "`islamic-rgsa:1448-04-08`, optionally followed by a clock reading and its offset exactly as gregorian-civil writes one"
    example: "islamic-rgsa:1448-04-08"
    establishes: false
    why: "a calendar reading corroborates when something happened and never fixes which being did it — as for gregorian-civil"
  - system: islamic-umalqura-calendar
    dimension: time
    calendar: islamic-umalqura
    reckoning: tabulated
    day_begins: sunset
    same_ground_as: [gregorian-civil]
    crosswalk: table
    levels: [ { level: year }, { level: month, count: 12 }, { level: day, unit: day }, { level: hour, unit: hour }, { level: minute, unit: minute }, { level: second, unit: second }, { level: millisecond, unit: millisecond } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial }
    meaning: "the Umm al-Qura calendar: the civil Hijri calendar of Saudi Arabia, published as a table computed for Mecca."
    pattern: '^islamic-umalqura:-?\d+-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2}(\.\d{1,3})?)?([+-]\d{2}:\d{2}|Z)?)?$'
    form_note: "`islamic-umalqura:1448-04-08`, optionally followed by a clock reading and its offset exactly as gregorian-civil writes one"
    example: "islamic-umalqura:1448-04-08"
    establishes: false
    why: "a calendar reading corroborates when something happened and never fixes which being did it — as for gregorian-civil"
  - system: coptic-calendar
    dimension: time
    calendar: coptic
    reckoning: arithmetic
    day_begins: midnight
    same_ground_as: [gregorian-civil]
    crosswalk: computed
    levels: [ { level: year }, { level: month, count: 13 }, { level: day, unit: day }, { level: hour, unit: hour }, { level: minute, unit: minute }, { level: second, unit: second }, { level: millisecond, unit: millisecond } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial }
    meaning: "the Coptic calendar: twelve months of thirty days and a thirteenth of five or six; the era of the Martyrs, from 284."
    pattern: '^coptic:-?\d+-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2}(\.\d{1,3})?)?([+-]\d{2}:\d{2}|Z)?)?$'
    form_note: "`coptic:1743-01-10`, optionally followed by a clock reading and its offset exactly as gregorian-civil writes one"
    example: "coptic:1743-01-10"
    establishes: false
    why: "a calendar reading corroborates when something happened and never fixes which being did it — as for gregorian-civil"
  - system: ethiopic-calendar
    dimension: time
    calendar: ethiopic
    reckoning: arithmetic
    day_begins: midnight
    same_ground_as: [gregorian-civil]
    crosswalk: computed
    levels: [ { level: year }, { level: month, count: 13 }, { level: day, unit: day }, { level: hour, unit: hour }, { level: minute, unit: minute }, { level: second, unit: second }, { level: millisecond, unit: millisecond } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial }
    meaning: "the Ethiopic calendar, Amete Mihret: the Coptic structure with an epoch in the year 8."
    pattern: '^ethiopic:-?\d+-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2}(\.\d{1,3})?)?([+-]\d{2}:\d{2}|Z)?)?$'
    form_note: "`ethiopic:2019-01-10`, optionally followed by a clock reading and its offset exactly as gregorian-civil writes one"
    example: "ethiopic:2019-01-10"
    establishes: false
    why: "a calendar reading corroborates when something happened and never fixes which being did it — as for gregorian-civil"
  - system: ethiopic-amete-alem-calendar
    dimension: time
    calendar: ethioaa
    reckoning: arithmetic
    day_begins: midnight
    same_ground_as: [gregorian-civil]
    crosswalk: computed
    levels: [ { level: year }, { level: month, count: 13 }, { level: day, unit: day }, { level: hour, unit: hour }, { level: minute, unit: minute }, { level: second, unit: second }, { level: millisecond, unit: millisecond } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial }
    meaning: "the Ethiopic calendar counted from Amete Alem, 5500 years earlier."
    pattern: '^ethioaa:-?\d+-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2}(\.\d{1,3})?)?([+-]\d{2}:\d{2}|Z)?)?$'
    form_note: "`ethioaa:7519-01-10`, optionally followed by a clock reading and its offset exactly as gregorian-civil writes one"
    example: "ethioaa:7519-01-10"
    establishes: false
    why: "a calendar reading corroborates when something happened and never fixes which being did it — as for gregorian-civil"
  - system: indian-calendar
    dimension: time
    calendar: indian
    reckoning: arithmetic
    day_begins: midnight
    same_ground_as: [gregorian-civil]
    crosswalk: computed
    levels: [ { level: year }, { level: month, count: 12 }, { level: day, unit: day }, { level: hour, unit: hour }, { level: minute, unit: minute }, { level: second, unit: second }, { level: millisecond, unit: millisecond } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial }
    meaning: "the Indian national calendar (Saka era): tied to the Gregorian leap rule, beginning on 22 March, or 21 March in a leap year."
    pattern: '^indian:-?\d+-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2}(\.\d{1,3})?)?([+-]\d{2}:\d{2}|Z)?)?$'
    form_note: "`indian:1948-06-29`, optionally followed by a clock reading and its offset exactly as gregorian-civil writes one"
    example: "indian:1948-06-29"
    establishes: false
    why: "a calendar reading corroborates when something happened and never fixes which being did it — as for gregorian-civil"
  - system: buddhist-calendar
    dimension: time
    calendar: buddhist
    reckoning: arithmetic
    day_begins: midnight
    same_ground_as: [gregorian-civil]
    crosswalk: computed
    levels: [ { level: year }, { level: month, count: 12 }, { level: day, unit: day }, { level: hour, unit: hour }, { level: minute, unit: minute }, { level: second, unit: second }, { level: millisecond, unit: millisecond } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial }
    meaning: "the Thai Buddhist calendar: Gregorian months and days, the year counted from 543 BCE."
    pattern: '^buddhist:-?\d+-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2}(\.\d{1,3})?)?([+-]\d{2}:\d{2}|Z)?)?$'
    form_note: "`buddhist:2569-09-20`, optionally followed by a clock reading and its offset exactly as gregorian-civil writes one"
    example: "buddhist:2569-09-20"
    establishes: false
    why: "a calendar reading corroborates when something happened and never fixes which being did it — as for gregorian-civil"
  - system: roc-calendar
    dimension: time
    calendar: roc
    reckoning: arithmetic
    day_begins: midnight
    same_ground_as: [gregorian-civil]
    crosswalk: computed
    levels: [ { level: year }, { level: month, count: 12 }, { level: day, unit: day }, { level: hour, unit: hour }, { level: minute, unit: minute }, { level: second, unit: second }, { level: millisecond, unit: millisecond } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial }
    meaning: "the Republic of China calendar: Gregorian months and days, the year counted from 1912."
    pattern: '^roc:-?\d+-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2}(\.\d{1,3})?)?([+-]\d{2}:\d{2}|Z)?)?$'
    form_note: "`roc:115-09-20`, optionally followed by a clock reading and its offset exactly as gregorian-civil writes one"
    example: "roc:115-09-20"
    establishes: false
    why: "a calendar reading corroborates when something happened and never fixes which being did it — as for gregorian-civil"
  - system: japanese-calendar
    dimension: time
    calendar: japanese
    reckoning: arithmetic
    day_begins: midnight
    same_ground_as: [gregorian-civil]
    crosswalk: computed
    levels: [ { level: era }, { level: year }, { level: month }, { level: day, unit: day }, { level: hour, unit: hour }, { level: minute, unit: minute }, { level: second, unit: second }, { level: millisecond, unit: millisecond } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial }
    meaning: "the Japanese imperial calendar: Gregorian months and days, the year counted within an ERA. The era is a LEVEL above the year — and the one level in this registry whose cells are named rather than numbered. Reckoned from 1873, when Japan adopted the Gregorian calendar."
    pattern: '^japanese:[a-z]+-\d+-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2}(\.\d{1,3})?)?([+-]\d{2}:\d{2}|Z)?)?$'
    form_note: "`japanese:reiwa-8-09-20`, optionally followed by a clock reading and its offset exactly as gregorian-civil writes one"
    example: "japanese:reiwa-8-09-20"
    establishes: false
    why: "a calendar reading corroborates when something happened and never fixes which being did it — as for gregorian-civil"
  - system: chinese-calendar
    dimension: time
    calendar: chinese
    reckoning: astronomical
    day_begins: midnight
    same_ground_as: [gregorian-civil]
    crosswalk: observed
    levels: [ { level: year }, { level: month, count: [12, 13] }, { level: day, unit: day }, { level: hour, unit: hour }, { level: minute, unit: minute }, { level: second, unit: second }, { level: millisecond, unit: millisecond } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial }
    meaning: "the traditional Chinese calendar: lunisolar, months beginning at the new moon computed for the 120th meridian east, with an intercalary month — written `L` — in some years."
    pattern: '^chinese:-?\d+-\d{2}L?-\d{2}([T ]\d{2}:\d{2}(:\d{2}(\.\d{1,3})?)?([+-]\d{2}:\d{2}|Z)?)?$'
    form_note: "`chinese:4723-08-09`, optionally followed by a clock reading and its offset exactly as gregorian-civil writes one"
    example: "chinese:4723-08-09"
    establishes: false
    why: "a calendar reading corroborates when something happened and never fixes which being did it — as for gregorian-civil"
  - system: dangi-calendar
    dimension: time
    calendar: dangi
    reckoning: astronomical
    day_begins: midnight
    same_ground_as: [gregorian-civil]
    crosswalk: observed
    levels: [ { level: year }, { level: month, count: [12, 13] }, { level: day, unit: day }, { level: hour, unit: hour }, { level: minute, unit: minute }, { level: second, unit: second }, { level: millisecond, unit: millisecond } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial }
    meaning: "the traditional Korean calendar: the Chinese structure computed for Korea's meridian."
    pattern: '^dangi:-?\d+-\d{2}L?-\d{2}([T ]\d{2}:\d{2}(:\d{2}(\.\d{1,3})?)?([+-]\d{2}:\d{2}|Z)?)?$'
    form_note: "`dangi:4359-08-09`, optionally followed by a clock reading and its offset exactly as gregorian-civil writes one"
    example: "dangi:4359-08-09"
    establishes: false
    why: "a calendar reading corroborates when something happened and never fixes which being did it — as for gregorian-civil"
  - system: julian-day
    dimension: time
    calendar: julian-day
    reckoning: arithmetic
    day_begins: noon
    same_ground_as: [gregorian-civil]
    crosswalk: computed
    levels: [ { level: day, unit: day } ]
    neighbours: metered
    restrictions: { lines: 1, order: total }
    meaning: "the Julian Day Number: a plain count of days, as astronomers keep it. EVERY CALENDAR MEETS THE OTHERS AT THE DAY, and this is that meeting point given a name: a system with one level and no months at all. Its day begins at NOON, so that a night of observation falls on one number."
    pattern: '^jdn:\d+$'
    form_note: "`jdn:<integer>` — the number of the day whose noon it is"
    example: "jdn:2461304"
    establishes: false
    why: "a day corroborates when something happened and never fixes which being did it"
  - system: mayan-long-count
    dimension: time
    calendar: mayan-long-count
    reckoning: arithmetic
    day_begins: midnight
    same_ground_as: [gregorian-civil]
    crosswalk: computed
    levels: [ { level: baktun }, { level: katun }, { level: tun }, { level: uinal }, { level: kin, unit: day } ]
    neighbours: metered
    restrictions: { lines: 1, order: total }
    meaning: "the Mayan long count: a count of days written in mixed base — 20 kin to a uinal, 18 uinal to a tun, 20 tun to a katun, 20 katun to a baktun. A calendar with NO MONTHS OF UNEQUAL LENGTH: every level is a fixed number of days. Reckoned from the Goodman-Martinez-Thompson correlation."
    pattern: '^mayan:\d+\.\d+\.\d+\.\d+\.\d+$'
    form_note: "`mayan:<baktun>.<katun>.<tun>.<uinal>.<kin>`"
    example: "mayan:13.0.13.17.1"
    establishes: false
    why: "as for julian-day"
  - system: bahai-calendar
    dimension: time
    calendar: bahai
    reckoning: astronomical
    day_begins: sunset
    same_ground_as: [gregorian-civil]
    crosswalk: observed
    levels: [ { level: year }, { level: month, count: 19 }, { level: day, unit: day } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial }
    meaning: "the Badi calendar: nineteen months of nineteen days and a few days between, the year beginning at the March equinox as computed for Tehran."
    pattern: '^bahai:\d+-\d{2}-\d{2}$'
    form_note: "`bahai:<year>-<month>-<day>`; the intercalary days are written as month 00"
    example: "bahai:183-10-13"
    establishes: false
    why: "as for gregorian-civil"
  - system: french-republican-calendar
    dimension: time
    calendar: french-republican
    reckoning: astronomical
    day_begins: midnight
    same_ground_as: [gregorian-civil]
    crosswalk: observed
    levels: [ { level: year }, { level: month, count: 12 }, { level: decade }, { level: day, unit: day } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial }
    meaning: "the calendar of the French Republic: twelve months of thirty days in three ten-day decades, and five or six days over, the year beginning at the autumn equinox as observed from Paris. Declared because dated sources exist in it, and because its ten-day decade is a partition no other calendar here has."
    pattern: '^french-republican:\d+-\d{2}-\d{2}$'
    form_note: "`french-republican:<year>-<month>-<day>`; the days over are written as month 13"
    example: "french-republican:234-13-04"
    establishes: false
    why: "as for gregorian-civil"
  - system: unix-epoch
    dimension: time
    levels: [ { level: millisecond, unit: millisecond } ]
    neighbours: metered
    restrictions: { lines: 1, order: total }
    meaning: "a time position as milliseconds since 1970-01-01T00:00:00Z. Declared at 7.0 for `beanger` records, whose ORDER is the thing being recorded — two operations in one session land in the same second, and a position that cannot separate them cannot order them."
    pattern: '^\d{13}$'
    form_note: "exactly 13 digits: epoch MILLISECONDS, never seconds. One length, one meaning — a 10-digit value would be a different unit wearing the same shape, which is the ambiguity `unit` was added to stop."
    establishes: false
    why: "a moment corroborates when something was done and never fixes which being did it. It differs from `gregorian-civil` in one useful way: it carries no offset, so it cannot be misread the way a +03 label on a UTC reading was misread in this estate's own journal."
  - system: geographic
    dimension: place
    neighbours: metered
    restrictions: { lines: 3, metered: length }
    meaning: "a position BY COORDINATES, in a named coordinate reference system, on the body that system is fixed to. THE ROOT OF PLACE: every other place system resolves through this one. Named here also because CIVIL TIME RESOLVES THROUGH IT — an offset is a geographic fact wearing a time costume."
    pattern: '^[A-Z][A-Z0-9_]*:[0-9]+;-?\d+(\.\d+)?(,-?\d+(\.\d+)?){1,2}(@\d{4}(\.\d+)?)?$'
    form_note: "`<authority>:<code>;<coordinates>[@<epoch>]` — `EPSG:4326;35.6892,51.3890@2026.72`. A COORDINATE IS NEVER BARE: a plain `<lat>,<lon>` names no datum, no axis order and no body, so two readers can disagree by hundreds of metres and neither be wrong. Coordinates in the axis order the system declares; the epoch when the frame is dynamic."
    example: "EPSG:4326;35.6892,51.3890@2026.72"
    establishes: false
    why: "a coordinate says where something IS and never which thing it is: two beings can stand in one spot, and one being can move"
  - system: event-anchored
    dimension: any
    neighbours: counted
    meaning: "a position fixed by NEIGHBOURING EVENTS rather than by any coordinate — 'after the branch was pushed, before the cutover'. Fully positioned while carrying no calendar value at all. Declared because it is what makes this a registry rather than a two-item enum: SEQUENCE is the general structure and a coordinate system is one restriction of it."
    pattern: '^(after|before):.+$'
    form_note: "after:<position> or before:<position>; state both as two entries when an interval is meant"
    establishes: false
    why: "an event anchor positions relative to other positions — it fixes an interval, never a point"
  - system: network-segment
    dimension: place
    resolves_through: geographic
    levels: [ { level: network }, { level: segment } ]
    neighbours: counted
    meaning: "WHERE A BEING IS ATTACHED in a network's topology: a VLAN, a wireless network, an address range with a role. Declared 11.0, operator-ratified: a segment is a PLACE (where you are), which is a different question from an address (where you answer) — those have their own registry, and a being keeps its address while moving between segments."
    pattern: '^[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9.:-]*$'
    form_note: "<network>/<segment>, e.g. an office network's guest VLAN or its wireless network for laptops. The network is named because two sites both have a `vlan-13` and they are not the same place."
    establishes: false
    why: "a being moves between segments — a laptop joins the guest network and then the staff one — so a segment corroborates where it is and never fixes which being it is"
  - system: windows-filesystem
    dimension: place
    levels: open
    neighbours: none
    meaning: "a position in ONE NAMED HOST's Windows filesystem. A SEPARATE SYSTEM from unix-filesystem, not a dialect of it: C:\\Users\\user\\source\\repos\\addin and /home/user/addin share no canonical form, and one system carrying two patterns is exactly the reinvention this registry forbids."
    pattern: '^(root:[a-z0-9][a-z0-9-]*(/[^:]*)?|[a-z0-9][a-z0-9.-]*:[A-Za-z]:\\.*)$'
    form_note: "root:<logical root>[/<relative path>], or <host>:<Drive>:\\<path> stated outright. The two colons are unambiguous — hostname, then drive letter — and the root: form is IDENTICAL to the unix one on purpose: a LOGICAL root is what crosses systems, a literal path is what does not. That is the whole mechanism for resolving one repository on machines that do not agree what a path looks like."
    establishes: false
    why: "a path is reassignable and a tree can be checked out anywhere — it corroborates a location, never fixes it. Identical to the unix case, because the reason has nothing to do with the operating system."
  # == ADDRESSES AND PORTS ARE PLACES ==
  - system: ipv4
    dimension: place
    levels: { by: prefix-length, from: 0, to: 32 }
    neighbours: counted
    restrictions: { lines: 1, ends: bounded }
    meaning: "a 32-bit Internet Protocol address, optionally carrying a prefix length."
    checked_by: ipaddress-v4
    form_note: "dotted quad, optionally /prefix. The bare address and the prefixed form are the SAME system: a prefix narrows a position, it does not change what kind of position it is."
    establishes: false
    why: "reassignable by DHCP, NAT, failover and plain reuse — it corroborates which being answers and never fixes which being it IS. The same rule the `ip` anchor has always carried, now stated where the position is."
  - system: ipv6
    dimension: place
    levels: { by: prefix-length, from: 0, to: 128 }
    neighbours: counted
    restrictions: { lines: 1, ends: bounded }
    meaning: "a 128-bit Internet Protocol address, optionally carrying a prefix length."
    checked_by: ipaddress-v6
    form_note: "lowercase hex in RFC 5952 compressed form, optionally /prefix. NOT a dialect of ipv4 — it shares no format with it, and one pattern covering both could not tell a malformed quad from a valid v6 address."
    establishes: false
    why: "everything ipv4's reason says, and one more: v6 addresses are also AUTOCONFIGURED, so a being may answer at an address nobody assigned and nobody recorded."
  - system: tcp-port
    dimension: place
    transport: tcp
    within: [ipv4, ipv6]
    neighbours: counted
    restrictions: { lines: 1, order: total, ends: bounded }
    meaning: "a TCP port: a position WITHIN an address, naming which listener there. Meaningless without the address beside it, as a path is without its host."
    pattern: '^([0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])$'
    form_note: "one decimal integer, 0 to 65535. ONE port: `110/143/993/995` is four positions, and four entries."
    establishes: false
    why: "a port is reassigned by editing one line of configuration — it corroborates which listener answers and never fixes which being it is"
  - system: udp-port
    dimension: place
    transport: udp
    within: [ipv4, ipv6]
    neighbours: counted
    restrictions: { lines: 1, order: total, ends: bounded }
    meaning: "a UDP port. A SEPARATE SYSTEM from tcp-port and not a dialect of it: 53/udp and 53/tcp are two positions, and a resolver that answers on both has two endpoints."
    pattern: '^([0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])$'
    form_note: "one decimal integer, 0 to 65535"
    establishes: false
    why: "as for tcp-port"
  - system: iso-3166
    dimension: place
    resolves_through: geographic
    levels: [ { level: country }, { level: subdivision } ]
    neighbours: counted
    meaning: "a country (ISO 3166-1 alpha-2) or one of its principal subdivisions (ISO 3166-2)."
    pattern: '^[A-Z]{2}(-[A-Z0-9]{1,3})?$'
    form_note: "`IR`, or `IR-23` — the code as published, upper case"
    establishes: true
    why: "a published code names the same territory in every garden; it survives a renaming, which a name does not"
  - system: osm
    dimension: place
    resolves_through: geographic
    neighbours: none
    meaning: "an OpenStreetMap element. An IDENTIFIER in somebody else's database: convenient, stable across a renaming, and NOT what a place is anchored to."
    pattern: '^(node|way|relation)/[1-9][0-9]*$'
    form_note: "`relation/1234567` — the element type and its id"
    example: "relation/1234567"
    establishes: false
    why: "An element id names a row in a third party's database: elements are split, merged, deleted and re-created, a tag may simply be wrong (a school tagged `place=village`), and the whole map is a CAPTURE of somebody else's truth under ground rule 3. It corroborates which mapped object was meant. What a place is rooted in is a coordinate on a body."
  # == MORE WAYS OF SAYING WHERE BY IDENTIFIER ==
  - system: street-address
    dimension: place
    within: [iso-3166]
    resolves_through: geographic
    neighbours: none
    meaning: "a postal street address, as its country writes one."
    pattern: none
    pattern_why: "no two countries write an address the same way, and inventing a canonical form would reject valid addresses to look thorough. The address is prose; the country it is within is not."
    establishes: false
    why: "an address names a DELIVERY POINT that is renumbered, renamed and shared — and one building has many"
  - system: local-frame
    dimension: place
    resolves_through: geographic
    neighbours: counted
    meaning: "a position in a frame that TRAVELS WITH ITS HOST: the third floor, room 12, rack 3 slot 7, a deck of a ship. ISO 19111 calls it an engineering system. It is where a thing is WITHIN something, and it keeps its meaning when the something moves — which is exactly what a coordinate does not."
    pattern: '^[a-z0-9][a-z0-9-]*#[^#]+$'
    form_note: "`<host or site>#<position within it>` — `head-office#floor-3/room-12`, `rack-a#u17`"
    example: "head-office#floor-3/room-12"
    establishes: false
    why: "rooms are renumbered and racks re-filled; and the frame itself may be moved"
  - system: geohash
    dimension: place
    resolves_through: geographic
    levels: { by: prefix-length, from: 1, to: 12 }
    neighbours: counted
    meaning: "a cell of the geohash grid over WGS 84. A GRID IS LEVELS LAID OVER COORDINATES: a prefix of a code is a coarser cell that contains it, so a position can be held — and PUBLISHED — at the precision somebody chose."
    pattern: '^[0-9bcdefghjkmnpqrstuvwxyz]{1,12}$'
    form_note: "base-32, 1 to 12 characters — `tnke13`"
    example: "tnke13"
    establishes: false
    why: "a cell says roughly where and never what"
  - system: plus-code
    dimension: place
    resolves_through: geographic
    levels: { by: prefix-length, from: 2, to: 15 }
    neighbours: counted
    meaning: "an Open Location Code: a grid cell written so that a person can read it aloud, for places with no street address."
    pattern: '^[23456789CFGHJMPQRVWX]{2,8}0*\+[23456789CFGHJMPQRVWX]{0,7}$'
    form_note: "the full code as published — `8H7JM9Q5+M2`"
    example: "8H7JM9Q5+M2"
    establishes: false
    why: "as for geohash"
  - system: postal-code
    dimension: place
    resolves_through: geographic
    within: [iso-3166]
    levels: { by: prefix-length, from: 1, to: 12 }
    neighbours: none
    meaning: "a postal code, within the country that issues it. A PREFIX is a coarser level of the same position: a whole code may name one building, which is a reason to hold a person's place at a shorter one."
    pattern: '^[A-Z]{2}:[A-Z0-9][A-Z0-9 -]{0,11}$'
    form_note: "`<ISO country>:<code or prefix>`, e.g. `IR:14155`"
    establishes: false
    why: "codes are re-drawn by the operator that issues them, and one code covers many places"
# == ROLES: what a being DOES, as against what it IS ==
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

# == OPERATING SYSTEMS: what a machine runs, and what that IMPLIES about its positions ==
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
  - { os: linux,   family: unix, path_grammar: unix-filesystem, meaning: "A Linux system whose distribution is not listed here, or not worth distinguishing." }
  - { os: debian,  family: unix, path_grammar: unix-filesystem, meaning: "Debian GNU/Linux." }
  - { os: ubuntu,  family: unix, path_grammar: unix-filesystem, meaning: "Ubuntu." }
  - { os: rhel,    family: unix, path_grammar: unix-filesystem, meaning: "Red Hat Enterprise Linux." }
  - { os: fedora,  family: unix, path_grammar: unix-filesystem, meaning: "Fedora Linux." }
  - { os: arch,    family: unix, path_grammar: unix-filesystem, meaning: "Arch Linux." }
  - { os: alpine,  family: unix, path_grammar: unix-filesystem, meaning: "Alpine Linux." }
  - { os: freebsd, family: unix, path_grammar: unix-filesystem, meaning: "FreeBSD." }
  - { os: macos,   family: unix, path_grammar: unix-filesystem, meaning: "Apple macOS." }

# == STORAGE FORMATS: the OTHER filesystem axis, the one ntfs and ext4 actually belong to ==
storage_formats:
  - { format: ext4,              layer: filesystem,     posix: true,  meaning: "the estate's ordinary Linux filesystem" }
  - { format: ext2,              layer: filesystem,     posix: true,  meaning: "a common /boot filesystem" }
  - { format: vfat,              layer: filesystem,     posix: false, meaning: "the usual EFI system partition. NOT posix: it carries no ownership or permission bits, which is why an EFI partition cannot hold anything whose mode matters." }
  - { format: swap,              layer: swap,                         meaning: "paging space; a formatted volume that holds no filesystem" }
  - { format: crypto_LUKS,       layer: encryption,                   meaning: "a LUKS container. CARRIES another volume rather than holding files itself — the clearest case for `carried_by`." }
  - { format: LVM2_member,       layer: volume-manager,               meaning: "an LVM physical volume; the logical volumes inside it are separate entries that name it in `carried_by`" }
  - { format: linux_raid_member, layer: raid,                         meaning: "an md RAID member. e.g. raid1 for /boot, raid6 for share arrays." }
  - { format: ntfs,              layer: filesystem,     posix: false, meaning: "the Windows filesystem. Declared and unoccupied — see the vacancy. It is named here because the question 'where does ntfs go' is what produced this registry, and the answer is that it is a STORAGE FORMAT and never a path grammar." }

# == PLANES: what a surface, a link or a treatment is FOR ==
planes:
  - { plane: data,       meaning: "the traffic the being exists to carry or to serve" }
  - { plane: control,    meaning: "how the being decides where traffic goes: routing adjacencies, discovery, redundancy election" }
  - { plane: management, meaning: "how an operator reaches the being to configure or observe it" }

# == REGISTRY LINKS: a row of one registry names a row of another, and the gate resolves it ==
registry_links:
  - { from: units, field: quantity, to: quantities, take: quantity, why: "a unit measures a quantity, and the quantity says what it is made of" }
  - { from: facets, field: depends_on, to: facets, take: facet, acyclic: true, rooted: true, why: "a facet depends only on facets the law declares, never on itself through others, and every facet but one reaches that one: the walk they form is the lattice ownership is faceted by, and `legal` is its root" }
  - { from: reference_systems, field: body,  to: bodies,                 take: body,  why: "a reference system is fixed to a body, and a latitude is a latitude ON something" }
  - { from: reference_systems, field: kind,  to: reference_system_kinds, take: kind,  why: "the classes ISO 19111 names" }
  - { from: reference_systems, field: frame, to: reference_frames,       take: frame, why: "static or dynamic: whether a coordinate needs an epoch" }
  - { from: net_protocols, field: technology, to: technology, take: code,
      why: "every protocol names its entry in the catalogue of technologies, which carries its specification and the field of knowledge it belongs to — so a routing mechanism ledgered tomorrow hangs from the same tree as a mail server does today" }

# == NET PROTOCOLS: the one owner of what a being may SPEAK ==
net_protocols:
  - protocol: tcp
    technology: tcp
    layer: transport
    positions: tcp-port
    meaning: "the Transmission Control Protocol. Its positions are ports (`anchor_systems.tcp-port`)."
  - protocol: udp
    technology: udp
    layer: transport
    positions: udp-port
    meaning: "the User Datagram Protocol. Its positions are ports (`anchor_systems.udp-port`)."
  - protocol: ssh
    technology: ssh
    layer: application
    transport: tcp
    default_ports: [22]
    meaning: "the Secure Shell transport: an authenticated, encrypted channel that other protocols ride."
  - protocol: sftp
    technology: sftp
    layer: application
    transport: tcp
    rides_on: [ssh]
    meaning: "file transfer carried INSIDE an ssh channel. It has no port of its own, and `rides_on` is what records that rather than a fabricated default."
  - protocol: git
    technology: git-protocol
    layer: application
    transport: tcp
    rides_on: [ssh, http]
    meaning: "the git wire protocol. It is usually carried — `host-a:git/ledger.git` and `vps-a:addin` are both git over ssh — so its protection is whatever carries it, and the row says so instead of claiming one."
  - protocol: http
    technology: http
    layer: application
    transport: tcp
    default_ports: [80, 443]
    meaning: "the Hypertext Transfer Protocol. 443 is this same protocol with an endpoint taking the `encrypted` position, NOT a separate protocol called https."
  - protocol: smtp
    technology: smtp
    layer: application
    transport: tcp
    default_ports: [25, 465, 587]
    meaning: "mail transfer. One protocol on three ports: 25 relay, 465 implicit TLS, 587 submission — the port is a fact about the endpoint and the protection is an aspect position, so none of the three needs its own row."
  - protocol: pop3
    technology: pop3
    layer: application
    transport: tcp
    default_ports: [110, 995]
    meaning: "mailbox retrieval, download-oriented. 995 is the same protocol wrapped in TLS."
  - protocol: imap
    technology: imap
    layer: application
    transport: tcp
    default_ports: [143, 993]
    meaning: "mailbox access, server-side-state-oriented. 993 is the same protocol wrapped in TLS."
  - protocol: smb
    technology: smb
    layer: application
    transport: tcp
    default_ports: [445]
    meaning: "the Server Message Block file-sharing protocol. The PROTOCOL — Samba is one implementation of it and is a bean, not a row."
  - protocol: mysql
    technology: mysql-protocol
    layer: application
    transport: tcp
    default_ports: [3306]
    meaning: "the MySQL/MariaDB client-server wire protocol. Again the protocol, not the server."
  - protocol: dns
    technology: dns
    layer: application
    transport: udp
    default_ports: [53]
    meaning: "the Domain Name System query protocol. Added beyond the eighteen names the design was asked for, because this estate runs three BIND beans and omitting it would have forced them to record their listening surface as something they do not speak."
  - protocol: wireguard
    technology: wireguard
    layer: link
    transport: udp
    default_ports: [51820]
    synthesizes_link: true
    meaning: "a tunnel protocol that MANUFACTURES A LINK: a wireguard peering produces an interface other protocols are then carried over. `synthesizes_link` is what distinguishes it from every application row above, and it is why `links` is a term and not a note."
  - protocol: pptp
    technology: pptp
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
  - { protocol: ipv4,  technology: ipv4,  layer: network,   positions: ipv4, meaning: "Internet Protocol version 4. Its positions are addresses (`anchor_systems.ipv4`)." }
  - { protocol: ipv6,  technology: ipv6,  layer: network,   positions: ipv6, meaning: "Internet Protocol version 6." }
  - { protocol: icmp,  technology: icmp,  layer: network,   plane: control,    meaning: "Internet Control Message Protocol: how the network layer reports that it could not deliver." }
  - { protocol: arp,   technology: arp,   layer: link,      plane: control,    meaning: "Address Resolution Protocol: finds the link-layer address that holds a network address — the join between two positioning systems." }
  - { protocol: dot1q, technology: dot1q, layer: link,      synthesizes_link: true, rides_on: [ethernet], meaning: "IEEE 802.1Q VLAN tagging: one physical link carried as several segments. The plainest OVERLAY: a place system drawn over another." }
  - { protocol: stp,   technology: stp,   layer: link,      plane: control,    meaning: "Spanning Tree (IEEE 802.1D/w/s): elects one loop-free tree out of a meshed link layer — `acyclic`, enforced by a protocol." }
  - { protocol: lldp,  technology: lldp,  layer: link,      plane: control,    meaning: "Link Layer Discovery Protocol (IEEE 802.1AB): each device tells its NEIGHBOUR who it is. Neighbourhood, measured rather than drawn." }
  - { protocol: gre,   technology: gre,   layer: link,      synthesizes_link: true, meaning: "Generic Routing Encapsulation: an unencrypted tunnel that manufactures a link." }
  - { protocol: ipsec, technology: ipsec, layer: link,      synthesizes_link: true, meaning: "IPsec: authenticated, encrypted carriage of the network layer; in tunnel mode it manufactures a link." }
  - { protocol: vxlan, technology: vxlan, layer: link,      transport: udp, default_ports: [4789], synthesizes_link: true, meaning: "Virtual eXtensible LAN: a link layer carried over a routed network — an overlay with the underlay's reach." }
  - { protocol: ospf,  technology: ospf,  layer: network,   plane: control, family: link-state,      scope: interior, meaning: "Open Shortest Path First. Floods link states, computes shortest paths by cost, and divides a network into AREAS that summarise at their borders." }
  - { protocol: is-is, technology: is-is, layer: link,      plane: control, family: link-state,      scope: interior, meaning: "Intermediate System to Intermediate System. Link-state like OSPF, carried directly on the link layer, with two LEVELS." }
  - { protocol: rip,   technology: rip,   layer: application, transport: udp, default_ports: [520], plane: control, family: distance-vector, scope: interior, meaning: "Routing Information Protocol. Distance-vector by hop COUNT — a metric that counts neighbours and measures nothing." }
  - { protocol: eigrp, technology: eigrp, layer: network,   plane: control, family: distance-vector, scope: interior, meaning: "Enhanced Interior Gateway Routing Protocol. Advanced distance-vector with a composite metric; one vendor's, published as an informational RFC." }
  - { protocol: bgp,   technology: bgp,   layer: application, transport: tcp, default_ports: [179], plane: control, family: path-vector, scope: exterior, meaning: "Border Gateway Protocol. Carries the whole path of autonomous systems, so POLICY can refuse one; the protocol between administrations." }
  - { protocol: vrrp,  technology: vrrp,  layer: network,   plane: control,    meaning: "Virtual Router Redundancy Protocol: several routers answer as one address, one at a time. A shared address made honest." }
  - { protocol: dhcp,  technology: dhcp,  layer: application, transport: udp, default_ports: [67, 68], plane: control, meaning: "Dynamic Host Configuration Protocol: hands a being its position in the address space — the reason an address corroborates and never establishes." }
  - { protocol: ntp,   technology: ntp,   layer: application, transport: udp, default_ports: [123], plane: control, meaning: "Network Time Protocol: how beings agree a position in TIME. A ledger of timestamps rests on it." }
  - { protocol: snmp,  technology: snmp,  layer: application, transport: udp, default_ports: [161, 162], plane: management, meaning: "Simple Network Management Protocol: a being read, and sometimes written, by its operator." }
  - protocol: ethernet
    technology: ethernet
    layer: link
    meaning: "an ethernet link, including an aggregated one. Added while MIGRATING the corpus, not while designing it: `carried_by` had nothing to terminate on until a base link existed, and an aggregated bond is a real measured one. This row is the design's own claim tested on itself — adding a protocol is a registry row, not a rule-change to any term."
  - protocol: pppoe
    technology: pppoe
    layer: link
    rides_on: [ethernet]
    synthesizes_link: true
    meaning: "PPP over Ethernet: a WAN dial that runs directly on ethernet frames, with no IP transport or port of its own (9.0 removed a `transport: tcp` / port 1723 copied from pptp). Like wireguard it MANUFACTURES a link, which is what lets a tunnel name it in `carried_by`."

# == UNITS: the resolution a position is actually held to ==
dimensions:
  - { dimension: time,        meaning: "how long" }
  - { dimension: length,      meaning: "how far" }
  - { dimension: mass,        meaning: "how much matter" }
  - { dimension: information, meaning: "how much can be stored or carried" }
  - { dimension: money,       meaning: "how much value, in a currency" }
quantities:
  - { quantity: duration,     of: { time: 1 } }
  - { quantity: frequency,    of: { time: -1 } }
  - { quantity: length,       of: { length: 1 } }
  - { quantity: area,         of: { length: 2 } }
  - { quantity: volume,       of: { length: 3 } }
  - { quantity: speed,        of: { length: 1, time: -1 } }
  - { quantity: acceleration, of: { length: 1, time: -2 } }
  - { quantity: mass,         of: { mass: 1 } }
  - { quantity: information,  of: { information: 1 } }
  - { quantity: data-rate,    of: { information: 1, time: -1 } }
  - { quantity: level,        of: {}, scale: logarithmic }
  - { quantity: attenuation,  of: { length: -1 }, scale: logarithmic }
  - { quantity: ratio,        of: {}, meaning: "a part of a whole, or a rate: dimensionless and linear — a share, a rate of interest" }
  - quantity: money
    of: { money: 1 }
    units_from: { registry: currencies, take: code, digits: digits }
    crosswalk: observed
    meaning: "an amount in one currency. Each currency is a unit, and no factor joins two of them: two currencies meet only through a rate someone observed at a moment, from a source — a reading, recorded with its provenance, never a law. So every amount stays in the currency it was paid or owed in, and whatever is computed from amounts — a share, a sum, a balance, a conversion at an observed rate — is computed in fractions and read, never stored."
units:
  - { unit: one,         quantity: ratio, factor: [1, 1],     meaning: "the whole" }
  - { unit: percent,     quantity: ratio, factor: [1, 100],   meaning: "one part in a hundred" }
  - { unit: per-mille,   quantity: ratio, factor: [1, 1000],  meaning: "one part in a thousand" }
  - { unit: basis-point, quantity: ratio, factor: [1, 10000], meaning: "one part in ten thousand: how a rate of interest is often quoted" }
  - { unit: millisecond, quantity: duration, factor: [1, 1000], meaning: "a thousandth of a second: the finest resolution this ledger records" }
  - { unit: second, quantity: duration, factor: [1, 1], meaning: "the SI second" }
  - { unit: minute, quantity: duration, factor: [60, 1], meaning: "sixty seconds" }
  - { unit: hour, quantity: duration, factor: [3600, 1], meaning: "sixty minutes" }
  - { unit: day, quantity: duration, factor: [86400, 1], meaning: "twenty-four hours: the level every calendar meets the others at" }
  - { unit: millimetre, quantity: length, factor: [1, 1000], meaning: "a thousandth of a metre" }
  - { unit: metre, quantity: length, factor: [1, 1], meaning: "the SI metre" }
  - { unit: kilometre, quantity: length, factor: [1000, 1], meaning: "a thousand metres" }
  - { unit: square-metre, quantity: area, factor: [1, 1], meaning: "a metre by a metre" }
  - { unit: hectare, quantity: area, factor: [10000, 1], meaning: "a hundred metres by a hundred" }
  - { unit: square-kilometre, quantity: area, factor: [1000000, 1], meaning: "a kilometre by a kilometre" }
  - { unit: cubic-metre, quantity: volume, factor: [1, 1], meaning: "a metre cubed" }
  - { unit: litre, quantity: volume, factor: [1, 1000], meaning: "a thousandth of a cubic metre" }
  - { unit: metre-per-second, quantity: speed, factor: [1, 1], meaning: "the coherent unit of speed" }
  - { unit: kilometre-per-hour, quantity: speed, factor: [5, 18], meaning: "a kilometre in an hour: five eighteenths of a metre per second" }
  - { unit: metre-per-second-squared, quantity: acceleration, factor: [1, 1], meaning: "a metre per second, gained each second" }
  - { unit: hertz, quantity: frequency, factor: [1, 1], meaning: "once per second" }
  - { unit: kilogram, quantity: mass, factor: [1, 1], meaning: "the SI kilogram" }
  - { unit: gram, quantity: mass, factor: [1, 1000], meaning: "a thousandth of a kilogram" }
  - { unit: bit, quantity: information, factor: [1, 8], meaning: "an eighth of a byte" }
  - { unit: byte, quantity: information, factor: [1, 1], meaning: "eight bits: what a storage address line is metered in" }
  - { unit: kilobyte, quantity: information, factor: [1000, 1], meaning: "a thousand bytes" }
  - { unit: megabyte, quantity: information, factor: [1000000, 1], meaning: "a million bytes" }
  - { unit: gigabyte, quantity: information, factor: [1000000000, 1], meaning: "a thousand million bytes" }
  - { unit: terabyte, quantity: information, factor: [1000000000000, 1], meaning: "a million million bytes" }
  - { unit: gibibyte, quantity: information, factor: [1073741824, 1], meaning: "two to the thirtieth bytes — NOT a gigabyte, which is seven per cent smaller" }
  - { unit: byte-per-second, quantity: data-rate, factor: [1, 1], meaning: "a byte each second: the coherent unit of a data rate" }
  - { unit: bit-per-second, quantity: data-rate, factor: [1, 8], meaning: "a bit each second" }
  - { unit: megabit-per-second, quantity: data-rate, factor: [125000, 1], meaning: "a million bits each second" }
  - { unit: decibel, quantity: level, factor: [1, 1], meaning: "a RATIO on a logarithmic scale: ten decibels is a factor of ten in power. Levels ADD where the ratios they stand for multiply" }
  - { unit: decibel-per-metre, quantity: attenuation, factor: [1, 1], meaning: "level lost per metre travelled" }
  - { unit: decibel-per-kilometre, quantity: attenuation, factor: [1, 1000], meaning: "level lost per kilometre: what a fibre is rated in" }
vacancy_reasons: [prediction, impossible, out-of-context, universal]

# == LEAF SUBSUMPTION ORDERS ==
leaf_orders:
  - order: cidr
    suffix: _ip
    exact: []
    why: "an address or network is absorbed by a network that contains it (ipaddress.subnet_of)"
  - order: version
    suffix: _version
    exact: [os, version]
    why: "a release string is absorbed by a more precise one that starts with it"
  - order: containment
    system: unix-filesystem
    also_systems: [windows-filesystem]
    why: "a tree is absorbed by a subtree of it under the SAME host or logical root (`host-a:/home/user` by `host-a:/home/user/tree`). Positions on two hosts, two roots or two systems are UNORDERED and stay a disagreement: the same path on two machines is two different trees, which is the whole reason a position names its host."
  - order: instant
    every_calendar: true
    why: "a calendar reading is absorbed by a finer one it CONTAINS (`2026-09-19` by `2026-09-19 22:50+03:00`), compared by the parts actually written and in the coarser reading's own offset, never as strings. Every other pair is unordered (the `time` aspect's order is partial): two readings that do not nest stay a disagreement for a person. The absorbed reading is kept in provenance, as every subsumed value is."
vacancies:
  - at: "registry:storage_formats"
    position: ntfs
    reason: prediction
    why: >
      Measured at zero across the corpus on 2026-08-07. Declared anyway because "where does ntfs go" is
      the question that produced this registry, and the answer needs to be visible: it is a STORAGE FORMAT
      and never a path grammar. It arrives with the first Windows machine given a bean — the same one
      `os.values = windows` waits for, which is why the two vacancies rise and fall together.
  # == THE ENTRY FORMS THE OWNERSHIP TERMS OFFER ==
  - at: "owned_by.entry_one_of"
    position: contract
    reason: prediction
    why: "Co-ownership of a single facet: a facet two parties genuinely share is owned by a `contract` bean — its `parties`, the `words` they agreed in, and a clause saying how they decide when they differ. An agreement ABOUT a being (a stake, a facilitation) is not ownership of it and needs no such facet. Expected with the first facet two parties share."
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
  # == THE DEFAULT POSITION, VACANT BECAUSE A DEFAULT NO LONGER OCCUPIES ==
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

# == ASPECTS ==
  # == POSITION SYSTEMS AND RESOLUTIONS NOT YET TAKEN ==
  - at: "registry:anchor_systems"
    position: physical
    reason: prediction
    why: "No being in this estate is recorded as a physical copy yet. It is expected and not hypothetical: this ledger's first rule is that it must survive being printed on paper and rescanned, a codebase can exist as a printed listing or a disk in a drawer, and the operator named exactly that case when this term was designed. It is the one system deliberately carrying `pattern: none`, so occupying it also exercises the deliberate-absence path."
  - at: "registry:anchor_systems"
    position: geographic
    reason: prediction
    why: "Declared because CIVIL TIME RESOLVES THROUGH IT — a UTC offset is a geographic fact — so a registry offering gregorian-civil while hiding what it resolves through would conceal the chain. Unoccupied because no bean states where its machine physically is: `owns.site` holds prose (a data-centre name) that has never been read as a position. Expected to fill the first time a time reading has to be reconciled across two sites — a +03:00 host read against UTC logs is the shape of that defect."
  - at: "registry:anchor_systems"
    position: event-anchored
    reason: prediction
    why: "A position fixed only by its neighbours — 'after the push, before the cutover' — carrying no coordinate at all. Declared because it is what makes this a registry of SYSTEMS rather than a pair of coordinate schemes: sequence is the general structure and a calendar is one restriction of it. Unoccupied because every position recorded so far has had a coordinate available. Expected first in the journal, where an entry's real position is often 'between these two commits' and a date was written because the form demanded one."
  - at: "registry:anchor_systems"
    position: network-segment
    reason: prediction
    why: "WHERE A BEING IS ATTACHED in a network — a VLAN, a wireless network, an address range with a role. Declared 11.0 with the operator's ratification that a segment is a place and not an address. Unoccupied because no bean yet states which segment it is attached to; expected first where one network carries staff, guests and laptops on separate segments and the difference decides what a machine may reach."
  - at: "registry:units"
    position: second
    reason: prediction
    why: "Nothing in this ledger is currently held to the second: session moments are recorded at millisecond, and everything else at day. Kept because it is the resolution a log line carries, and the digestion of host logs is the obvious first occupant."
  # == MECHANISMS AHEAD OF THEIR OCCUPANTS ==
  - { at: "clauses.state", position: in-force, reason: universal, why: "what became of a clause, declared whole: held, met, released by the party it is owed to, broken, disputed — the states every obligation can reach, which a stranger keeping an agreement expects to find. `clauses` is occupied; a clause's state is written the day something becomes of it" }
  - { at: "clauses.state", position: met, reason: universal, why: "what became of a clause, declared whole: held, met, released by the party it is owed to, broken, disputed — the states every obligation can reach, which a stranger keeping an agreement expects to find. `clauses` is occupied; a clause's state is written the day something becomes of it" }
  - { at: "clauses.state", position: waived, reason: universal, why: "what became of a clause, declared whole: held, met, released by the party it is owed to, broken, disputed — the states every obligation can reach, which a stranger keeping an agreement expects to find. `clauses` is occupied; a clause's state is written the day something becomes of it" }
  - { at: "clauses.state", position: broken, reason: universal, why: "what became of a clause, declared whole: held, met, released by the party it is owed to, broken, disputed — the states every obligation can reach, which a stranger keeping an agreement expects to find. `clauses` is occupied; a clause's state is written the day something becomes of it" }
  - { at: "clauses.state", position: disputed, reason: universal, why: "what became of a clause, declared whole: held, met, released by the party it is owed to, broken, disputed — the states every obligation can reach, which a stranger keeping an agreement expects to find. `clauses` is occupied; a clause's state is written the day something becomes of it" }
  - { at: "parties.entry_one_of", position: external, reason: universal, why: "a party the garden holds no bean for — the bank that issued a card, a shop. `parties` is occupied through its other form, `who`; this one is declared because an agreement names parties nobody will write a bean for" }
  - { at: "registry:units", position: one, reason: universal, why: "a unit of the `ratio` quantity — a share of a cost, a rate of interest — declared as the four ways a ratio is written, because an amount a clause asks for may be one. The quantity machinery they belong to is occupied by every measured value" }
  - { at: "registry:units", position: percent, reason: universal, why: "a unit of the `ratio` quantity — a share of a cost, a rate of interest — declared as the four ways a ratio is written, because an amount a clause asks for may be one. The quantity machinery they belong to is occupied by every measured value" }
  - { at: "registry:units", position: per-mille, reason: universal, why: "a unit of the `ratio` quantity — a share of a cost, a rate of interest — declared as the four ways a ratio is written, because an amount a clause asks for may be one. The quantity machinery they belong to is occupied by every measured value" }
  - { at: "registry:units", position: basis-point, reason: universal, why: "a unit of the `ratio` quantity — a share of a cost, a rate of interest — declared as the four ways a ratio is written, because an amount a clause asks for may be one. The quantity machinery they belong to is occupied by every measured value" }
  - { at: "registry:facets", position: financial, reason: universal, why: "who pays for a being and is paid by it: in the standard because a stranger's garden expects it beside `legal`, `technical` and `experience`, the facets that are occupied" }
  - { at: "words.form", position: written, reason: universal, why: "an agreement's words, declared whole: written down, spoken aloud, or not yet put into words — the three ways any agreement stands, which a stranger keeping one expects to find. `words` is occupied through `spoken`; `written` is taken the day an agreement's text is kept in a `document`" }
  - { at: "words.form", position: unstated, reason: universal, why: "an agreement's words, declared whole: written down, spoken aloud, or not yet put into words — the three ways any agreement stands, which a stranger keeping one expects to find. `words` is occupied through `spoken`; `unstated` is an agreement that is named and whose terms nobody has put into words yet" }
# == FIGURES: the shapes an aspect may take ==
figures:
  - figure: opposition
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
# == EXTENT ==
extent_form:
  in:      "optional: the positioning SYSTEM the region is stated in. A system may be metered where its aspect is not (`geographic` in metres), and then the region may carry a measure."
  of:      "the ASPECT whose domain this region lies in. Its figure must declare `extent: possible` — an opposition's positions are modalities with nothing between them, so a region on one is refused rather than silently allowed."
  from:    "optional: the position the region starts at, in the canonical form of one of that aspect's domain systems"
  to:      "optional: the position it ends at"
  lines:   "a region spans as many LINES as its measure's unit has powers of the metered dimension — one for a length, two for an AREA, three for a VOLUME — and never more than the system it is stated in has."
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

# == RECURRENCE ==
recurrence_form:
  of:     "the SEQUENCE aspect the repetition runs along. An opposition has no neighbours, so nothing on one repeats."
  in:     "optional: the positioning SYSTEM it is counted in. Required by `each`, because a level belongs to its system."
  every:  "{ count } — every Nth NEIGHBOUR: needs only that positions have a next one. Or { count, unit } — every N UNITS: needs the aspect, or the system named, to be metered in that unit's dimension."
  each:   "<level> — the same place in EACH CELL of that level of the system named: each month, each week, each era."
  at:     "optional: where in the cell, as the system writes it — `15`, `W-5`. Prose to the gate."
  from:   "optional: the position it starts at, in the form of the system named (with no `in:`, of a system the aspect holds), and a day its calendar has"
  to:     "optional: the position it ends at, written as `from` is"
  times:  "optional: how many occurrences in all, the first included — six instalments. With `to`, whichever comes first ends it"
  requires: "exactly one of `every` / `each`"
# == VALUE TYPES ==
value_types:
  - type: iso_date
    system: gregorian-civil
    unit: day
    pattern: '^\d{4}-\d{2}-\d{2}$'
    refusal: "must be an ABSOLUTE date YYYY-MM-DD (Rule 6 paper-durable)"
    meaning: "a calendar position held to the DAY; its time of day is not known, which is different from midnight"
  - type: date
    dimension: time
    unit: day
    any_system: true
    exists: { reckoning: [arithmetic] }
    refusal: "must be an ABSOLUTE date held to the day, in the one form of the calendar it is stated in — `2026-09-20`, `persian:1405-06-29`, `hebrew:5787-01-09`, `2026-W38-7` (Rule 6 paper-durable)"
    meaning: "a position held to the DAY, in ANY calendar. What `observed`, `as_of` and `expires` are typed with: a fact is dated in the calendar it was known in, and no calendar is the one a date must be in. `iso_date` stays for a garden's own term that really means the Gregorian calendar. A day its calendar does not have is no date: where the calendar's row is reckoned in one of the ways `exists.reckoning` names, the day a position names, written back in that calendar, is the position written, and a year the reckoning cannot reach is no year. So it is for every position held to a day — a date, where a repetition starts and ends, a bound of a region in time."
  - type: kebab
    pattern: '^[a-z0-9]+(-[a-z0-9]+)*$'
    refusal: "must be kebab-case (the name is open, but still paper-durable)"
    meaning: "an open name in lowercase words joined by hyphens"
  - type: count
    pattern: '^-?(0|[1-9][0-9]{0,39})(\.[0-9]{1,40})?$'
    refusal: "must be a whole number, or a decimal written as a string (\"12.5\"), in plain decimal digits — no leading zero, at most forty digits before the point and forty after: a float has no canonical form, and a longer count is one some reader cannot hold exactly"
    meaning: "the count of a measured value — how many of its unit — written as a person writes a number, and held exactly by every reader"
  - type: text
    holds_no: Cc
    but: ["\t"]
    lines_in: block
    refusal: "a control character, which text never holds: no one reads it, and printed it moves, erases or hides what a reader's terminal shows. Text holds a tab, and a line feed only in a block scalar (`|` or `>`), whose lines are lines on the page"
    meaning: "what every key and every string value of a bean, a mapping, GARDEN.md and VOCAB.md is: characters a person reads. It holds no character of the Unicode general category `holds_no` but those in `but`, and a line feed only in a scalar of the style `lines_in` names. Every other value type is text first"
# == THE JOURNAL ==
journal:
  path: log/journal.md
  heading_form: "## <when> · <who> · <what> — <when> in a declared calendar's own form, to the minute, with its offset (`2026-09-20 15:07+03:00`, `persian:1405-06-29 15:37+03:30`)"
  system: any
  unit_at_least: minute
  checks: added
  heading: stamped
aspects:
  - aspect: necessity
    meaning: "what a being requires in order to do its work"
    figure: opposition
    poles: [[necessary, contingent], [possible, impossible]]
    positions:
      - { position: necessary,  complement: contingent, meaning: "without it the being cannot do its work at all" }
      - { position: contingent, complement: necessary,  meaning: "the being uses it, but could do its work without it" }
      - { position: possible,   complement: impossible, meaning: "the being could take it; nothing forbids it" }
      - { position: impossible, complement: possible,   meaning: "the requirement exists but the recorded target CANNOT satisfy it. Distinct from an ABSENT edge: a missing backup is a gap, while a backup that cannot work is worse, because the record makes it look present. First occupied 2026-08-02 by a domain's backup MX record that named its own primary." }

  - aspect: capability
    meaning: "what a being may or must be able to do"
    figure: opposition
    poles: [[required, omissible], [permitted, forbidden]]
    positions:
      - { position: required,  complement: omissible,  meaning: "the being MUST have it — remove it and the being stops working correctly" }
      - { position: omissible, complement: required,   meaning: "the being need not have it; its absence breaks nothing" }
      - { position: permitted, complement: forbidden,  meaning: "the being MAY have it; nothing forbids it" }
      - { position: forbidden, complement: permitted,  meaning: "the being MUST NOT have it. The enforcer may be our own policy or an outside party (a provider blocking a port), so an entry may name it in `by`." }

  - aspect: feasibility
    meaning: "whether a state of affairs CAN obtain for this being, independent of whether it is allowed"
    figure: opposition
    poles: [[necessary, contingent], [possible, impossible]]
    positions:
      - { position: necessary,  complement: contingent, meaning: "unavoidably the case — the being cannot not have it" }
      - { position: contingent, complement: necessary,  meaning: "it IS the case, but could be otherwise — which is exactly why it is worth recording" }
      - { position: possible,   complement: impossible, meaning: "not the case, but it COULD be. A prohibition sitting here is a live risk, not a formality." }
      - { position: impossible, complement: possible,   meaning: "it cannot be the case at all — something outside the rule already prevents it" }

  - aspect: confidentiality
    meaning: "whether a channel protects what crosses it from anything on the path"
    figure: opposition
    poles: [encrypted, cleartext]
    positions:
      - { position: encrypted, complement: cleartext, meaning: "the payload is unreadable to anything between the two ends" }
      - { position: cleartext, complement: encrypted, meaning: "the payload is readable by anything on the path. The DEFAULT, deliberately: a channel nobody has said protects anything does not, and a default that assumed otherwise would report an estate safer than it is." }

  - aspect: time
    meaning: "when: a position on the one line everything that happens is ordered along"
    figure: sequence
    lines: 1
    metered: time
    order: partial
    acyclic: true
    ends: open
    domain: { systems: time }
  - aspect: place
    meaning: "where: a position among the places a being can be, whether a coordinate, a site or a path in a tree"
    figure: sequence
    lines: open
    metered: none
    order: partial
    acyclic: true
    ends: bounded
    domain: { systems: place }
  - aspect: walk
    meaning: "a relation a reader can walk from being to being without coming back: ownership, habitat, part-of, dependency"
    figure: sequence
    lines: 1
    metered: none
    order: partial
    acyclic: true
    ends: open
    term_key: dag
    domain: { systems: none }
  - aspect: routine
    meaning: "the steps a procedure takes, the branches between them and the conditions that choose a branch"
    figure: sequence
    lines: open
    metered: none
    order: partial
    acyclic: false
    ends: bounded
    domain: { systems: none }

# == PROFILES ==
# == KNOWLEDGE: published classifications as UNIVERSAL ANCHORS ==
registry_files:
  - { registry: isced-f-2013, file: seed/knowledge/isced-f-2013.tsv, key: code }
  - { registry: isco-08,      file: seed/knowledge/isco-08.tsv,      key: code }
  - { registry: technology,   file: seed/knowledge/technology.tsv,   key: code }
  - { registry: crosswalk-isco-08-isced-f-2013, file: seed/knowledge/crosswalk-isco-08-isced-f-2013.tsv, key: isco_08 }
  - { registry: currencies,   file: seed/knowledge/currencies.tsv,   key: code }
# == FACETS: the aspects of ownership, one owner and one holder each ==
facets:
  - { facet: legal,      depends_on: [],      meaning: "who owns it in law, and answers for it there. Every other facet reaches it through `depends_on`" }
  - { facet: technical,  depends_on: [legal], meaning: "who runs and maintains it" }
  - { facet: experience, depends_on: [legal], meaning: "who designs how people meet it — its words, flows and look — and whose judgment of that decides" }
  - { facet: financial,  depends_on: [legal], meaning: "who pays for it and is paid by it" }
knowledge_schemes:
  - scheme: isced-f-2013
    classifies: fields of knowledge (education and training)
    publisher: UNESCO Institute for Statistics
    url: "https://uis.unesco.org/en/topic/international-standard-classification-education-isced"
    levels: [ { level: broad }, { level: narrow }, { level: detailed } ]
    neighbours: none
    sources: seed/knowledge/SOURCES.md
  - scheme: isco-08
    classifies: occupations
    publisher: International Labour Organization
    url: "https://ilostat.ilo.org/methods/concepts-and-definitions/classification-occupation/"
    levels: [ { level: major }, { level: sub-major }, { level: minor }, { level: unit } ]
    same_ground_as: [isced-f-2013]
    crosswalk: table
    neighbours: none
    sources: seed/knowledge/SOURCES.md
  - scheme: technology
    classifies: established technologies (software, protocols, operating systems), each with its OFFICIAL documentation
    publisher: daftar (curated; every row names the project's own documentation, never a third party's)
    url: "seed/knowledge/technology.tsv"
    levels: [ { level: technology } ]
    within: [isced-f-2013]
    neighbours: none
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
      meaning: >
        The on-disk code trees a code bean is built from or references. Each entry is a CLASSED path so any
        agent locates code without re-walking a tree, and knows which trees are reference-only (never re-scanned
        each session — consult summary_ref + grep only for one specific symbol on demand).
      context_keys: ["code_paths"]
      schema:
        shape: list_of_entries
        required_on_gene: [codebase]
        attrs:
          path:         { required: true, in: { pattern: "^(root:[a-z0-9][a-z0-9-]*(/[^:]*)?|[a-z0-9][a-z0-9.-]*:([/A-Za-z]).*)$", soft: true, why: "a bare absolute path names no host: give it `root:<name>/…` (resolved by each host's `roots`) or `<host>:<path>`" }, meaning: "WHERE THE TREE IS, as a position: `root:<name>[/<relative>]` resolved through each host's own `roots` map, or `<host>:<absolute path>` stated outright. A bare absolute path names no host and WARNS (11.0): this estate holds 13 paths that exist on two machines as two different trees, so a path with no host is a position in a system nobody named." }
          role:         { required: true, in: [own-source, framework-reference, vendored-dependency, generated-artifact], meaning: "own-source | framework-reference | vendored-dependency | generated-artifact" }
          scan_policy:  { required: true, in: [index, reference-only, skim], meaning: "index (own code — walk fully) | reference-only (do NOT re-scan each session; consult analysis_cache, grep on demand only) | skim (structure only)" }
          stack:        { in: { type: kebab }, meaning: "language/runtime tag, e.g. python-django | csharp-dotnet (optional)" }
          entrypoint:   { in: prose, meaning: "manifest / solution / addin that roots the tree (optional)" }
          note:         { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" }
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
      anchor: { class: logical, establishing: true }
      merge: { cardinality: single, order: none }
      canonical: "verbatim remote string (e.g. host:path or scheme URL); lowercase host only"
      promotion: { status: candidate, note: "general (any code garden has repos) — REVIEW in the attrs-to-universal session" }
    - term: git_host
      meaning: "the being hosting the source repository of a code bean (storage habitat, not ownership)"
      context_keys: ["git_host"]
      schema:
        shape: mapping
        is_ref: true
        attrs:
          bean:  { required: true, in: id }
          repo:  { in: { pattern: "^[a-z0-9][a-z0-9.-]*:[^ ]+$" }, meaning: "the repository AS ITS HOST NAMES IT (`host-a:git/ledger.git`) — what a clone that has forgotten its remote needs" }
      merge: { cardinality: single, order: none }

  network:
    meaning: >
      for a garden that manages machines that talk to each other: what a being ANSWERS ON, what it
      REACHES FOR, the LINKS those ride over, and what a forwarding device DOES to traffic in between.
      A garden with one host and no network should inherit none of it.
    vacancies:
    - at: "registry:net_protocols"
      position: pptp
      reason: impossible
      why: >
        Nothing in this estate speaks it and nothing ever should. `impossible` rather than `prediction`,
        which is the whole point of registering it: MS-CHAPv2 and MPPE are broken by published attacks,
        so a pptp tunnel protects nothing while presenting as a VPN in every inventory that lists it.
        Measured: zero occurrences across the estate it was declared in. Declaring the
        position and refusing it is how the estate states a standing decision that would otherwise exist
        only as an absence — and an absence is indistinguishable from nobody having thought about it.
    - { at: "registry:net_protocols", position: ipv4, reason: universal, why: "declared because the structure is general, not because this garden expects an occupant (CONTRIBUTING: a mechanism may precede its occupants)" }
    - { at: "registry:net_protocols", position: ipv6, reason: universal, why: "declared because the structure is general, not because this garden expects an occupant (CONTRIBUTING: a mechanism may precede its occupants)" }
    - { at: "registry:net_protocols", position: icmp, reason: universal, why: "declared because the structure is general, not because this garden expects an occupant (CONTRIBUTING: a mechanism may precede its occupants)" }
    - { at: "registry:net_protocols", position: arp, reason: universal, why: "declared because the structure is general, not because this garden expects an occupant (CONTRIBUTING: a mechanism may precede its occupants)" }
    - { at: "registry:net_protocols", position: dot1q, reason: universal, why: "declared because the structure is general, not because this garden expects an occupant (CONTRIBUTING: a mechanism may precede its occupants)" }
    - { at: "registry:net_protocols", position: stp, reason: universal, why: "declared because the structure is general, not because this garden expects an occupant (CONTRIBUTING: a mechanism may precede its occupants)" }
    - { at: "registry:net_protocols", position: lldp, reason: universal, why: "declared because the structure is general, not because this garden expects an occupant (CONTRIBUTING: a mechanism may precede its occupants)" }
    - { at: "registry:net_protocols", position: gre, reason: universal, why: "declared because the structure is general, not because this garden expects an occupant (CONTRIBUTING: a mechanism may precede its occupants)" }
    - { at: "registry:net_protocols", position: ipsec, reason: universal, why: "declared because the structure is general, not because this garden expects an occupant (CONTRIBUTING: a mechanism may precede its occupants)" }
    - { at: "registry:net_protocols", position: vxlan, reason: universal, why: "declared because the structure is general, not because this garden expects an occupant (CONTRIBUTING: a mechanism may precede its occupants)" }
    - { at: "registry:net_protocols", position: ospf, reason: universal, why: "declared because the structure is general, not because this garden expects an occupant (CONTRIBUTING: a mechanism may precede its occupants)" }
    - { at: "registry:net_protocols", position: is-is, reason: universal, why: "declared because the structure is general, not because this garden expects an occupant (CONTRIBUTING: a mechanism may precede its occupants)" }
    - { at: "registry:net_protocols", position: rip, reason: universal, why: "declared because the structure is general, not because this garden expects an occupant (CONTRIBUTING: a mechanism may precede its occupants)" }
    - { at: "registry:net_protocols", position: eigrp, reason: universal, why: "declared because the structure is general, not because this garden expects an occupant (CONTRIBUTING: a mechanism may precede its occupants)" }
    - { at: "registry:net_protocols", position: bgp, reason: universal, why: "declared because the structure is general, not because this garden expects an occupant (CONTRIBUTING: a mechanism may precede its occupants)" }
    - { at: "registry:net_protocols", position: vrrp, reason: universal, why: "declared because the structure is general, not because this garden expects an occupant (CONTRIBUTING: a mechanism may precede its occupants)" }
    - { at: "registry:net_protocols", position: dhcp, reason: universal, why: "declared because the structure is general, not because this garden expects an occupant (CONTRIBUTING: a mechanism may precede its occupants)" }
    - { at: "registry:net_protocols", position: ntp, reason: universal, why: "declared because the structure is general, not because this garden expects an occupant (CONTRIBUTING: a mechanism may precede its occupants)" }
    - { at: "registry:net_protocols", position: snmp, reason: universal, why: "declared because the structure is general, not because this garden expects an occupant (CONTRIBUTING: a mechanism may precede its occupants)" }
    - at: "registry:net_protocols"
      position: tcp
      reason: prediction
      why: >
        Every endpoint recorded so far takes its transport from its protocol's row, and A DEFAULT DOES NOT OCCUPY:
        a position is taken by an entry that STATES it. Expected first where a protocol answers on a transport
        other than its usual one — the DNS server that answers on 53/tcp as well as 53/udp.
    - at: "registry:net_protocols"
      position: udp
      reason: prediction
      why: "As for tcp: no entry has yet needed to state it, because the protocols that use it say so in their own rows."
    - at: "registry:anchor_systems"
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
    - term: endpoints
      meaning: >
        The listening surfaces this being offers: for each, the protocol spoken, the address system and
        address it answers at, the port, and what the channel protects. An endpoint entry is a STATEMENT
        THAT THE BEING ANSWERS THERE — which is why a `forbidden` position on one is a breach by itself.
      context_keys: [endpoints]
      schema:
        shape: list_of_entries
        attrs:
          protocol:         { required: true, in: { registry: net_protocols, take: protocol }, meaning: "which protocol is spoken here — a row of net_protocols, never an implementation name" }
          system:           { required: true, in: { registry: anchor_systems, take: system, where: { dimension: [place, any] } }, meaning: "the PLACE system the surface is stated in — `ipv4` or `ipv6` for a network address, `unix-filesystem` for a socket path. It selects the form `at` must take. Named `system`, as in `roots`, `located_at` and `timing`: `keyed_by` resolves a registry row by a field that exists on BOTH the entry and the row, so the two are one name by construction." }
          at:               { required: true, in: { form_of: anchor_systems, keyed_by: system, take: pattern }, meaning: "the address answered at, in that system's ONE canonical form" }
          exposure:         { in: [loopback, lan, link, internet], meaning: "loopback (this machine only) | lan (the local segment) | link (reachable only over a named link, e.g. the wireguard tunnel) | internet (bound to a public address directly)" }
          observed:         { in: { type: date }, meaning: "ABSOLUTE date the surface was checked. Endpoints age faster than almost anything else here." }
          confidentiality:  { in: { aspect: confidentiality, default: cleartext }, meaning: "the position on the confidentiality aspect — what the channel protects. Defaults to cleartext, because a channel nobody has said protects anything does not." }
          permission:       { in: { aspect: capability, default: permitted }, meaning: "the position on the capability aspect — whether this surface MAY exist at all" }
          transport:        { in: { registry: net_protocols, take: protocol, where: { layer: transport } }, default_from: { registry: net_protocols, keyed_by: protocol, take: transport }, meaning: "tcp | udp — which transport's port space `port` is a position in. Defaults to the protocol row's `transport`." }
          plane:            { in: { registry: planes, take: plane }, meaning: "data | control | management — what this is FOR. Stated where it matters: a management surface deserves a different exposure from a data one." }
          port:             { in: { form_of: anchor_systems, keyed_by: transport, take: pattern }, meaning: "the port: a position in the transport's port space, WITHIN the address beside it. One port per entry. Omitted where the protocol rides another (sftp over ssh) and has none of its own, and for a socket path, which has none at all." }
          via_link:         { in: { key_of: links }, meaning: "optional: the `links` key this surface is reachable over, when it is not reachable without it" }
          admitted_from:    { in: prose, meaning: "WHO may reach this surface, when not everyone who can reach its address may: the named sources the being itself admits, and where that is enforced. A second fact beside `exposure`, which says only WHERE the surface is bound. Absent means nothing restricts it." }
        cells:
          - { when: { permission: forbidden }, verdict: in_breach, why: "a listening surface that MUST NOT exist, recorded as existing. Unlike a capability, an endpoint entry is not a stance about a possibility — it is a statement that the being answers there — so `forbidden` alone is the breach and needs no second aspect to confirm it. A database container published on 0.0.0.0:5432, reachable across the LAN, is this shape." }
          - { when: { permission: required, confidentiality: cleartext, exposure: [lan, link, internet] }, verdict: in_breach, why: "a channel the estate REQUIRES and which protects nothing on the wire, on a path something else can be on. A mail policy that forces cleartext delivery to a partner domain that mail must still reach is exactly this, so the requirement and the exposure are both real and neither can simply be withdrawn." }
          - { when: { plane: management, exposure: internet }, expects: [admitted_from], why: "a MANAGEMENT surface bound to a public address, with nothing said about who may reach it: as recorded, the way an operator configures this being answers anyone, guarded only by its login. Restrict it to named sources and state them in `admitted_from`." }
      merge: { cardinality: multi, order: "by-protocol+system+at+port?" }
    - term: links
      meaning: >
        The links this being terminates: physical interfaces and the tunnels that manufacture one. A
        tunnel is not a special case here — it is a link whose `protocol` row declares
        `synthesizes_link`, which is what lets other traffic be recorded as riding it.
      context_keys: [links]
      schema:
        shape: open_map_of_entries
        key_form: kebab
        attrs:
          protocol:         { required: true, in: { registry: net_protocols, take: protocol }, meaning: "what makes this link — wireguard for a tunnel, and a physical row where one exists" }
          observed:         { in: { type: date }, meaning: "ABSOLUTE date the link was checked" }
          peer:             { in: ref, meaning: "a {bean, field} ref to the far end. A REF, not a retyped address: this is the field whose absence produced the .169/.146 contradiction." }
          confidentiality:  { in: { aspect: confidentiality, default: cleartext }, meaning: "what the link protects, for everything carried over it" }
          plane:            { in: { registry: planes, take: plane }, meaning: "data | control | management — what this is FOR." }
          carried_by:       { in: { key_of: links }, meaning: "optional: the `links` entry this one rides over — a tunnel rides a WAN link rides an interface" }
      dag_note: >
        NOTHING HERE IS ACYCLIC, and the first draft of this term got that wrong twice in one line. It
        carried `dag: true` over `peer` and `carried_by`, and the design review caught both before any bean
        was written. `peer` is MUTUAL — a router peers a VPS and the VPS peers the router — so the acyclic check
        would have refused the very first tunnel recorded honestly: a rule made unsatisfiable by its own
        subject matter. `carried_by` names another entry on THE SAME bean, so it is not a cross-bean edge
        and there is no graph to walk; it is documented ordering, and it is deliberately NOT `in: ref`.
        PROTOCOL carriage is separately and permanently not acyclic — wireguard is carried by udp over
        ipv4 and then carries ipv4, because that recursion is what encapsulation IS — which is why
        `rides_on` in the registry is descriptive and joins no check. Written at this length because a rule
        that cannot be satisfied is worse than no rule: it is the failure `inverse_of` already carries a
        cardinality to avoid, met twice more in a single term.
      merge: { cardinality: multi, order: by-key }
    - term: reaches
      meaning: >
        The beings this one must be able to reach in order to work, each naming the protocol it reaches
        for and how badly it needs it. It takes positions on the EXISTING `necessity` aspect, because
        needing a network peer is not a new modality — it is what `consumes` and `depends_on` already are.
      context_keys: [reaches]
      schema:
        shape: open_map_of_entries
        key_form: kebab
        attrs:
          protocol:   { required: true, in: { registry: net_protocols, take: protocol }, meaning: "what it speaks to get there" }
          observed:   { in: { type: date }, meaning: "ABSOLUTE date the reach was verified to work" }
          target:     { in: ref, meaning: "a {bean[, field]} ref to what it reaches. A ref rather than an address, so the far end stays the one owner of its own address." }
          necessity:  { in: { aspect: necessity, default: necessary }, meaning: "the position on the necessity aspect — `necessary` if the being cannot do its work without it" }
          via_link:   { in: { key_of: links }, meaning: "optional: the link this reach must cross" }
      merge: { cardinality: multi, order: by-key }
    - term: treatments
      meaning: >
        What a forwarding device does to traffic crossing it: the routes, address translations, packet
        marks and access lists that decide where something goes and whether it arrives at all. Required
        on a router, because a router that documents no treatment has documented nothing about itself.
      context_keys: [treatments]
      schema:
        shape: list_of_entries
        required_on_roles: [router]
        attrs:
          kind:        { required: true, in: [route, nat, mangle, acl, queue], meaning: "route (where traffic goes) | nat (what its addresses become) | mangle (what marks it carries) | acl (whether it is allowed at all) | queue (what bandwidth it gets)" }
          plane:       { in: { registry: planes, take: plane }, meaning: "data | control | management — what this is FOR." }
          what:        { required: true, in: prose, meaning: "the treatment itself, briefly. A POINTER to the device's own config, never a copy of it — ground rule 3: the router owns its rules and they are not hand-edited from here." }
          why:         { required: true, in: prose, meaning: "what breaks if it is removed. This is the load-bearing attr: a treatment with no stated consequence is an inventory row, and inventory is what the device's own export already gives you." }
          observed:    { in: { type: date }, meaning: "ABSOLUTE date the treatment was read off the device" }
          to:          { in: ref, meaning: "optional: a {bean, field} ref to where the treatment sends traffic" }
          permission:  { in: { aspect: capability, default: permitted }, meaning: "the position on the capability aspect. `required` is the one that earns this term: a server's outbound SPF identity can DEPEND on firewall mangle marks, and today that is a prose safety note nothing enforces." }
      merge: { cardinality: multi, order: by-kind+what }
  domain:
    meaning: >
      for a garden that holds delegated names — registered domains. The one class of fact that can lose a name
      outright is its registration: an unrenewed domain takes its DNS and its mail with it. A garden with no
      domains should inherit none of it.
    terms:
    - term: registration
      meaning: "the registration facts of a delegated name: who holds the record, when it lapses, and when that was last observed"
      context_keys: ["registration"]
      schema:
        shape: mapping
        required_on_gene: [domain]
        expiry:
          attr: expires
          notice: { of: time, measure: { count: 90, unit: day } }
          why: "an unrenewed name takes its DNS and its mail with it"
        attrs:
          registrar:   { required: true, in: prose, meaning: "the registrar of record — who the renewal is actually paid to" }
          created:     { required: true, in: { type: date }, meaning: "ABSOLUTE date the registration began" }
          expires:     { required: true, in: { type: date }, meaning: "ABSOLUTE date it lapses if unrenewed — the fact that can lose the name" }
          auto_renew:  { required: true, in: [enabled, disabled, unknown], meaning: "enabled | disabled | unknown. `unknown` is the honest default: it is a registrar-ACCOUNT setting and does not appear in WHOIS, so it cannot be observed the way the dates can." }
          observed:    { required: true, in: { type: date }, meaning: "ABSOLUTE date these facts were read. They age: an expiry moves on renewal, and a registrar changes on transfer." }
          source:      { required: true, in: prose, meaning: "where they were read from" }
          registrant:  { in: prose, meaning: "optional: the party holding the registration, where the registry discloses it" }
          note:        { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" }
      merge: { cardinality: single, order: none }
    vacancies:
    - { at: "registration.auto_renew", position: enabled, reason: universal, why: "whether the registrar renews the name by itself, declared whole — on, off, or not known — because every registration is in one of the three; a garden holding a few names takes one or two of them" }
    - { at: "registration.auto_renew", position: disabled, reason: universal, why: "whether the registrar renews the name by itself, declared whole — on, off, or not known — because every registration is in one of the three; a garden holding a few names takes one or two of them" }
    - { at: "registration.auto_renew", position: unknown, reason: universal, why: "whether the registrar renews the name by itself, declared whole — on, off, or not known — because every registration is in one of the three; a garden holding a few names takes one or two of them" }

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
      meaning: "how this being stands to published knowledge: classified as an occupation, drawing on a field, using a technology"
      context_keys: [knowledge]
      schema:
        shape: list_of_entries
        attrs:
          scheme:  { required: true, in: { registry: knowledge_schemes, take: scheme }, meaning: "which classification: isced-f-2013, isco-08, technology" }
          code:    { required: true, in: { registry_from: scheme, take: code }, meaning: "the code in it" }
          rel:     { required: true, in: [classified_as, draws_on, uses], meaning: "classified_as (this IS of that kind) | draws_on (this rests on that knowledge) | uses (this runs that technology)" }
          topic:   { in: prose, meaning: "optional: the concept inside the field this draws on" }
          note:    { in: prose, meaning: optional }
      merge: { cardinality: multi, order: by-scheme+code+rel }

terms:
  - term: capabilities
    meaning: "what this being may or must be able to do: an OPEN map of capability name -> the stance taken on it"
    context_keys: ["capabilities"]
    schema:
      shape: open_map_of_entries
      key_form: kebab
      attrs:
        why:              { required: true, in: prose, meaning: "WHY this stance holds — the consequence of violating it, in prose an operator can act on" }
        permission:       { in: { aspect: capability, default: permitted }, meaning: "the position taken on the capability aspect (required | omissible | permitted | forbidden)" }
        feasibility:      { in: { aspect: feasibility, default: possible }, meaning: "the position on the feasibility aspect — whether the being CAN be in that state at all, independent of whether it may. `forbidden` + `possible` is a live risk; `forbidden` + `impossible` is already prevented by something else." }
        by:               { in: prose, meaning: "optional: who imposes it, when the enforcer is not us (e.g. a hosting provider)" }
        feasibility_why:  { in: prose, meaning: "optional: WHY the feasibility position holds — a sysctl is reversible, a kernel flag is not. Distinct from `why`, which is the reason for the PERMISSION" }
      cells:
        - { when: { permission: required, feasibility: impossible }, verdict: incoherent, why: "an unsatisfiable requirement — it must be had and cannot be. Either the requirement is not real, or the impossibility is not, and until that is resolved the entry asserts a contradiction." }
        - { when: { permission: forbidden, feasibility: necessary }, verdict: incoherent, why: "an unenforceable prohibition — it must not be had and unavoidably is. A rule that cannot be obeyed is not a rule; the being needs a different mitigation, or the necessity is overstated." }
        - { when: { permission: required, feasibility: possible }, verdict: in_breach, why: "REQUIRED but NOT CURRENTLY THE CASE — the requirement is unmet right now." }
        - { when: { permission: forbidden, feasibility: contingent }, verdict: in_breach, why: "FORBIDDEN but CURRENTLY THE CASE — the prohibition is being violated right now." }
    merge: { cardinality: multi, order: by-capability }
  - term: consumes
    meaning: "an input this being requires — the produced state of another being that it reads to do its work"
    context_keys: ["consumes"]
    schema:
      shape: list_of_entries
      is_ref: true
      attrs:
        necessity:  { in: { aspect: necessity, default: necessary } }
    merge: { cardinality: multi, order: "by-bean?+mapping?+field?" }
  - term: refs
    meaning: "the open residual relation: any typed edge outside the canonical set, self-described by `rel`"
    context_keys: ["refs"]
    schema:
      shape: open_map_of_entries
      is_ref: true
      attrs:
        rel:   { required: true, in: { type: kebab }, meaning: "the relation TYPE, kebab-case and open" }
        path:  { in: { pattern: "^(root:[a-z0-9][a-z0-9-]*(/[^:]*)?|[a-z0-9][a-z0-9.-]*:([/A-Za-z]).*)$", soft: true, why: "a bare or relative path names no host, and means something else from every other working copy" }, meaning: "INSTEAD of a bean: a pointer to something that is not a managed object here — an off-garden document. The residual relation's own residual, kept since the relation algebra was declared" }
        note:  { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" }
    merge: { cardinality: multi, order: by-key }
  - term: depends_on
    meaning: "a being this being requires to function; recovery ordering reads this edge"
    context_keys: ["depends_on"]
    schema:
      shape: open_map_of_entries
      dag: true
      is_ref: true
      attrs:
        necessity:  { in: { aspect: necessity, default: necessary } }
    merge: { cardinality: multi, order: by-bean }
  # == CORE GRAMMAR ENUMS ==
  - term: status
    meaning: "the lifecycle state of a bean"
    context_keys: ["status"]
    schema:
      path: status
      values: [active, planned, deprecated, draft, closed]
    merge: { cardinality: single, order: none }
  - term: identity_status
    meaning: "whether a bean's identity is established or still provisional (MERGE.md §4)"
    context_keys: ["identity.status"]
    schema:
      path: identity.status
      values: [confirmed, provisional]
  - term: anchor_class
    meaning: "the KIND of evidence an anchor is: hardware (matter), logical (an id, a name, a key pair), network (an address), role (a job that moves between beings). The nature's family is stated in these classes, so the class of an establishing anchor is what the family rule reads; a term that governs the key declares it"
    context_keys: ["identity.anchors[].class"]
    schema:
      path: identity.anchors[].class
      values: [hardware, logical, network, role]
  - term: provenance_src
    meaning: "how a fact came to be known. `inferred` may NEVER auto-override `asserted-by-human` (MODEL Rule: the provenance guard)."
    context_keys: ["provenance.src"]
    schema:
      path: provenance.src
      values: [observed, inferred, asserted-by-human, generated-by-tool]
    merge: { order: "generated-by-tool<inferred<observed<asserted-by-human", borrows: generated-by-tool }
    values_meaning:
      asserted-by-human: "a person said so, and answers for it. The top, because a person can be ASKED, and because the fact may be one only a person can know (who owns this, what was agreed). The guard protects this place and no other."
      observed:          "read directly off the world by whoever recorded it — a command's output, a file, a registry reply. It can be re-read, which is its whole authority."
      inferred:          "reasoned from observations rather than read. Someone weighed evidence and may be wrong; the fact is recorded so it can be found, and is not settled."
      generated-by-tool: "COMPUTED from other recorded facts by a program: a merged bean, a generated config, a count. A tool knows NOTHING of its own — it cannot be wrong about the world, only about its inputs, and it cannot be right about more than they were. So this src has no standing of its own and BORROWS it: a generated fact ranks as the WEAKEST src named in its `provenance.from` (a chain is as strong as its weakest link), and sits at the bottom of the rank only when it names none — because a derivation that will not say what it derives from is worth less than a guess that owns up to being one."
  - term: analysis_cache
    meaning: >
      An OPEN map of typed, provenance-stamped, staleness-keyed analysis results, held on the bean that owns the
      analysed thing. Each entry STANDS IN FOR re-running that analysis for as long as its staleness_key still
      matches the live source; once the key moves, the entry is STALE and must not be trusted.
    context_keys: ["analysis_cache"]
    schema:
      shape: open_map_of_entries
      key_form: kebab
      required_on_gene: [codebase]
      attrs:
        produced_by:     { required: true, in: { pattern: "^((agent|tool|human):[^ ].*|[^ :][^:]* \\(.+\\))$", soft: true, why: "attribution has one convention across the ledger — `agent:<model>/<garden>` for an agent, `tool:<name>` for a tool, `name (role)` for a person — so that `who to ask` can be read by something" }, meaning: "the agent/tool id that produced this analysis (provenance — who to ask, who to blame)" }
        as_of:           { required: true, in: { type: date }, meaning: "ABSOLUTE date the analysis was produced, YYYY-MM-DD (Rule 6 paper-durable)" }
        staleness_key:   { required: true, in: { pattern: "^([a-z0-9][a-z0-9._-]*@[0-9a-f]{7,40}|manual:.+)$" }, meaning: "the value that makes this entry VALID; when it MOVES, the entry is STALE. The FORM is the pattern this attribute declares, beside this sentence, and is not restated here: `<repo>@<object-id>`, a position in a named repository's object graph, or `manual:<why>` for what no key can track. Until 2026-09-20 this line listed three spellings — the git-head, the digest and the manual one — two of which the pattern had already refused since 11.0. A person reading the term was taught the form the gate rejects, which is the same defect as a law the code ignores, pointing the other way. (The superseded wording is in git, and is deliberately NOT quoted here: a document that quotes a spelling it is abolishing still contains it, and the check in test/place.py cannot tell a quotation from a lesson. Nor should it have to.)" }
        policy:          { required: true, in: [index, reference-only, skim], meaning: "index | reference-only | skim — how the analysed source is to be treated" }
        form:            { in: [summary_ref, inline, external], meaning: "summary_ref | inline | external — where the cached result physically lives" }
        covers_paths:    { in: { pattern: "^(root:[a-z0-9][a-z0-9-]*(/[^:]*)?|[a-z0-9][a-z0-9.-]*:([/A-Za-z]).*)$", soft: true, why: "a bare absolute path names no host — the same defect `code_paths.path` carries" }, meaning: "the code_paths path(s) this entry analysed — this is WHERE an agent re-checks staleness_key" }
        summary_ref:     { in: { pointer: bean_field_pointer }, meaning: "REQUIRED when form: summary_ref. A pointer, or a list of pointers, to the recorded result. Each pointer is either '<section>.<key>' (a field on THIS bean, gate-resolved), or {bean: <id>, field: <key>} (a field on ANOTHER bean, gate-resolved), or 'file:<path>' (an on-disk document)." }
        relevant_scope:  { in: prose, meaning: "optional: which part of a large covered tree matters to THIS bean (e.g. 'CE module: hr')" }
        digest:          { in: { pattern: "^[a-z0-9]+:[0-9a-f]{7,}$" }, meaning: "optional short content hash of the cached result itself" }
      cells:
        - { when: { form: summary_ref }, requires: [summary_ref] }
        - { when: { staleness_key: { starts_with: "manual:" } }, expects: [covers_paths], why: "an agent cannot tell where to re-check it" }
    open_keys: true
    key_note: >
      kebab-case <cache_type>. Known types so far (a NON-exhaustive registry, NOT an enum the gate enforces):
      code-structure | framework-surface | api-surface | api-client-contract | security-surface | bcf-domain.
      Anticipated: dep-graph | sql-schema | revit-ui | csharp-api | python-models | test-coverage.
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
  - term: nature
    meaning: "the ontological category of a being; routes it to the correct branch of the ownership crown"
    context_keys: ["nature"]
    schema:
      shape: scalar
      values_from: "registry:natures[].nature"
      required: true
      must_equal_genos_attr: of_nature
    merge: { cardinality: single, order: none }
  - term: owned_by
    meaning: "who owns a being, per facet; introduced (explicit) at a node and inherited down the tree"
    context_keys: ["owned_by"]
    schema:
      shape: mapping
      required: true
      alt_form: { key: via, ref_fields: [via] }
      key_form: "values_from:registry:facets[].facet"
      entry_one_of: [owner, contract, external, crown]
      entry_must_match:
        - { attr: crown, registry: natures, keyed_by: nature, take: crown }
      entry_form_from_genos_attr: ownership_form
      dag: true
      attrs:
        owner:     { in: ref }
        contract:  { in: ref }
        since:     { in: { type: date }, meaning: "optional: ABSOLUTE date this owner came to hold the facet" }
        note:      { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" }
    forms:
      explicit:  "owned_by: { <facet>: { owner: {bean: <person|org>} }, ... }   # introduce facet-owners here"
      inherited: "owned_by: { via: {bean: <parent>} }                           # inherit parent's facet-owners"
      co_owned:  "owned_by: { <facet>: { contract: {bean: <contract>} } }       # a SINGLE facet co-owned -> a contract resolves it"
      external:  "owned_by: { <facet>: { external: '<who>' } }                  # owned OUTSIDE this garden (third-party software, a vendor); names the owner in prose because they are not a managed object here"
      crown:     "owned_by: { <facet>: { crown: <branch> } }                     # ownership TERMINATES at the axiom; the branch must be the one this bean's nature routes to. A person is pinned to it; an agreement between parties, or a happening between people, may choose it — owned by none of them"
    merge: { cardinality: multi, order: by-facet }
  - term: responsibility
    meaning: "who ANSWERS FOR this being, per facet — the arc that makes an ownership claim actionable"
    context_keys: ["responsibility"]
    schema:
      shape: mapping
      alt_form: { key: via, ref_fields: [via] }
      key_form: "values_from:registry:facets[].facet"
      entry_one_of: [holder, contract, external, self, parties]
      entry_form_from_genos_attr: responsibility_form
      facet_parity_with: owned_by
      dag: true
      attrs:
        holder:    { in: ref }
        contract:  { in: ref }
        since:     { in: { type: date }, meaning: "optional: ABSOLUTE date this holder came to answer for the facet" }
        note:      { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" }
    forms:
      explicit:  "responsibility: { <facet>: { holder: {bean: <person|org>} } }"
      inherited: "responsibility: { via: {bean: <parent>} }"
      shared:    "responsibility: { <facet>: { contract: {bean: <contract>} } }   # shared duty -> a contract, as with co-ownership"
      external:  "responsibility: { <facet>: { external: '<who>' } }              # answered for outside this garden"
      self:      "responsibility: { <facet>: { self: true } }                      # a being answers for ITSELF (persons). Reflexive, so it is deliberately NOT an edge — a self-edge would be a cycle, and autonomy is not a dependency."
      parties:   "responsibility: { <facet>: { parties: true } }                   # an agreement is answered for by the parties it binds, each for its own clauses. Reflexive like `self`: the parties are named in `parties`, so this draws no edge. Reserved to the gene that name it (an agreement)."
    rules:
      parity: "every facet with an OWNER must have a HOLDER and vice versa. An ownership claim nothing answers for is a loose end; a duty nobody owns is orphaned."
      not_the_same_as_ownership: "they are opposite arcs, not synonyms. A rented VPS is owned by the provider and answered for by the operator; that is the normal case, not an exception."
    merge: { cardinality: multi, order: by-facet }
  - term: instance_of
    meaning: "the code product a running instance (token) instantiates"
    context_keys: ["instance_of"]
    schema:
      shape: mapping
      required_on_gene: [instance]
      is_ref: true
      attrs:
        bean:  { required: true, in: id }
    form: "instance_of: {bean: <product|codebase>}"
    merge: { cardinality: single, order: none }
  - term: lives_in
    meaning: "the immediate habitat a token lives in/on; recursive (habitat may itself be a token); a DAG"
    context_keys: ["lives_in"]
    schema:
      shape: mapping
      required_on_gene: [instance]
      dag: true
      is_ref: true
      attrs:
        bean:  { required: true, in: id }
    form: "lives_in: {bean: <habitat>}   # follow the chain for the full stack"
    merge: { cardinality: single, order: none }
  - term: provides_habitat
    meaning: "the kind of habitat this being offers to the tokens that live in it"
    context_keys: ["provides_habitat"]
    schema:
      shape: scalar
      required_on_targets_of: lives_in
    merge: { cardinality: single, order: none }
  - term: part_of
    meaning: "the whole this being is a component of (composition; a being is part_of at most one whole)"
    context_keys: ["part_of"]
    schema:
      shape: mapping
      dag: true
      is_ref: true
      attrs:
        bean:  { required: true, in: id }
    merge: { cardinality: single, order: none }
  - term: creator
    meaning: "the being that made this being"
    context_keys: ["creator"]
    schema:
      shape: mapping
      is_ref: true
      attrs:
        bean:  { required: true, in: id }
    merge: { cardinality: single, order: none }
  - term: ip
    meaning: "an Internet Protocol address identifying a network interface/endpoint"
    context_keys: ["*_ip", "*_ips", "provides_ip", "identifiers.ipv4", "identifiers.ipv6"]
    schema:
      governs_anchor: ip
      value_form: ip
    anchor: { class: network, establishing: false }
    merge: { cardinality: single, order: cidr, authority: "scanned<operator-asserted<external" }
    canonical: "python ipaddress normal form (v4/v6); reject bad octets"
    escape: "bean `shared_identifiers:` (floating/VRRP/anycast), or the network the address is on (reused private range)"
    exceptions:
      - { case: "shared/floating/VRRP/anycast IP", decision: "co-owned; own-bean+ref OR shared_identifiers", why: "many nodes answer for one address", acked: 2026-07-31 }
      - { case: "reused RFC1918 range on isolated LANs", decision: "qualify with the network it is on", why: "private ranges exist independently", acked: 2026-07-31 }
      - { case: "dotted-quad that is NOT an ip (v17.0.0.0, CIDR base)", decision: "only values under context_keys are ips; parse with ipaddress", why: "free-text mis-read as IPs", acked: 2026-07-31 }
      - { case: "IPv6 / abbreviated shorthand (.160)", decision: "canonical full form required; ipv6 deduped", why: "invisible to IPv4-only check", acked: 2026-07-31 }
  - term: hostname
    meaning: "a machine's OS hostname"
    context_keys: ["hostname", "identity.anchors[].hostname"]
    schema:
      governs_anchor: hostname
      value_pattern: '^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)*$'
      canonical_note: "lowercase; one label or dotted"
    anchor: { class: network, establishing: false }
    merge: { cardinality: single, order: none }
    canonical: "lowercase"
  - term: fqdn
    meaning: "a DNS-unique fully-qualified domain name. Logical: it ESTABLISHES a being whose family is logical (a domain, a service, a virtual-host) and only CORROBORATES a body (nature soma), whose matter identifies it — a replaced machine keeps its name. The nature's family decides; the bean writes the flag that follows"
    context_keys: ["fqdn"]
    schema:
      governs_anchor: fqdn
      value_pattern: '^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$'
      canonical_note: "IDNA + lowercase; at least two labels"
    anchor: { class: logical }
    merge: { cardinality: single, order: none }
    canonical: "IDNA + lowercase"
  - term: mac
    meaning: "an IEEE MAC address of a NIC. Matter when burned into a physical NIC, and then it establishes; a virtual NIC's is assigned by the hypervisor and only corroborates — the nature decides"
    context_keys: ["mac", "*_mac"]
    schema:
      governs_anchor: mac
      value_pattern: '^([0-9a-f]{2}:){5}[0-9a-f]{2}$'
      canonical_note: "lowercase colon form"
    anchor: { class: hardware }
    merge: { cardinality: set, order: none }
    canonical: "lowercase colon form"
    exceptions:
      - { case: "cloned/spoofed or reused MAC (freed lease)", decision: "scope+date the anchor; never sole establisher if transient", why: "MACs can be duplicated", acked: 2026-07-31 }
  - term: serial
    meaning: "a hardware/chassis serial or asset serial"
    context_keys: ["serial", "identity.anchors[].serial"]
    schema:
      governs_anchor: serial
      compare_form: upper-trim
    anchor: { class: hardware, establishing: true }
    merge: { cardinality: single, order: none }
  - term: wg_pubkey
    meaning: "a WireGuard public key: what a peer proves itself with. A credential, not matter — it is copied when a machine is migrated and regenerated on the same one — so it is logical, and the nature decides whether it establishes"
    context_keys: ["wg_pubkey"]
    schema:
      governs_anchor: wg_pubkey
      value_pattern: '^[A-Za-z0-9+/]{43}=$'
      canonical_note: "exact base64, 44 characters"
    anchor: { class: logical }
    merge: { cardinality: single, order: none }
    canonical: "exact base64 (44 chars)"
  - term: openpgp_fingerprint
    meaning: "the fingerprint of an OpenPGP key (RFC 9580; RFC 4880 before it): what a person or an agent SIGNS with. It establishes WHO, in a way no name or address can — and it is what lets a record of who said something be checked rather than believed."
    context_keys: ["openpgp_fingerprint", "identity.anchors[].openpgp_fingerprint"]
    schema:
      governs_anchor: openpgp_fingerprint
      value_pattern: '^[0-9A-F]{40}([0-9A-F]{24})?$'
      canonical_note: "40 upper-case hex digits (a version 4 key) or 64 (version 5 and later), with no spaces"
    anchor: { class: logical, establishing: true }
    merge: { cardinality: set, order: none }
  - term: ssh_key_fingerprint
    meaning: "the SHA-256 fingerprint of an SSH public key, as `ssh-keygen -lf` prints it: what a HOST proves itself with, and what an account is opened by."
    context_keys: ["ssh_key_fingerprint", "identity.anchors[].ssh_key_fingerprint"]
    schema:
      governs_anchor: ssh_key_fingerprint
      value_pattern: '^SHA256:[A-Za-z0-9+/]{43}$'
      canonical_note: "`SHA256:` and 43 base64 characters, unpadded"
    anchor: { class: logical }
    merge: { cardinality: set, order: none }
  - term: emp_id
    meaning: "an employer-assigned unique employee identifier"
    context_keys: ["emp_id"]
    enforced_by: none
    anchor: { class: logical, establishing: true }
    merge: { cardinality: single, order: none }
  - term: product_id
    meaning: "the logical identity of a product: a stable id the product's own home assigns, which identifies it wherever it is written, or a name the garden mints once (`product:<name>`)"
    context_keys: ["product_id"]
    enforced_by: none
    anchor: { class: logical, establishing: true, minted: true }
    merge: { cardinality: single, order: none }
  - term: service_id
    meaning: "the logical identity of a service: a stable id its provider assigns, or a name the garden mints once (`service:<name>`)"
    context_keys: ["service_id"]
    enforced_by: none
    anchor: { class: logical, establishing: true, minted: true }
    merge: { cardinality: single, order: none }
  - term: org_id
    meaning: "the logical identity of an organisation: a registry number or a tax id, written as its registry writes it, or a name the garden mints once (`org:<name>`)"
    context_keys: ["org_id"]
    enforced_by: none
    anchor: { class: logical, establishing: true, minted: true }
    merge: { cardinality: single, order: none }
  - term: person_id
    meaning: "the logical identity of a person as a garden knows them: a name the garden mints once (`person:<name>`). Never a national or government number, which is a secret"
    context_keys: ["person_id"]
    enforced_by: none
    anchor: { class: logical, establishing: true, minted: true }
    merge: { cardinality: single, order: none }
  - term: program_id
    meaning: "the logical identity of a program: its package or executable name in its own ecosystem (`postfix`), or a name the garden mints once (`program:<name>`)"
    context_keys: ["program_id"]
    enforced_by: none
    anchor: { class: logical, establishing: true, minted: true }
    merge: { cardinality: single, order: none }
  - term: contract_id
    meaning: "the logical identity of a contract: the agreement's own reference, as whoever issued it writes it, or a name the garden mints once (`contract:<name>`)"
    context_keys: ["contract_id"]
    enforced_by: none
    anchor: { class: logical, establishing: true, minted: true }
    merge: { cardinality: single, order: none }
  - term: design_id
    meaning: "the logical identity of a design: the id its design tool assigns, or a name the garden mints once (`design:<name>`)"
    context_keys: ["design_id"]
    enforced_by: none
    anchor: { class: logical, establishing: true, minted: true }
    merge: { cardinality: single, order: none }
  - term: doc_id
    meaning: "the logical identity of a document: the id its home assigns (a document store, a wiki, a design tool's file), or a name the garden mints once (`document:<name>`). Whether it ESTABLISHES is the bean's to say: it establishes a document bean and corroborates a design the document is one rendering of"
    context_keys: ["doc_id"]
    enforced_by: none
    anchor: { class: logical, minted: true }
    merge: { cardinality: single, order: none }
  - term: manifest_id
    meaning: "the logical identity a manifest or package descriptor declares for the thing it describes (an add-in id, a bundle id, a module's technical name). Whether it ESTABLISHES is the bean's to say: a module's name is unique within its repository and corroborates beside the git_remote that establishes"
    context_keys: ["manifest_id"]
    enforced_by: none
    anchor: { class: logical }
    merge: { cardinality: single, order: none }
  - term: instance_id
    meaning: "the logical identity of a running instance: for an instance of a program, its deployment coordinate (`<product>@<host>[/<db>]`); for a virtual-host, the id its hypervisor or provider assigns. Neither is a name a garden gives, so either identifies wherever it is written; a name the garden mints is `instance:<name>`. It is the instance's, not the matter's: it lapses at teardown"
    context_keys: ["instance_id"]
    enforced_by: none
    anchor: { class: logical, establishing: true, minted: true }
    merge: { cardinality: single, order: none }
  - term: session_id
    meaning: "the logical identity of a session: the name `bin/dmsession.py` mints when a session opens (`session:<slug>`)"
    context_keys: ["session_id"]
    enforced_by: none
    anchor: { class: logical, establishing: true, minted: true }
    merge: { cardinality: single, order: none }
  - term: email
    meaning: "an e-mail address a person or an organisation is reached at. Logical; whether it ESTABLISHES is the bean's to say, because an address is reassigned and a person outlives it"
    context_keys: ["email"]
    enforced_by: none
    anchor: { class: logical }
    merge: { cardinality: single, order: none }
  - term: garden_id
    meaning: "the identity of a garden: the first twelve hexadecimal digits of the commit it germinated from — the root of its first-parent history. Assigned by no registry and no person; every clone carries the same one, and a copy given a new history is another garden. A garden's own id is read from its git and written in none of its own documents; it is stated where git cannot be read — on another garden's `garden` bean, in a proposal, and before a name the garden minted"
    context_keys: ["garden_id"]
    schema:
      governs_anchor: garden_id
      value_pattern: '^[0-9a-f]{12}$'
      canonical_note: "twelve lowercase hexadecimal digits: the germination commit, abbreviated as a cited commit is"
    anchor: { class: logical, establishing: true }
    merge: { cardinality: single, order: none }
  - term: content_hash
    meaning: "the SHA-256 of a thing's own bytes: one value names one content in every garden that holds it, and a changed byte is a different thing. What identifies a file, a scan, a transcript kept whole"
    context_keys: ["content_hash"]
    schema:
      governs_anchor: content_hash
      value_pattern: '^sha256:[0-9a-f]{64}$'
      canonical_note: "`sha256:` and sixty-four lowercase hexadecimal digits"
    anchor: { class: logical, establishing: true }
    merge: { cardinality: single, order: none }
  - term: event_id
    meaning: "the logical identity of a happening: the UID its invitation carries (RFC 5545) or its id where it is kept, either written as its home writes it, or a name the garden mints once (`event:<name>`)"
    context_keys: ["event_id"]
    enforced_by: none
    anchor: { class: logical, establishing: true, minted: true }
    merge: { cardinality: single, order: none }
  - term: id
    meaning: "a bean/mapping identifier = its filename stem (garden-local; NOT identity)"
    context_keys: ["bean", "mapping"]
    enforced_by: core
    handling: { format: "kebab-case; quote if numeric/reserved; genos-prefixed for high-cardinality gene", unique: "per (space,base)" }
    exceptions:
      - { case: "duplicate legit human names (two hosts both called 'file-server')", decision: "ids disambiguate via genos-prefix+slug; anchor to serial/asset-tag; title may repeat (warn)", why: "labels collide; ids must not", acked: 2026-07-31 }
      - { case: "device replaced, role kept", decision: "role bean (stable) vs device bean (serial-anchored); retired → deprecated + role re-points via replaces:", why: "not silent id reuse", acked: 2026-07-31 }
  - term: ref
    meaning: "the LINK FORM {bean|mapping: <id>[, field: <key>]} — a pointer to the single owner of a value. The relations that USE this form declare themselves (see refs, depends_on, and a garden's own edges)."
    context_keys: []
    enforced_by: core
    handling: { resolve: "target exists in right space; field present in target owns/attributes/details; shallow (ref-to-ref=warn)", graph: "acyclicity is declared PER RELATION via schema.dag — not asserted here for a fixed list of sections (narrowed at 2.0)" }
    exceptions:
      - { case: "'bean' as a plain DATA key", decision: "links only inside refs/consumes/depends_on", why: "reserved word collides with data", acked: 2026-07-31 }
      - { case: "YAML-coerced ref target (bean: no→False)", decision: "non-string target = error; quote the id", why: "coerced targets silently skipped", acked: 2026-07-31 }
  # == THE BEAN-GRAMMAR AND FACT-SECTION KEYS ==
  - term: genos
    meaning: "which genos of being this bean records; a refinement of its nature, from the `gene` registry"
    context_keys: [genos]
    enforced_by: core
    merge: { cardinality: single, order: none }
  - term: kind
    meaning: "which kind of procedure or relationship a MAPPING records — a procedure, a checklist, an automation. A mapping records no being, so it has no genos"
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
    enforced_by: none
    merge: { cardinality: multi, order: by-key }
  - term: details
    meaning: "the abstraction layer: namespaced capsules of detail, and a datum kept intact because it does not yet fit a term (MODEL Ground rule 2) — never dropped, never mis-bucketed, and never crowding `owns` (Rule 6)"
    context_keys: [details]
    enforced_by: none
    merge: { cardinality: multi, order: by-key }
  - term: open
    meaning: "the questions this bean has not answered. An open item is a standing debt, not a defect."
    context_keys: [open]
    enforced_by: none
    merge: { cardinality: set, order: none }
  # == THE MERGE DRIVER'S OWN STATE ==
  - term: merge_open
    meaning: "this bean holds an unresolved merge: both values are kept and a human has not yet chosen. Written by the merge driver, read by the gate, cleared by the person who resolves it. `true`, or absent."
    context_keys: [merge_open]
    enforced_by: core
    merge: { cardinality: single, order: none }
  - term: merge_conflicts
    meaning: "the dotted paths inside this bean that hold a captured disagreement, each written as text. The companion to merge_open: it says WHERE, so a human does not have to search the document for it. A member of a list a term merges member by member is at `<term>.<its key>`, the key its `merge.order` names. The rules stand down on a conflict record only where the merge driver captured it: `merge_open: true`, its path named here, and the record `{conflict: [...]}` with nothing beside `conflict`, holding two values or more that differ. Any other conflict record is refused, named at its path."
    context_keys: [merge_conflicts]
    enforced_by: core
    merge: { cardinality: set, order: none }
  - term: provenance_of
    meaning: "who said each merged value and how they know, keyed by the same dotted path merge_conflicts uses: {path: [{value, src, seen_in, subsumed?}]}. A subsumed value appears here and NOWHERE else, because the document carries only the winner."
    context_keys: [provenance_of]
    enforced_by: none
    merge: { cardinality: single, order: none }
  # == BETWEEN GARDENS ==
  - term: test
    meaning: "present on a `garden` bean when that garden is a rehearsal or a test, saying what it rehearses: the receiving garden's own record of the other, whatever the other's proposals say. What arrives from it is taken as a rehearsal, never as a person's word"
    context_keys: [test]
    schema:
      shape: scalar
      only_on_gene: [garden]
    merge: { cardinality: single, order: none }
  - term: parties
    meaning: "who an agreement binds — an open map, one entry per party, keyed by a short name its clauses and transactions use. A party with `accepted` said yes on that day; one without has no acceptance on record — an offer not yet taken up, or an agreement whose acceptance nobody recorded — and the record says so rather than assuming"
    context_keys: [parties]
    schema:
      shape: open_map_of_entries
      key_form: kebab
      required_on_gene: [contract]
      entry_one_of: [who, external]
      attrs:
        who:      { in: ref, meaning: "the party: a person or an organisation the garden holds, {bean: <id>}" }
        external: { in: prose, meaning: "a party the garden holds no bean for — the bank that issued a card — named as the record can name it" }
        role:     { in: { type: kebab }, meaning: "what the party is to the agreement: payer, cardholder, buyer, lender, facilitator. Open, like `rel`" }
        accepted: { in: { type: date }, meaning: "the day this party accepted. Whose word it is, is the entry's provenance: the party's own word, or another person's report of it — never an inference" }
        during:   { in: extent, meaning: "when this party was a party, where that is not the agreement's whole life" }
        note:     { in: prose, meaning: "optional prose" }
    merge: { cardinality: multi, order: by-key }
  - term: over
    meaning: "what an agreement concerns: the beings it is about, or in words what it is about"
    context_keys: [over]
    schema:
      shape: list_of_entries
      entry_one_of: [thing, what]
      attrs:
        thing: { in: ref, meaning: "a {bean} ref to what it concerns" }
        facet: { in: { registry: facets, take: facet }, meaning: "the facet of it the agreement shares, where it shares one" }
        what:  { in: prose, meaning: "what it concerns, in words: a purchase, a stake, the creation of a codebase" }
    merge: { cardinality: set, order: none }
  - term: words
    meaning: "an agreement's own words: whether they were written, spoken, or not yet put into words; where they are; and the day it was agreed"
    context_keys: [words]
    schema:
      shape: mapping
      required_on_gene: [contract]
      attrs:
        form:   { required: true, in: [written, spoken, unstated], meaning: "written — a text exists, and `at` names the document that holds it | spoken — agreed aloud; `at` may name the happening | unstated — the agreement is named, and its terms have not been put into words" }
        at:     { in: ref, meaning: "the `document` that holds its text, or the `event` at which it was said" }
        agreed: { in: { type: date }, meaning: "the day it was agreed, in any calendar" }
        note:   { in: prose, meaning: "optional prose" }
      cells:
        - { when: { form: written }, requires: [at], why: "a written agreement can be found: name the document that holds it" }
    merge: { cardinality: single, order: none }
  - term: clauses
    meaning: "what an agreement asks of its parties, one clause each: an open map keyed by a short name. A clause is a position on the `capability` aspect — required (must), omissible (need not), permitted (may), forbidden (must not) — the square of obligation a being's capabilities already take. A clause with no `by` is a rule of the agreement that binds every party"
    context_keys: [clauses]
    schema:
      shape: open_map_of_entries
      key_form: kebab
      expiry: { attr: due, repeats: every, unless: { state: [met, waived, broken] }, notice: { of: time, measure: { count: 7, unit: day } }, why: "a clause falls due, and from that day the party it is owed to is owed it" }
      attrs:
        what:   { required: true, in: prose, meaning: "the clause in words, as its parties would say it" }
        by:     { in: { key_of: parties }, meaning: "the party it binds" }
        to:     { in: { key_of: parties }, meaning: "the party it is owed to" }
        stance: { in: { aspect: capability, default: required }, meaning: "required | omissible | permitted | forbidden" }
        amount: { in: { quantity: any }, meaning: "how much, where it is measured — money, time, anything. Absent while unknown, and `what` then says how it will be known" }
        due:    { in: { type: date }, meaning: "the day it falls due — the first day, when it repeats" }
        every:  { in: recurrence, meaning: "how it repeats: each month of a calendar, six times" }
        when:   { in: prose, meaning: "the condition that brings it into force, where that is not a date: 'an instalment paid late'" }
        state:  { in: [in-force, met, waived, broken, disputed], meaning: "in-force — it holds and is not yet discharged; the reading when it is silent | met | waived — released by the party it is owed to | broken | disputed — the parties disagree that it holds" }
        note:   { in: prose, meaning: "optional prose" }
    merge: { cardinality: multi, order: by-key }
  - term: transactions
    meaning: "what has moved between an agreement's parties, or out of it on their behalf: each an amount, who paid how much of it, and who bears it in what shares. What one party owes another is READ from these and from the clauses (bin/dmledger.py), never written: a stored balance is a second copy, and it drifts. Every figure is exact — a whole number or a decimal string — and every sum, share and balance is computed in fractions"
    context_keys: [transactions]
    schema:
      shape: open_map_of_entries
      key_form: kebab
      sums: { whole: [charged, amount], parts: paid_by.amount }
      attrs:
        what:     { required: true, in: prose, meaning: "what was bought, paid, repaid or charged, in the person's own words" }
        amount:   { required: true, in: { quantity: money }, meaning: "the whole, in the currency it was priced in" }
        charged:  { in: { quantity: money }, meaning: "what it came to in the currency it was paid in, where that is another currency — both as the statement shows them. The rate between them is READ (charged ÷ amount, exactly), never stored" }
        day:      { in: { type: date }, meaning: "the day it happened, where known" }
        paid_by:
          required: true
          meaning: "who paid, and how much each paid — one entry per party. A single payer may leave `amount` out: they paid the whole"
          in: { entries: { party: { required: true, in: { key_of: parties } }, amount: { in: { quantity: money } } }, keyed_by: party }
        borne_by:
          meaning: "who bears it, one entry per party, in whole-number shares: two to one is 2 and 1. Absent: whoever paid bears it"
          in: { entries: { party: { required: true, in: { key_of: parties } }, share: { required: true, in: { pattern: '^[1-9][0-9]{0,39}$' } } }, keyed_by: party }
        under:    { in: { key_of: clauses }, meaning: "the clause it was made under, or keeps" }
        through:  { in: ref, meaning: "the card, account or agreement it moved through — itself an agreement with whoever issued it" }
        category: { in: prose, meaning: "the person's own word for what kind of spending it was" }
        note:     { in: prose, meaning: "optional prose" }
    merge: { cardinality: multi, order: by-key }
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
    schema:
      on_sequence: routine
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
  # == POSITION TERMS ==
  - term: located_at
    meaning: >
      Where this being is found: a list of positions, each in a named anchor system, each stating how far
      it is known to reach. A being may be located in several systems at once, and a location that is not
      known is STATED as unknown rather than left out.
    context_keys: [located_at]
    schema:
      shape: list_of_entries
      required_on_gene: [document]
      attrs:
        system:    { required: true, in: { registry: anchor_systems, take: system }, meaning: "which anchor system this position is stated in — it selects the form the position must take" }
        openness:  { required: true, in: [here, elsewhere, unreachable, unknown], meaning: "here (reachable from the machine that recorded it) | elsewhere (reachable, and NOT from here) | unreachable (known, and cannot be reached) | unknown (nobody has established where it is)" }
        observed:  { in: { type: date }, meaning: "ABSOLUTE date this location was checked. A location ages: a tree is moved, a branch is checked out elsewhere, a printout is filed." }
        at:        { in: { form_of: anchor_systems, keyed_by: system, take: pattern }, meaning: "the position itself, in that system's ONE canonical form. Required unless openness is `unknown`, which is precisely the case where there is no position to state." }
        note:      { in: prose, meaning: "optional prose — the only place a `physical` address can live, since that system declares no canonical form" }
      cells:
        - { when: { openness: here }, requires: [at] }
        - { when: { openness: elsewhere }, requires: [at] }
        - { when: { openness: unreachable }, requires: [at] }
    merge: { cardinality: multi, order: "by-system+at?" }
  - term: timing
    meaning: >
      When something happened, as an OPEN map of moment-name -> a position in a time anchor system at a
      STATED resolution. The resolution is declared, never inferred from how many digits were typed, so
      two positions whose resolutions overlap can be known to be unordered rather than silently ordered.
    context_keys: [timing]
    schema:
      shape: open_map_of_entries
      key_form: kebab
      required_on_gene: [session, event]
      attrs:
        system:  { required: true, in: { registry: anchor_systems, take: system }, meaning: "the time anchor system — gregorian-civil for a calendar reading, event-anchored for a position fixed only by its neighbours" }
        at:      { required: true, in: { form_of: anchor_systems, keyed_by: system, take: pattern }, meaning: "the position, in that system's ONE canonical form" }
        unit:    { required: true, in: { registry: units, take: unit }, meaning: "the resolution ACTUALLY HELD. `2026-08-07T05:21` recorded at unit: minute means the second is not known — not that it was zero." }
        by:      { in: prose, meaning: "optional: who or what read the clock, when that is not the bean's default provenance" }
        note:    { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" }
    key_note: >
      kebab-case moment names. Used so far: start | sync | stop. The key is DELIBERATELY OPEN and the gate
      is forbidden from enumerating it — a run with four sync points, or a moment nobody has named yet,
      must never require a rule-change.
    merge: { cardinality: multi, order: by-key }
  - term: roots
    meaning: >
      This host's resolution of logical roots: the map that turns a portable `root:<name>` position into a
      literal position on THIS machine. Absence is not an error — a host that does not resolve a root
      simply does not hold that thing, and a reader is told so rather than shown a path that is not there.
    context_keys: [roots]
    schema:
      shape: open_map_of_entries
      key_form: kebab
      entry_must_match:
        - { attr: system, registry: operating_systems, keyed_by: os, take: path_grammar }
      attrs:
        system:    { required: true, in: { registry: anchor_systems, take: system }, meaning: "which filesystem system this host resolves the root in — pinned since 7.0 to the grammar this host's `os` declares, so it is checked rather than merely stated" }
        at:        { required: true, in: { form_of: anchor_systems, keyed_by: system, take: pattern }, meaning: "the literal position this root means HERE, host named, in that system's canonical form" }
        observed:  { in: { type: date }, meaning: "ABSOLUTE date the resolution was checked — a tree gets moved" }
        note:      { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" }
    key_note: >
      kebab-case root names, shared across hosts by AGREEMENT rather than by a registry: a root is a name
      two machines both choose to use, and centralising the list would re-introduce the one shared document
      this term exists to avoid.
    merge: { cardinality: multi, order: by-key }
  - term: roles
    meaning: "the jobs this being does, each a row of the `roles` registry"
    context_keys: [roles]
    schema:
      shape: list_of_entries
      attrs:
        role:      { required: true, in: { registry: roles, take: role }, meaning: "which job — a registry row, so a typo is an error and not a new role" }
        observed:  { in: { type: date }, meaning: "ABSOLUTE date the role was confirmed to be one this being actually performs" }
        why:       { in: prose, meaning: "optional: what this being does in that role that another in the same role would not" }
    merge: { cardinality: multi, order: by-role }
  - term: os
    meaning: "the operating system this machine runs — a row of the `operating_systems` registry"
    context_keys: [os]
    schema:
      shape: scalar
      values_from: "registry:operating_systems[].os"
    version_note: >
      The RELEASE (15.0, 9.7) is deliberately NOT part of this value. A version moves on every upgrade
      while the OS does not, and putting both in one scalar would make the enum unclosable — a new point
      release would be a rule-change. The release belongs in `owns.os_release`, beside the date it was read.
    merge: { cardinality: single, order: none }
  - term: volumes
    meaning: >
      The storage this machine holds, as a layered stack: each entry a formatted volume, naming what
      carries it. Recorded so a machine can be REBUILT from its bean rather than from memory of it.
    context_keys: [volumes]
    schema:
      shape: open_map_of_entries
      key_form: kebab
      attrs:
        format:      { required: true, in: { registry: storage_formats, take: format }, meaning: "a row of storage_formats — ext4, crypto_LUKS, LVM2_member and so on" }
        observed:    { in: { type: date }, meaning: "ABSOLUTE date the layout was read off the machine" }
        carried_by:  { in: { key_of: volumes }, meaning: "the `volumes` key beneath this one. A local key and NOT a ref: the stack is intra-bean, which is why it joins no acyclic check." }
        uuid:        { in: { pattern: "^[0-9A-Za-z][0-9A-Za-z:-]*$" }, meaning: "the volume's own identifier, as its format reports it. The datum a rebuild needs and the one that survives a device rename." }
        at:          { in: { pattern: "^(/[^ ]*|[A-Za-z]:[/\\\\].*)$" }, meaning: "where it is mounted, in this machine's path grammar. Absent for a volume that holds no filesystem — a LUKS container or an LVM member is mounted nowhere." }
    reproduction_note: >
      The LAYOUT only — what exists, what carries what, and where it is mounted: what a rebuild needs to
      recreate the shape. Never contents, keys or passphrases. Configuration is not layout: it is somebody
      else's authoritative truth, referenced and never mirrored.
    merge: { cardinality: multi, order: by-key }

  - term: beanger
    meaning: >
      A per-datum ledger: what a datum IS, which field on this bean holds its CURRENT value, how to read
      it, and the append-only log of every operation on it — each stamped to the millisecond, attributed,
      and linked to the one before.
    context_keys: [beanger]
    schema:
      shape: open_map_of_entries
      key_form: kebab
      attrs:
        defines:  { required: true, in: prose, meaning: "WHAT this datum is, structurally — the part that stays true across every value it will ever hold. Written so a reader who has never seen the machine can tell which reading would refresh it." }
        tracks:   { required: true, in: { pointer: bean_field_pointer }, meaning: "a pointer to the field holding the CURRENT value — `<section>.<key>` on this bean. The value is NOT copied here: it lives in one place and this names it." }
        source:   { required: true, in: prose, meaning: "the exact command or file the value is read from, so the next scan reads THE SAME THING. Without it a differing value cannot be told from a differing METHOD — the failure this estate met when /sys/class/net reported a bond's MAC where ethtool -P reported the NIC's." }
        records:
          required: true
          meaning: "the append-only log, OLDEST FIRST. Each record is an entry, and is held to these attributes like any other."
          in:
            entries:
              seq: { required: true, in: { pattern: "^[1-9][0-9]*$" }, meaning: "1-based position in this datum's log. The identity `prev` points at." }
              at: { required: true, in: { system: unix-epoch }, meaning: "the moment of the RECORD, epoch MILLISECONDS (see the `unix-epoch` anchor system). Milliseconds because two operations in one session can land in the same second and their order is the thing being recorded." }
              unit: { in: { registry: units, take: unit }, meaning: "the resolution the moment was ACTUALLY held to — a row of `units`. Defaults to millisecond for anything this ledger stamped itself. A record reconstructed from a date carries `unit: day` and an `at` of that day's midnight, so that thirteen digits of apparent precision cannot be mistaken for thirteen digits of knowledge. This is the same rule `timing` already applies, and it exists because this estate has twice written a value that looked measured and was inferred." }
              op: { required: true, in: [add, change, remove, confirm], meaning: "add | change | remove | confirm. `confirm` is the only one that does not move the value." }
              value: { in: any, meaning: "the value AS OF this record. Present on add and change; on `confirm` it is omitted, because repeating an unchanged value is the duplication this design removed. On `remove` it is omitted for the same reason — the outgoing value is already on the record before." }
              prev: { in: { pattern: "^([1-9][0-9]*|None)$" }, meaning: "the `seq` of the record before, or null on the first. The BACK link only: forward is list order, and storing both would let them disagree." }
              who: { required: true, in: { pattern: "^((agent|tool|human):[^ ].*|[^ :][^:]* \\(.+\\))$", soft: true, why: "attribution has one convention across the ledger" }, meaning: "who performed it, in `provenance.by` form — `sam (operator)` for a person, `agent:<model>/<garden>` for an agent. One convention for attribution across the ledger, not a second." }
              from_where:
                meaning: "the CURSOR the operation was performed FROM: `{host, session, guide}` — which machine, which working session, and which context the operator had in attention. All three are bean refs where a bean exists."
                in:
                  entries:
                    host: { in: bean_id, meaning: "which machine" }
                    session: { in: bean_id, meaning: "which working session" }
                    guide: { in: bean_id, meaning: "which context the operator had in attention" }
              to_where: { in: ref, meaning: "what the operation was performed ON, as a bean ref, where that differs from the bean carrying the beanger. Absent for a plain local read." }
              why: { in: prose, meaning: "optional: what caused the change. Load-bearing on `change` and `remove`, where the value alone does not say what happened." }
    merge: { cardinality: multi, order: by-key }

  - term: workspace
    meaning: "the working copy and branch a session commits from, on a named host"
    context_keys: [workspace]
    schema:
      shape: mapping
      required_on_gene: [session]
      attrs:
        host:       { required: true, in: ref, meaning: "a {bean} ref to the machine the session ran on. A session is not portable: its shell history, its reachability and what it could measure all belong to one machine." }
        at:         { required: true, in: { pattern: "^(root:[a-z0-9][a-z0-9-]*(/[^:]*)?|[a-z0-9][a-z0-9.-]*:([/A-Za-z]).*)$" }, meaning: "the working copy, as a position in that host's path grammar — `root:` form where a root exists, so it resolves on a second machine rather than reading as a literal path that is not there." }
        branch:     { required: true, in: { pattern: "^[A-Za-z0-9][A-Za-z0-9._/-]*$" }, meaning: "the git branch it commits to. `session/<slug>` by convention; `master` for a session that worked the main copy directly, which is what every session before 2026-08-07 did." }
        opened_at:  { in: { system: unix-epoch }, meaning: "epoch milliseconds, stamped by bin/dmsession.py. A session's own start is the one moment nobody should be estimating." }
    merge: { cardinality: single, order: none }

  - term: capture
    meaning: >
      A dated, staleness-keyed copy of truth somebody else owns, taken so the thing can be REBUILT. Never
      authoritative, never applied back unread, never carrying a secret.
    context_keys: [capture]
    schema:
      shape: open_map_of_entries
      key_form: kebab
      attrs:
        of:             { required: true, in: prose, meaning: "WHAT was copied — the config, the layout, the ruleset — in enough detail that a reader knows what they are holding." }
        owned_by_them:  { required: true, in: prose, meaning: "WHO owns the original and therefore the truth. A capture that does not name its owner reads as an authoritative fact, which is the failure ground rule 3 exists to prevent." }
        source:         { required: true, in: prose, meaning: "the EXACT command that produced it, so it can be produced again and compared. The same argument `beanger.source` makes, and it earned it there within the hour: naming the command is what gets it run." }
        taken_at:       { required: true, in: { system: unix-epoch }, meaning: "epoch milliseconds — a capture with no moment cannot be told from a guess." }
        staleness_key:  { required: true, in: prose, meaning: "how a reader decides whether this still holds: a config version, a change counter, a hash of the live export. The same job `analysis_cache.staleness_key` does for code, which is where this shape comes from rather than being invented beside it." }
        redactions:     { required: true, in: prose, meaning: "WHAT WAS REMOVED and why. REQUIRED. Write `none — the source emits no secrets` explicitly if that is true; the point is that it is a claim, not a default." }
        holds:          { required: true, in: prose, meaning: "the content itself for something small, or a `file:` pointer into this garden for something large. Large captures do not belong inline: a bean must stay legible on paper, and a 900-line router export is not." }
        restores:       { in: prose, meaning: "optional: what this capture would let somebody rebuild, and what it would NOT. The honest half is usually the second." }
        supersedes:     { in: { key_of: capture }, meaning: "optional: the `capture` key on this bean that this one replaces" }
        note:           { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" }
    merge: { cardinality: multi, order: by-key }

  - term: risks
    meaning: >
      The named ways this being can fail: what the defect is, what it costs, whether it is happening now,
      and how that was established. One inventory, on the bean that owns the failing thing.
    context_keys: [risks]
    schema:
      shape: open_map_of_entries
      key_form: kebab
      attrs:
        what:         { required: true, in: prose, meaning: "the defect, plainly." }
        consequence:  { required: true, in: prose, meaning: "WHAT IT COSTS IF IT BITES. The load-bearing attr, and the one a prose register loses first — severity is an opinion about this, so recording severity without it records the opinion and drops the argument." }
        severity:     { required: true, in: [high, medium, low], meaning: "high | medium | low. An opinion, and it should follow from `consequence` rather than lead it." }
        state:        { required: true, in: [live, latent, unproven, resolved, superseded], meaning: "live (the defect IS the case right now) | latent (it is not, and nothing prevents it — the `forbidden` + `possible` shape) | unproven (nobody has established which, and that is the finding) | resolved | superseded (a different change made it moot; say which).\n" }
        evidence:     { required: true, in: prose, meaning: "how the state was established, specific enough to re-run. `unproven` states what WOULD establish it — a risk whose test is unnamed cannot be closed by anyone but its author." }
        owned_with:   { in: ref, meaning: "optional {bean} ref: where the FIX lives, when that is not this bean. A defect on one being is often only fixable on another." }
        found:        { in: { type: date }, meaning: "ABSOLUTE date the finding was first made." }
        resolution:   { in: prose, meaning: "on `resolved` / `superseded`: WHAT settled it. A closed risk that does not say how is a risk a reader must re-open to trust." }
        resolved:     { in: { type: date }, meaning: "ABSOLUTE date it was settled." }
        note:         { in: prose, meaning: "optional: history, partial resolutions, and what a reader would otherwise re-derive." }
    capability_note: >
      A `capabilities` entry at `forbidden` + `possible` IS a latent risk, and the two are deliberately
      NOT merged: a capability records the STANCE a being takes, a risk records a FAILURE MODE, and the
      same prohibition can hold on beings with no risk attached. Where one produces the other, the risk
      entry says so in `evidence` and cites the capability by name. The alternative — deriving risks from
      capabilities in the gate — was rejected because a derived finding cannot carry a `consequence` that
      anybody wrote, and the consequence is the part worth having.
    merge: { cardinality: multi, order: by-key }

gene:
  - genos: codebase
    of_nature: lekton
    meaning: "a source-code tree managed as one object (a repo / Odoo addon / plugin project)."
  - genos: product
    of_nature: lekton
    meaning: "an umbrella bean tying a product's codebases + business context together; not itself code. A THIRD-PARTY product is recorded here for one reason only: so its per-host deployments have a TYPE to be instances of. That rationale belongs to this genos and is stated once — a product bean should describe the product, not re-explain why it exists. A product is a LOGICAL code unit — its mapping to storage (git repos) is many-to-many (sub-git or multi-git); git_remote is a source anchor, NOT product identity."
  # == being-gene for the ownership / type-token / habitat model ==
  - genos: org
    of_nature: lekton
    meaning: "an organization / juridical person (company) that owns beings."
  - genos: person
    of_nature: empsychon
    ownership_form: crown
    meaning: "a human being who can own/steward other beings."
  - genos: instance
    of_nature: empsychon
    meaning: "a running token — a deployment of a code product in a habitat, carrying the runtime facts. Distinct being from its code product; `instance_of` and `lives_in` are required on it."
  - genos: host
    of_nature: soma
    meaning: >
      A MACHINE THE ESTATE RUNS ON — matter of its own: bare metal, general-purpose or appliance. A virtual
      machine is a `virtual-host`; a router is a host in the `router` role. What a genos answers is the one
      question: this being is a machine.
  - genos: virtual-host
    of_nature: empsychon
    meaning: >
      A VIRTUAL MACHINE — a running machine-instance on a hypervisor, rented from a provider or run on a host of
      the estate's own. It has no matter: what identifies it is the provider's instance id or its name, never a
      serial, and it lapses at teardown. That is the nature empsychon, as `instance`'s is. TENANCY is not what it is:
      a rented VM is owned `external` (the provider) and answered for here; a VM on the estate's own hypervisor
      is owned through it. Its habitat, where that is a bean, is `lives_in`.
  - genos: domain
    of_nature: lekton
    meaning: "a DNS domain — a name held by agreement with a registry, not a thing in space."
  - genos: service
    of_nature: lekton
    meaning: "a named capability the estate provides or consumes (mail pipeline, monitoring), above any one host."
  - genos: program
    of_nature: lekton
    meaning: "a bounded body of work with an aim (a hardening programme), tracked as one object."
  - genos: design
    of_nature: lekton
    meaning: "a durable design/decision document — the recorded reasoning behind a change."
  - genos: session
    of_nature: lekton
    meaning: "a bounded stretch of work with a start, any number of sync points, and a stop. Declared because sessions already exist in practice — handed off in prose, their times nowhere in data — and because they are what makes `timing` earn a resolution: a session is the one object whose position must be held finer than a day."
  - genos: contract
    of_nature: lekton
    ownership_form: [crown]
    responsibility_form: [parties]
    meaning: "an agreement between parties: who it binds (`parties`), its words (`words`), what it asks (`clauses`) and what has moved under it (`transactions`). An agreement between parties may be owned by none of them — it ends at the crown — and then its parties answer for it; one a person authored may be owned by its author. Co-owning one facet of one being is one use of it."
  - genos: garden
    of_nature: lekton
    meaning: "ANOTHER daftar garden this one deals with: a git repository of beans kept by its gardener, identified by `garden_id`, owned by its gardener and answered for by them. A garden's own identity is read from its git and its gardener is named in its GARDEN.md — never in a bean of its own."
  - genos: document
    of_nature: lekton
    meaning: "words or figures fixed in a form that can be kept and handed on: a statement, a letter, a scanned sheet, a conversation kept as a transcript. Identified by its home's reference (`doc_id`) or by its content (`content_hash`); where its copies are is `located_at`. What must not be kept whole — a card number — stays out of it, and a redacted copy of its lines is a `capture` on it."
  - genos: event
    of_nature: lekton
    ownership_form: [crown]
    meaning: "a happening between people at a time: a meeting, a dinner, a party, a conversation in which something was agreed. When is `timing`; who took part is `refs`, each naming what they were in `rel` — present, invited, host, paid, or any other part a person played. A happening between people is owned by none of them — it may end at the crown — and whoever hosted it answers for it."
---
# daftar — Tier-0 Universal Standard Vocabulary

The portable, estate-agnostic classification shared by every garden — the abstract model of *types* (data + process) and *anchors* (identity classes). Gardens pin a version in their own `VOCAB.md` / `GARDEN.md` and add only local terms/exceptions there.

**Anchor classes.** An anchor establishes identity if and only if it carries `establishing: true`. Which classes may establish for a bean is stated once, in the front matter: the classes are the `anchor_class` term's values, each nature's family is its row in `natures`, and `identity_policy.establishing_family` says the gate holds a confirmed bean to it. This prose restates none of them. See `MODEL.md`.

**Growth:** a garden-local term that proves general is **promoted** here by a pull request to the daftar repository (`CONTRIBUTING.md`): propose, show the neighbourhood, a person ratifies, and the version moves. This file's version history is its changelog below.

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

- **11.3** (2026-09-20, proposed rule-change) — **the rank the merge kept to itself, and a schema language that
  describes itself.** `provenance_src` declares `merge.order: "generated-by-tool<inferred<observed<asserted-by-human"`.
  MODEL.md and MERGE.md have always stated the guard; the order that implements it was a constant in
  `bin/dmmerge.py`, which now reads the declaration the way it reads `anchor_authority`'s and refuses to merge
  without one. No merge outcome changes: the declared order is the one the constant held. And `schema_language`
  declares four constructs the gate has interpreted for months and the language never mentioned — `path`,
  `alt_form`, `attr_types`, `canonical_note`; the gate now WARNS when a term's `schema:` uses a key the language
  does not declare, because an unknown construct is a rule that silently enforces nothing (a typo in
  `entry_required_attrs` has always passed). A warning and not an error, so this stays MINOR: no bean and no
  vocabulary that passed before is refused.

- **12.0** (2026-09-20, proposed rule-change) — **structure before prose, and a rank that says why.** MAJOR, for
  two reasons. (1) AN ENTRY HOLDS ONLY THE ATTRIBUTES ITS TERM DECLARES. Top-level keys have been closed since
  2026-09-17; one level down, one garden of 143 documents held forty attributes no term knew — sentences promoted
  to field names (`what_this_does_NOT_establish:`) so that prose would look like data. They are refused now, and
  prose goes in the attribute a term declares for it: `note` is declared on `code_paths`, `registration`, `refs`,
  `owned_by`, `responsibility`, `timing`, `roots` and `capture`. Declared because beans legitimately carried them:
  `capabilities.feasibility_why`, `risks.resolution` / `resolved`, `capture.supersedes`, `refs.path`,
  `git_host.repo`, `since` on the two ownership arcs. `provenance` is allowed on ANY entry, because MODEL.md has
  always said a fact may carry its own. A term that declares no attribute (`owns`, `details`, `attributes`) stays a
  free container, by declaration. (2) A SCHEMA KEY THE LANGUAGE DOES NOT DECLARE IS AN ERROR (a warning at 11.3).
  Also: `provenance_src` states what each src MEANS and why it ranks where it does, and `generated-by-tool`
  BORROWS its standing — it ranks as the weakest src in its `provenance.from`, and at the bottom only when it
  names none; the label is never rewritten. And a fourth vacancy reason, `universal`, for a position declared
  because the mechanism is general rather than because this garden expects an occupant.

- **13.0** (2026-09-20, proposed rule-change) — **the law keyed by attribute.** MAJOR: the SPELLING of a term's
  schema changes, and the old spelling is refused. Until now one attribute's law was scattered across as many
  constructs as it had properties — `entry_required_attrs`, `entry_values`, `entry_types`, `entry_in_registry`,
  `on_aspect`, `pointer_fields`… each a map keyed by attribute — and stated a second time, for people, in the
  term's `entry_attrs:`; the two copies are on record as having drifted twice. Now it is stated once:
  `schema.attrs.<name>: { required, in, meaning }`. EVERY ATTRIBUTE IS A POSITION IN EXACTLY ONE DOMAIN —
  measured over every term before the spelling was chosen: none carried two — so `in:` is one thing
  (`schema_language.attr_domains`): a closed list, a registry, an aspect, a value type, the form a sibling's
  system declares, a pattern, `extent`, `ref`, a pointer, `id`; or `prose`, which is deliberately not a position;
  or `untyped`, which owns up to a domain nobody has declared yet. An attribute that states no domain is refused.
  `cross_aspect`, `entry_required_if` and `entry_expect_if` were three constructs for one idea and are `cells`.
  The marker `self` inside the ref lists is `is_ref: true`. EIGHTEEN constructs and two doc maps are retired; a
  garden's overlay now merges `attrs` per attribute, so it can add one attribute to a standard term without
  restating the rest. NO VERDICT MOVES: proved over a real garden with the old law under the old gate against
  the translated law under the new one, every mutation applied to both, a mutated law compared with its own
  translation — identical output in every case. What changes is wording: a refusal names
  `schema.attrs.<name>` where it named a retired construct. A GARDEN DOES NOT REWRITE ITS OWN TERMS BY HAND:
  `bin/dmreform.py` translates them, keeps every comment, proves per term that the form read is unchanged, and
  leaves the file alone when it cannot; `bin/dmupgrade.py` runs it inside its rollback. The standard's own text
  was translated by the same tool, then its comments put back beside what they explain by hand. One comment was
  deleted, because it had become false: "human documentation; the GATE reads schema: above".

- **14.0** (2026-09-20, proposed rule-change) — **addresses and ports are places.** MAJOR: the `address_systems`
  registry and the `address_system` term are gone, so a garden that added a row there must move it. 6.0 gave ipv4
  and ipv6 their own registry and `dimension: address` because where a being IS and where it ANSWERS are two
  questions. They are — but that is a difference of RELATION, which this law carries as terms (`located_at`,
  `endpoints`), as `observed` / `expires` / `created` are relations to one dimension of time. And `address` was a
  dimension NO ASPECT HELD: the two systems belonged to no figure, while `leaf_orders.cidr` had already described
  them as a containment order, which is `place`'s. They join `anchor_systems` as place systems. A PORT is a
  position nested in an address the way a path is nested in a host; it had no system because the transport layer
  had no row. `tcp` and `udp` are `net_protocols` rows now (`layer: transport`), `tcp-port` and `udp-port` are
  place systems, and `endpoints.port` — `untyped` until now — is a position in the port space its transport
  names: `port: "110/143/993/995"`, the defect the term was written to end, is refused at last, and so is 70000.
  `endpoints.system` may be ANY place system, so a unix socket path is an endpoint like any other. An entry may
  state `transport` when it differs from its protocol's usual one. TWO GENERIC ADDITIONS, neither naming a term:
  `where:` narrows a registry domain to the rows that say so, and `default_from:` reads an attribute's value off a
  registry row when the entry is silent — never written back, never an occupant. NOT in this release, on purpose:
  a system row stating its OWN restrictions (a port line is one totally ordered counted line; geographic is
  metered) so that extents and recurrences can ask the system what it permits. That arrives with its consumer.

- **15.0** (2026-09-20, proposed rule-change) — **a system knows its own shape; the network stack completed and rooted
  in the fields of knowledge.** MAJOR for ONE reason: a verdict cell now sees EVERY attribute of an entry (it saw only
  aspect positions), and `endpoints`' cleartext-and-required cell names `exposure: [lan, link, internet]` — so the
  loopback over-fire it had carried since 6.0, and explained at length in its own `why`, ends. Everything else is
  additive. A SYSTEM ROW MAY STATE ITS SHAPE: `levels` (the resolutions a position may be held to — a named list or a
  counted range; a level is metric when it names a unit, and a month never does), `within`, `resolves_through`,
  `neighbours`, and its own `restrictions`, which narrow its aspect's and never widen them. It is the "subaspect" of
  the 2026-08-05 time conversation and the thing `place` has always said it lacked. Every existing system states it;
  the trees of knowledge already had. `units` gains `hour` and the first LENGTH, `metre`. Three canonical systems for
  a garden that keeps a map: `iso-3166`, `osm`, `postal-code`. `planes` (data / control / management) is a registry
  and an attribute of endpoints, links and treatments, with one new cell: a MANAGEMENT surface answering on the
  INTERNET. `net_protocols` gains the network layer, the rest of the link layer, and the control plane — OSPF, IS-IS,
  RIP, EIGRP, BGP, each with its `family` and `scope` — and EVERY protocol row names its entry in the catalogue of
  technologies (`registry_links`, resolved by the gate), which gains 29 rows and is declared `within` the UNESCO
  fields: a routing mechanism ledgered tomorrow hangs from the same tree of knowledge as a mail server does today.
  NOT built: places-in-the-network as a registry of site roles (no garden yet has site beans); extents and
  recurrences that ASK a system its shape (next).

- **16.0** (2026-09-20, proposed rule-change) — **a calendar is not time, and a coordinate is never bare.** MAJOR for
  three reasons: the `geographic` system's form changes from a bare `<lat>,<lon>` to
  `<authority>:<code>;<coordinates>[@<epoch>]`; `osm`, declared establishing one release ago, no longer establishes;
  and the law's patterns are matched ASCII-ONLY, so a position written in another script's digits — which the gate
  accepted as a date until now, because `\d` matches every script — is refused. CALENDARS: all eighteen that Unicode
  CLDR identifies, and the Julian, are time systems, each with its own `levels` (a month is a level of ITS calendar
  and never metric; the Hebrew and Chinese year has twelve months or thirteen; the Japanese calendar has an `era`
  level), its `reckoning` (arithmetic / astronomical / observational / tabulated), when its `day_begins` (the Hebrew
  and the Hijri day at sunset), and a TAGGED form, because `1405-06-29` is also a Gregorian date. They all partition
  one line of days (`same_ground_as`, `crosswalk`), so they meet at the DAY: `bin/dmcal.py` converts through it for the
  fourteen reckoned by rule and REFUSES the five that are not. NO CALENDAR IS PRIVILEGED: a moment is stated in the
  calendar it was known in. Every dated attribute of the standard is typed `date` — a day in ANY calendar — and `bin/dmstale.py`
  ages one through the day. (Still Gregorian-only, named: `leaf_orders.instant` and the journal's heading form.) COORDINATES, after ISO 19111 / 19112: `bodies` (a
  latitude is a latitude ON something — the Earth, the Moon, Mars), `reference_systems` with their `kind` and whether
  the `frame` is static or DYNAMIC (ground drifts in a dynamic frame, so a coordinate there needs its epoch), and
  `geographic` as THE ROOT OF PLACE: every way of saying where by IDENTIFIER — an administrative code, a postal code,
  a street address, a grid cell, a map database's element id, a `local-frame` position such as "third floor" that
  travels with its building — `resolves_through` it and none of them is one. `bin/dmgeo.py` reads a position, names
  its grid cells and measures on the body the system names; it does NOT transform between datums, which needs
  published parameters. Generic additions to a system's shape: `same_ground_as`, `crosswalk`, `example` (held to the
  system's own pattern by the gate); the words a shape may use are declared in `system_shape`, so the gate carries
  no copy.

- **16.1** (2026-09-20, proposed rule-change) — **the law and its reasons, kept apart and related by key.** MINOR: no
  rule moves. Every comment left this file's front matter — eight hundred lines of argument, incident and history that
  had grown beside the rules — for `seed/RATIONALE.md`, VERBATIM, each under the PATH of the law item it explains
  (`anchor_systems[geographic].restrictions`). The law now says what is in force, and carries as DATA — `meaning:`,
  `why:` — the reason a reader needs in order to apply it; the rationale says why it is that way; the changelog and a
  garden's journal say what happened. `bin/dmwhy.py <name>` reads law and rationale together, and `--check` refuses a
  reason whose law item is gone, so a reason cannot outlive its rule unnoticed. `test/rationale.py` holds the
  separation: no commentary in the law, section titles that are only titles, no orphaned reason, and a RATCHET on the
  narrative that still sits inside the law's data strings (14 lines; it may only fall). Additive in the same release,
  from a look at what GNU publishes: the day itself as a system (`julian-day`, the astronomers' count, whose day
  begins at NOON) and the Mayan long count, both reckoned by `bin/dmcal.py`; the Badi and the French Republican
  calendars, declared astronomical and therefore not converted; `guix-store`, a second place system in which a
  position says what it holds; and `openpgp_fingerprint` and `ssh_key_fingerprint` as establishing identity anchors.

- **16.2** (2026-09-20, proposed rule-change) — **recurrence.** MINOR, additive. `in: recurrence` and `recurrence_form`:
  a repetition is a sequence whose neighbours are given by a rule. It strides by NEIGHBOURS (`every: { count }` — every
  tenth release), by MEASURE (`every: { count, unit }` — every five minutes, every five metres) or by CELL (`each:
  <level>` of a named system — the 15th of each Persian month). Which stride a repetition may use is read from the
  aspect's figure and from the SHAPE the named system declares — neighbours, metering, levels — so a new system gets
  repetitions with no change to the gate. `each` requires `in:`, because a level belongs to its system. An extent may
  name a system too, and then carries a measure where the system is metered and its aspect is not.

- **22.0** (2026-09-24, human-ratified rule-change) — **the law says what a being is in one tongue: its Greek.**
  MAJOR: every bean changes. The words for what a being is came from four traditions, and one misused its own — in
  Aristotle, metaphysics studies every being, not the ones that are not physical. RENAMED: the crown's root `god` ->
  `theos` and its branches `nature` -> `physis`, `logos` kept, `love` -> `agape`; the natures `physical` -> `soma`,
  `metaphysical` -> `lekton`, `living` -> `empsychon`, their meanings said in the Greek words and unchanged in
  substance; a bean's `kind:` -> `genos:`, the registry `kinds` -> `gene`, each row `- genos: <name>`, and a garden's
  `local_kinds` -> `local_gene`; the schema constructs `required_on_kinds` -> `required_on_gene`, `only_on_kinds` ->
  `only_on_gene`, `must_equal_kind_attr` -> `must_equal_genos_attr`, `entry_form_from_kind_attr` ->
  `entry_form_from_genos_attr`, and `bean_id`'s `kinds` -> `gene`; `identity_policy.minted.form_kind: kinds` ->
  `form_genos: gene` — a minted name is still written `<genos>:<name>`, and no value a garden minted changes. KEPT:
  the bean attribute `nature`, the registry `natures` and a genos's `of_nature`; and a mapping's `kind`, which names no
  being — a `kind` term says so, beside the new `genos` term. `retired` names every old word with the one that took its
  place, so a refusal says where it went. GATE CHANGES: a key retired on a bean is refused on a bean even where another
  document still declares it (`kind`, a mapping's); a nature, a crown branch or a genos's `of_nature` in a retired word
  is refused naming its Greek one; a garden's VOCAB.md still carrying `local_kinds`, a `kinds` registry restated or
  added to, or `form_kind`, is refused naming where it went, never left unread; `in: { bean_id: … }` takes `gene` and
  nothing else; `required_on_<registry>` and `only_on_<registry>` read their axis from the field the registry's rows
  are named by, since γένη is not γένος with an `s`. With the release: `bin/dmupgrade.py` translates a garden crossing
  into 22.0 — in every bean its `kind`, its `nature` and the crown branch its ownership ends in; in VOCAB.md
  `local_kinds`, a restated or added `kinds` and their rows, the schema keys and `bean_id` of its own terms, a
  registry or a nature they name, and a vacancy at a renamed position; in the garden's own RATIONALE.md, a heading
  keyed by a path VOCAB.md renamed — each found by the YAML node that holds it, comments and prose untouched, each
  document proved to parse to exactly the old one renamed, and all of it reported on the journal entry's
  `translated:` line; a mapping keeps its `kind`. Germinate plants the gardener in the new words and takes
  `--gardener-genos` (`--gardener-kind` still read), as `bin/dmupgrade.py` takes `--gardener-genos` and
  `DAFTAR_GARDENER_GENOS` (the old names still read); every tool reads and writes `genos`, `gene` and the Greek
  natures, and a merge's seed carries its `genos`. The reasons, and every option that was put to the operator — the
  one taken, and why — are in seed/RATIONALE.md under `natures`. The suites that hold it: test/upgrade.py (a 21.0
  garden translated and passing its gate), test/refusals.py and test/germinate.py (every retired word refused,
  naming its Greek one).
- **21.0** (2026-09-23, proposed rule-change) — **what passes between: persons, and gardens.** MAJOR. Until now the
  language described one gardener's world. The first garden kept by someone who had not written the language needed
  what it could not say: money, an agreement between two people, the person who keeps the garden, and a thing two
  gardens share — so its agreements sat in free keys under `details`, the person who keeps it appeared in it only as
  an outside party in prose, and a merge of it against a copy of itself saw two records as four. BETWEEN PERSONS: a
  `money` dimension and quantity whose units are the currencies Unicode CLDR publishes (`currencies`, a registry
  file), with no factor between two of them — a rate is an observation, never a law — and a count held to the
  currency's decimal places; a `ratio` quantity; an agreement as structure — `parties` (each with the day it
  accepted, or no acceptance on record: an offer is not an acceptance; merged party by party, so a difference about
  one party stays on that party), `words` (written, spoken or not yet put into words, and where), `clauses` (each a
  position on the `capability` square, with amount, due day, recurrence and condition, and `expiry` per entry that
  `unless` silences once met) and `transactions` (what moved, on which `day`, who paid, who bears it in whole
  shares, their parts summing exactly to the whole through the new schema construct `sums`, and each party named
  once among the payers and once among the bearers through the new `keyed_by`, their order carrying nothing). A
  count or a share is what was written: plain decimal digits, bounded in number so every reader holds them exactly;
  the loader reads a plain scalar as an integer only in plain decimal, so YAML 1.1's octal, hexadecimal, binary,
  sexagesimal and underscore spellings (`010`, `0x64`, `1:30`) are refused, never read as another amount. A day a
  calendar reckoned by rule does not have (`2026-02-30`, a thirtieth of a twenty-nine-day month) is refused, never
  moved. A balance is read from them, never stored, so `balance` is retired. `contract` names `ownership_form:
  [crown]`: it may end at the crown and be answered for by its `parties`, owned by none of them — or be owned by its
  author, as before. `document` and `event` are kinds, identified by `content_hash` and `event_id`, and a happening
  between people may end at the crown too, answered for by whoever hosted it. `recurrence_form.times` counts
  instalments. BETWEEN GARDENS: the manifest is judged as itself (`manifest`): each attribute in its form, the
  required ones present, `daftar_release` a release tag or `untagged <commit | unknown>`, and its `gardener` a bean the garden
  holds, of a kind the manifest admits — a person or an organisation; a garden grown to rehearse says so in `test`; a
  garden is a being (`garden`, anchored by `garden_id`: the commit it germinated from, which no one assigns and every
  clone shares), and the receiving garden marks one it knows to be a rehearsal with `test`, its own record, whatever
  that garden's proposals say; the anchor terms whose values a garden mints say `minted: true`, and
  `identity_policy.minted` gives a minted name its form, `<kind>:<name>`, and qualifies it by the garden that gave it
  (`<garden_id>/<kind>:<name>`), so equal bare names from two gardens are candidates and never fused — while a value
  of such a term in any other form (a package's name, a registry number, an invitation's UID) was assigned outside
  every garden, fuses as every anchor does, and is refused qualified; `provenance_record` declares the record every
  fact carries, `from` and `garden` included. AND: the ownership facets are a registry whose `depends_on` walk is
  checked acyclic and reaches `legal`, with `experience` and `financial` beside `legal` and `technical`;
  `entry_form_from_kind_attr` reads a list, which allows a form where one names pins it; `retired` lists what the law
  took back, so a refusal says where it went — the anchor attribute `scope` (said by the term and the name's own form
  now), `between`, `agreement_ref`, `conflict_rule`, `balance`, `attributes` (into `details`), the `facets` term,
  `values_consistent_with`, and the manifest's `seeds_from`, `created` and `models`; the Tier-0 vacancy
  `located_at.openness = unknown` is withdrawn, occupied by a real bean; and the positions 21.0 adds that no garden
  uses yet are declared vacant, `universal`. GATE CHANGES: a key YAML does not read as text — `on`, `off`, `yes`,
  `no`, a bare number — is refused, never crashed on (the transactions attribute is `day` for that reason); what the
  gate cannot read it refuses, saying where, never with a traceback; a local term named for a retired one says where
  it went; a `garden` bean anchored by this garden's own id is refused; a journal line a commit adds holding a
  character some reader takes for a line break is refused, so no line can carry a heading nobody stamped. With the
  release: gardens meet by proposal (`bin/dmpropose.py`: a garden's first contact with another, a fingerprint that
  detects damage and is not a signature, a proposal taken once, every record stamped with the garden it was made in
  so that no garden speaks as another, and taking an agreement in never its acceptance, which is the receiving
  gardener's own word); a merge compares one fact written two ways as one value (a count in its shortest exact
  decimal, a keyed list in its key's order); what is owed is read (`bin/dmledger.py`), `bin/dmstale.py` warns before
  each clause falls due, and `bin/dmunits.py` converts between two currencies only at a rate passed in (`--rate`);
  germination writes a random seed into the first commit, so two gardens grown alike are two, and plants the
  gardener — a person, or with `--gardener-kind org` an organisation — qualified at birth, and a rehearsal is grown,
  never cloned; `bin/dmupgrade.py` carries a garden into 21.0 and names its gardener (`DAFTAR_GARDENER` where the
  garden's own tool is older than `--gardener`); the hooks choose a Python that imports yaml; the tools write UTF-8
  on every platform, `bin/dmjournal.py` included, which reads a body on standard input as UTF-8, refuses every control
  character but a tab, and prints the heading only once it is written; no command a tool prints or a page gives joins
  two with `&&` or removes files with `rm`, a path holding a space is quoted, and a body or a block goes in with
  `--body` or `--block` — so each runs in Windows PowerShell 5.1 too, with `python` for `python3`, but where a page or
  a tool's help shows a Unix shell's form (its `<`, its `$(…)`) and gives PowerShell's beside it; and MODEL.md says
  whose a judgment is. AFTER THE LAST REVIEW: TEXT IS TEXT — the law says a value holds no control character (every
  one Unicode names but a tab, and a line feed only where a value may hold lines), the gate refuses one in any key or
  value of a bean, a mapping, GARDEN.md or VOCAB.md, naming where it is and which (`U+001B`), and every message the
  gate, `bin/dmledger.py` and `bin/dmstale.py` print quotes what a bean wrote escaped, so a garden that already holds
  such bytes cannot drive its reader's terminal; a disagreement is left standing only as the merge captures one — a
  record of exactly `{conflict: [<two sides or more>]}`, at a path the bean's `merge_conflicts` names, while
  `merge_open` is set — and any other conflict record is refused by name; a value where the law asks for one position
  (a clause's `stance`) that is a list or a map is refused by name, and a proposal whose scratch gate ends without a
  verdict is not called clean; a bean, a mapping, GARDEN.md or VOCAB.md that is not UTF-8 is refused by name, saying
  what it looks like; each entry of a VOCAB.md block is read in its shape — by the gate for this garden's, by the
  merge for another's — and refused by name where it has another; the reverse gate counts the positions of a closed
  list on an attribute of a mapping-shaped term, and `words.form`'s `written` and `unstated` are declared vacant,
  `universal`; the law says, where it defines a date, that a day its calendar does not have is no date, the gate
  judges it in the calendars the law marks as reckoned by rule, and `bin/dmrules.py` prints it; the manifest's
  `policy` has the shape its meaning says: rules, in prose. Between gardens: `dmledger --between` names each shared
  agreement it left out of the net and why, and calls the net partial when it left one out; an entry that carries its
  own provenance goes back to the garden it came from and reads clean, however often it crosses — and a value both
  gardens changed at once reads as a disagreement, never a forgery; each recurrence is walked within its own allowance,
  and every recurrence of a run within one budget, a clause beyond either named as not walked and the run of dmstale
  then exiting 1, so no clause can hide another's due day; a proposal's records are stamped whichever way their keys
  are written (JSON's `"provenance":` too); a YAML set is refused as no shape a garden writes; a clause that does not
  repeat is shown due in the calendar it was written in; `make` says a party in a merge conflict is a person's to
  settle first; first contact prints each bean once, and an organisation's bean in the law's form for a gardener. The
  tools: germinate judges a garden's name by the law's form before it creates anything, takes `--name` where the
  directory is named otherwise, removes what it made when anything stops it, and grown from inside a garden records
  the release that garden runs; `bin/dmupgrade.py` refuses a garden whose name the release's law refuses before
  touching anything, printing the `garden:` line to write and its RULE-CHANGE entry, and plants an organisation as the
  gardener too (`--gardener-kind org`, `DAFTAR_GARDENER_KIND`); `bin/dmsafe.py` reads a block as UTF-8, or UTF-16 with
  its mark, on every platform, from standard input or from a file with `--block`. The suites that hold it:
  test/money.py (money and agreements), test/mycelium.py (gardens and proposals), test/refusals.py (what the gate
  refuses, and that it refuses rather than crashes), test/journal.py (the journal's one tool, and dmsafe's block),
  test/upgrade.py (a garden into the release, its name and its gardener), and test/germinate.py, which commits the
  cookbook's recipes one at a time, in the order of the page.
  THE LAW UNCHANGED, the tools corrected by what a first real rehearsal met: the fast check reads `captures/` as it
  reads the journal — a record held whole, whose quoted versions are what was said, never the garden stating its
  release; and `dmpropose make` tells a bean with no establishing anchor at all that it has no identity here yet —
  give it one, or name it in words where it is referred to — instead of pointing at `mint`, which has nothing to
  qualify.
- **20.0** (2026-09-22, proposed rule-change) — **a heading is stamped by the clock, not typed; an anchor says how it
  is known the way every fact does.** `journal.heading: stamped`: `bin/dmjournal.py` writes every heading from the
  clock and records it in the clone's git directory, and the gate refuses a heading a commit adds that the tool did
  not write. The form was checked since 10.0; the truth of the moment never was, and a writer typed the time before
  reading it twice in one evening. With the release: `seed/germinate.py` and `bin/install.py` — a garden grows
  on Windows, where `sh` is not a given; the shell scripts hand over to them. And the anchor:
  `anchor_authority` (`scanned < operator-asserted < external`) was a second vocabulary for the one question
  `provenance_src` answers, and the two disagreed on twelve anchors of the first garden. It is retired: an anchor
  carries `provenance: { src, by, as_of }` where its source differs from the bean's, and nothing where it does not
  — the rule every entry has had since MODEL v2. `identity_policy.anchor_attrs` declares what an anchor may
  carry, so a retired or invented attribute is refused with its reason. The merge ranks two records of one
  anchor by `provenance_src`, as it ranks every other value.
- **19.0** (2026-09-22, proposed rule-change) — **an anchor's key is a term, and a virtual machine is a living
  being.** The fourth cold-start drill invented an anchor key and the gate took it; measured, one garden's beans
  carried seventeen keys no term declared, and identity is matched by (key, value), so an open key was an open
  merge key. `identity_policy.anchor_key: term`: every anchor's key names a term that declares `anchor:`, and the
  gate refuses any other. The ids the kinds registry had named in prose since P3 are declared: `product_id`,
  `service_id`, `org_id`, `person_id`, `program_id`, `contract_id`, `design_id`, `doc_id`, `manifest_id`,
  `session_id`, and `email`. `identity_policy.establishing_family: enforced`: an establishing anchor of a confirmed
  bean is of its nature's family, as the registry has said and `dmrules` has printed since P3 — the gate had
  checked only the count. The one bean that broke it was a rented VPS anchored on its name, and the cookbook's
  recipe had the same shape, because a virtual machine has no matter to anchor: `virtual-host`, `of_nature:
  living`, is a running machine-instance that lapses at teardown, as `instance` is; `host` is matter. This is the
  reading the kinds registry foresaw at P3 ("D5 will re-read this as an instance living_on a provider").
  With it, the terms classed before there were natures: `wg_pubkey` and `ssh_key_fingerprint` are logical
  credentials, `mac` establishes only matter, none of the three pins `establishing` — the family decides;
  `anchor_class` decides again and loses `none`; `id` and `ref` carry no anchor block; `shell-log` is retired;
  the living family is `[logical]` (`personal` named a class that never existed); `owned_by` is required on
  every bean; `status` loses `at-risk`, which `risks.state` carries; the kinds rows are their nature and
  meaning, the prose `schema`/`required`/`min_anchors` copies gone; and the promotion notes on terms that are
  the standard are gone with them.
- **18.3** (2026-09-20, proposed rule-change) — **who may reach a surface is a fact of its own.** `endpoints` gains
  `admitted_from` (prose): the named sources a surface admits, beside `exposure`, which says only where it is bound.
  The management-on-the-internet cell becomes `expects: [admitted_from]` instead of `verdict: in_breach`: it warns
  while nothing is said about who may reach the surface and is silent once it is. It can only let a warning stop —
  no entry that passed is refused, and the cell fires on exactly the entries it fired on before. The gate's
  conditional cells (`requires` / `expects`) now take a `when` of more than one attribute, as verdict cells did.
- **18.2** (2026-09-20, proposed rule-change) — **a form a tool already checks is checked by that tool.** A system
  row states its form as a `pattern` or names a check with `checked_by`, never both. `ipv4` and `ipv6` are
  `checked_by: ipaddress-v4 / ipaddress-v6` — the standard library's validator, which the `ip` anchor has always
  used — and their patterns are gone. The form is the library's own spelling, so an address has one: `2001:db8::1`,
  not `2001:DB8::1` and not the exploded form. TIGHTER than 18.1 in that one respect.
- **18.1** (2026-09-20, proposed rule-change) — **nothing is untyped.** `in: { entries: {…} }` — entries INSIDE an
  entry, each judged as an entry by every rule an entry answers to; `in: bean_id`; `in: any`, a decision where `untyped`
  is a debt. `beanger.records` is typed with them and `record_attrs`, a map of sentences nothing read, is gone: a
  record's attributes are attributes. The law now has no `untyped` attribute. TIGHTER, and so able to refuse what
  passed: the `ipv4` row's pattern admitted `256.1.1.1` and `01.2.3.4`, and both rows any prefix length; an octet is
  now 0-255 without a leading zero and a prefix is 0-32 or 0-128. The `ip` anchor always checked this; a position in
  the same system did not.
- **18.0** (2026-09-20, proposed rule-change) — **what was owed.** MAJOR, four things.
  A REGISTRY IS ITS OWN ENUM OWNER: the five terms that only held a copy of a registry's column are gone
  (`anchor_system`, `unit`, `role`, `storage_format`, `net_protocol`) with their drift guards; `nature` and `os` read
  theirs with `values_from: "registry:<name>[].<field>"`. A position in a registry is addressed `registry:<name>`,
  which is where a vacancy for an unused row is declared (`dmupgrade` rewrites a garden's). A garden that adds a row
  states it once, under `registry_additions`.
  A MAPPING IS ONE ENTRY: a term whose value is a mapping is judged by the same controllers as an entry of a list.
  Until now the value scope had its own copies of four of them and none of the rest, so a closed list, a pattern or a
  pointer declared on a mapping's attribute was read by nothing.
  TWO DOMAINS: `in: { system: <anchor system> }`, a position in one named system; `in: { key_of: <term> }`, a key of
  that term's mapping on this bean or `<bean>:<key>` on another. With them twenty-six of the twenty-seven `untyped`
  attributes are typed — dates as dates, stamped moments as `unix-epoch`, a link a surface rides as a key of `links`
  — and a garden whose values were free text in those positions is told so. One remains, `beanger.records`.
  NO CALENDAR IS THE ONE TIME IS READ IN: the `instant` order holds between readings in any declared calendar, asked
  at the day, and across two calendars only when both begin their day at the same moment. A journal heading is a
  position in any declared calendar, in that calendar's own form, to the minute and with its offset; the journal's
  copy of one calendar's pattern is gone (`journal.system` names one for a garden that wants one).
- **17.0** (2026-09-20, proposed rule-change) — **quantities.** MAJOR: a `units` row names its `quantity` and its
  `factor` instead of a `dimension`, so a garden that added a unit restates it. A QUANTITY is a product of powers of
  base `dimensions`: duration is time, area is length squared, SPEED is length per time, ACCELERATION is length per
  time squared, a data rate is information per time. `in: { quantity: <name> }` types an attribute as a measured value
  `{ count, unit }`, and the unit must measure that quantity. An extent's measure may now be an AREA or a VOLUME: it
  spans as many lines as its unit has powers of the metered dimension, and never more than the system has (`geographic`
  has three; `time` has one, so there are no square seconds). `level` and `attenuation` are LOGARITHMIC quantities —
  decibels, and decibels per metre — whose values add where the ratios they stand for multiply. `bin/dmunits.py`
  converts within a quantity by exact rational factors and refuses across quantities.
  EXACTNESS IS A RULE, not a habit of the tool: a `factor` is two positive whole numbers in lowest terms and the gate
  refuses anything else; a `count` is a whole number or a decimal string, never a float; a conversion is printed in full
  or as a fraction of whole numbers, never rounded; and a conversion is a READING — a bean keeps the value in the unit
  it was measured in, so no chain of conversions can accumulate an error.
