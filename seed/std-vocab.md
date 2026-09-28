---
version: "29.1"
# == THE SCHEMA LANGUAGE ==
schema_language:
  shape:                "scalar | mapping | list_of_entries | open_map_of_entries — the term's on-bean form"
  attrs:                "{<attr>: {required?, in, meaning}} — THE ATTRIBUTES: one record each, saying what the attribute is a position IN, whether it is required, and what it means — once, for the gate and the reader both. They describe each ENTRY of a list, an open map or a faceted mapping, and otherwise the mapping itself. An entry holds only the attributes declared here. See `attr_domains` for what `in:` may say."
  default_from:         "{registry, keyed_by, take} — inside an attribute's record: when the entry is SILENT, the attribute's value is READ from a registry row, the row selected by another attribute of the same entry. The registry stays the one owner of the usual value (a protocol's transport), and an entry states the attribute only when it differs. Like an aspect's default, a value that came from here never counts as OCCUPYING a position."
  origin:               "{act, nature?, by?} — inside an attribute's record: WHERE A VALUE IN THIS POSITION COMES FROM, sorted by nature. `act` is a row of `acts`: made here, derived from what was given, read off the world or a clock, or said; `nature` is the nature of what it comes from, a row of `natures` or a list of them, and absent it may be any; `by` is one of the names the act's row lists, and absent the act is the recorder's own. Stated only where the one its domain gives (the domain's record in `attr_domains`, or the `origin` of its value type's row) is wrong, so every position has one origin and no tool keeps a list of names. A position read by the save (`by: save`) is written `now`, and the save writes in its place the reading of the journal heading it writes: the day at a date, the moment at a moment. A position its recorder reads (`act: read` and no `by`) may be written `now` too, and a reading typed there stands. A domain whose positions are its own (`entries`) or another's (`any`: the value of the field it tracks) takes no origin of its own, written `inner`"
  cells:                "[{when, verdict|requires|expects, why}] — COMBINATIONS of what an entry holds. `verdict: incoherent` is an ERROR (the positions cannot both hold, so one is mis-stated); `verdict: in_breach` a WARNING (all can hold, and the state needs action). `requires: [...]` is an error when the entry sits in the cell and lacks those attributes — an item that is itself a list names alternatives, one of which is enough (`[[at, external]]`); `expects: [...]` the same as a warning. `when` maps an attribute to the value it holds, or to `{starts_with: …}`; an aspect attribute is read at its EFFECTIVE position, stated or defaulted."
  attr_domains:
    values:      { form: "in: [a, b, c] — one of a closed list written here", origin: { act: said, nature: lekton, by: law } }
    registry:    { form: "in: { registry: <name>, take: <field> } — a row of a registry, so the registry OWNS the enum and no term restates it. `where: { <field>: <value> | [<values>] }` narrows it to the rows that say so — a PLACE system, a TRANSPORT-layer protocol — so one registry serves attributes that may name only some of its rows. `registry_from: <attr>` instead of `registry`: the registry is NAMED by another attribute of the same entry", origin: { act: said, nature: lekton, by: law } }
    aspect:      { form: "in: { aspect: <name>, default: <position> } — a position on an opposition; the default applies when the entry is silent, and a default never counts as occupying the position", origin: { act: said, nature: lekton, by: law } }
    type:        { form: "in: { type: <value type>, unit?: <unit> } — a row of `value_types`: its pattern, and for a time type its system and unit. `unit` beside a position type holds the attribute to that unit or a finer one — `minute` for a moment — and is the unit the save writes for `now`", origin: { act: said, nature: [lekton, empsychon] } }
    form_of:     { form: "in: { form_of: <registry>, keyed_by: <attr>, take: pattern } — a position in the system a SIBLING attribute names, written in that system's ONE form. A row declaring `pattern: none` has deliberately no canonical form", origin: { act: said, nature: [lekton, empsychon] } }
    system:      { form: "in: { system: <anchor system> } — a position in ONE named system, in that system's one form. `form_of` asks a sibling WHICH system; this names it, for an attribute that is only ever in one", origin: { act: said, nature: [lekton, empsychon] } }
    key_of:      { form: "in: { key_of: <term> } — a key of that term's mapping ON THIS BEAN, or `<bean>:<key>` on another: a PART of a being, resolved by the gate. Not an edge — the being is reached by the refs the bean already states", origin: { act: said, nature: lekton, by: law } }
    entries:     { form: "in: { entries: { <attr>: {required?, in, meaning} } } — entries INSIDE an entry: a list of them, or one mapping. Each is judged as an entry, by the attributes written here and by every rule an entry answers to. A ref inside one is resolved and draws no edge. `keyed_by: <attr>` beside `entries` says the list holds ONE entry per value of that attribute, and that the order of its entries carries nothing: two entries for one value are refused, and a merge compares the list in that attribute's order `one_of: [<attr>, ...]` beside `entries`: each entry inside carries at least one of these; `at_most_one_of: [[<attr>, ...], ...]`: and at most one of each group. `keyed_by` may name several attributes, `[<a>, <b>]`: one entry per combination of their values.", origin: inner }
    bean_id:     { form: "in: bean_id — the bare id of a bean the garden holds: resolved by the gate, and not an edge (an edge is a `ref`). `in: { bean_id: { gene: [<genos>, ...] } }` holds it to a bean of one of those gene", origin: { act: said, nature: lekton, by: law } }
    any:         { form: "in: any — DELIBERATELY any value, because its type is another attribute's business (a record's `value` is whatever the tracked field holds). A decision, where `untyped` is a debt", origin: inner }
    pattern:     { form: "in: { pattern: '<regex>' } — a form the TERM owns. With `soft: true` and a `why` it WARNS instead of refusing: the form a value SHOULD take while a corpus is migrated onto it", origin: { act: made } }
    quantity:    { form: "in: { quantity: <name> } — a MEASURED VALUE, written { count, unit }: a speed, an acceleration, an area, a data rate, an amount of money. The unit must measure the quantity named; `count` is a whole number or a decimal written as a string, in the form `value_types[count]` declares, so that no float reaches a canonical form and every reader holds it exactly. A quantity whose row takes its units from a registry (`units_from`) holds a count with at most the row's `digits` decimal places. `in: { quantity: any }` takes any. A quantity may carry how well it is known inside it — `u` or `accuracy` (`uncertainty_form`) — and holds nothing else beside `count` and `unit`.", origin: { act: said, nature: [lekton, empsychon] } }
    extent:      { form: "in: extent — a bounded region of an aspect's domain (`extent_form`)", origin: { act: said, nature: [lekton, empsychon] } }
    recurrence:  { form: "in: recurrence — a repetition over a sequence: every Nth neighbour, every N units, or the same place in each cell of a level (`recurrence_form`)", origin: { act: said, nature: [lekton, empsychon] } }
    ref:         { form: "in: ref — a {bean|mapping: <id>[, field: <key>]} ref; the gate RESOLVES it (dangling = error)", origin: { act: said, nature: lekton, by: law } }
    origin:      { form: "in: origin — where a value comes from, `{act, nature?, by?}` (`schema_language.origin`): a row of `acts`, a row of `natures` or a list of them, and one of the names the act's row lists", origin: { act: said, nature: lekton, by: law } }
    pointer:     { form: "in: { pointer: bean_field_pointer } — '<section>.<key>' on this bean, {bean, field} on another, or 'file:<path>'", origin: { act: said, nature: lekton, by: law } }
    id:          { form: "in: id — the id of a bean or mapping: a key of the ref FORM itself, on a term whose value `is_ref`", origin: { act: said, nature: lekton, by: law } }
    prose:       { form: "in: prose — a reason, a description, a remark. DELIBERATELY not a position: `why`, `what`, `note`. The reason IS the fact, and a schema for it would launder an opinion into a field. `in: { prose: named }` — one text, or several under the names of what each says: a map of named sayings, each one text", origin: { act: made } }
    untyped:     { form: "in: untyped — a position whose domain nobody has declared yet. A standing debt, written down so that an oversight and a decision stop looking alike", origin: { act: said, nature: [lekton, empsychon] } }
  is_ref:               "true — the value (or each entry) IS ITSELF a {bean|mapping: <id>[, field: <key>]} ref, which the gate resolves"
  path:                 "<dotted path> — the term governs a NESTED field rather than a top-level key named after it (`identity.status`, `identity.anchors[].class`, `provenance.src`)."
  alt_form:             "{key, ref_fields} — an ALTERNATIVE whole-value form: a mapping carrying `key` takes this form INSTEAD of the faceted one, and the per-key rules stand down for it (the inherited `owned_by: {via: …}`)."
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
  at_most_one_of:       "[[<attr>, ...], ...] — each inner list is a GROUP of attributes of which an entry carries AT MOST ONE: two are refused as a contradiction — a stated `due` beside a `falls_due`, a `u` beside an `accuracy`. With `entry_one_of` naming the same group, exactly one"
  keyed_by:             "<attr> | [<attr>, ...] — beside a `shape` whose value has entries: ONE entry per value, or per combination of values, of these attributes among the term's entries on one bean (one observer's one verdict on one entry). An entry holding none of them is not counted; two holding the same are refused, and both are named"
  exclusive:            "{extent: <attr>, being: <attr>, role?: <attr>} — the extents that entries of this term hold for ONE being, in ONE role, across every bean of the garden, do not overlap: one person booked twice over the same days, one room lent twice. The gate refuses an overlap and names both entries; an entry its term's `expiry.unless` silences, or that says it was declined, is not counted. The law puts this on no term: a garden that needs it adds it to a term in its VOCAB.md, a RULE-CHANGE"
  expiry:               "{attr, notice, why} — ONE of this term's attrs is the position at which the thing LAPSES if nothing is done, and a reader should be warned before it. `notice` is HOW LONG BEFORE, as an EXTENT on `time`. `why` is the CONSEQUENCE, printed with the warning, because a date alone does not say what is lost. Read by bin/dmstale.py, not by the gate: a check whose answer changes with the calendar would make the gate non-deterministic, and a gate that fails on a Tuesday for no committed reason is a gate people disable. Deliberately NOT derived from an attribute's type: most dates a bean carries are `observed` or `as_of`, the day a fact was READ rather than the day it runs out. A term that does not declare this is never warned about, which is why a garden's own term can buy the warning its Tier-0 neighbour has. On a term whose value is a list or an open map, the attribute is each ENTRY's, and each entry is warned about by itself. `repeats: <attr>` names a sibling attribute `in: recurrence`: the position falls due again at each occurrence after `attr`, and the reader is warned before the next. `unless: {<attr>: [<values>]}` names the entries that no longer lapse — a debt already met. `relative: <attr>` names a sibling attribute holding the position RELATIVE to another (`from`, then `after` or `before` by an extent, then `at` a place in the cell reached), read in the place of `attr` where an entry states it. `lapses: <attr>` names a sibling attribute `in: extent`: the entry LAPSES at that extent's end, and a reader warns before it with `lapses_why`. `permission: <attr>` names the attribute whose EFFECTIVE position on its aspect chooses the words: `why` and `lapses_why` are each one text, or a map from that aspect's positions to the words — an obligation falls due, a permission lapses. `condition: <attr>` names the attribute holding what brings an entry into force where that is not a day: an entry holding one has no due to be missing."
  sums:                 "{whole: <attr> | [<attr>, ...], parts: <attr>.<attr>} — the PARTS of a quantity add up to its WHOLE: the parts are the named attribute of each entry inside `parts`' first attribute, the whole is the first of `whole` the entry states. Checked exactly, in fractions, whenever every count is known, and the parts must be in the whole's unit. An entry holding one part that states no amount holds the whole. A LIST of such rules is several wholes, each checked. `whole` may be a constant quantity instead of an attribute (`{ count: 100, unit: percent }`: shares of a whole), and parts in another unit of the same quantity are converted exactly. `per: { level: <level> }` groups the parts by the ancestor, at that level, of the code each part names (its entry's `scheme` and `code`): each group makes the whole on its own — the amounts of each plan of an analytic distribution make the amount"
  on_sequence:          "<aspect> — the term's value is a walk on that SEQUENCE aspect: prose lines in list order, or step entries {id, do, next: [{to, when?}]} whose neighbourhoods are CLOSED; each step entry is judged by the term's `attrs`, and a key they do not declare is refused; the gate refuses a `to` that names no step, a step nothing reaches, a branch with no condition, a routine with no end, and a loop when the aspect declares acyclic"
  series:               "true — each ENTRY of this term is a SERIES: a line whose positions HOLD values (the figure's `holds`). Its positions are its `grid`, a recurrence whose occurrences are its rows in order, or listed in its `span`, an extent from whose `from` each row writes its offset; `unit` is what an offset counts and the resolution held; `holds` names the channels, one column each; its rows are one table (`value_types[rows]`) inline in `rows`, or the parts `series/<bean>/<key>/<part>.tsv` in the estate, each added whole and never rewritten; `excluded` sets a cell aside, naming its judge. The gate reads every row against its channels, and nothing read from a series is stored"
  moves_along:          "<attr> — each entry of this term is a MOVE along the course its <attr> names, a key of a term whose entries each name a `walk`: its `step` is a step of that walk, and the moves of one course, in the order of their moments, are held to it — a move follows a `next`, reaches an `exit`, or returns to the step a pause (`resumes`) was entered from; a move `next` does not offer passes only with a `why`, and warns; nothing follows a `final` step; a moment never goes back, and one course's two moves to one step are two moments. Where a course stands is read, never stored"
  dag:                  "true — this term's edges are positions on the `walk` sequence aspect (`dag` is that aspect's `term_key`), and they join the acyclic check BECAUSE that aspect declares `acyclic: true`"
  required_on_targets_of: "<term> — a bean that is the TARGET of that relation must carry this term (e.g. anything lived in must say what kind of habitat it is)"
  entry_must_match:     "[{attr, registry, keyed_by, take}] — an entry attr must equal a registry row's attr, the row selected by a field on the bean (e.g. the crown branch is fixed by the bean's nature)"
  entry_form_from_genos_attr: "<attr> — a genos that names ONE form in this attr PINS it: every entry must use it. A genos that names a LIST ALLOWS those forms beside the ordinary ones. Either way a form some genos names is RESERVED to the gene that name it, so no other bean can short-circuit its chain to the axiom (only genos:person may pin `crown`; an agreement may choose it)."
  governs_anchor:       "<key> — this term governs the FORMAT of anchors carrying that key; pairs with value_pattern or value_form"
  value_pattern:        "<regex> — the canonical form an anchor value must match (with canonical_note as the human statement of it)"
  value_form:           "ip — a format needing real parsing rather than a pattern"
  canonical_note:       "<prose> — with value_pattern or value_form: the human statement of the canonical form, printed in the refusal and by bin/dmrules.py. Prose for a reader; the gate checks the pattern, never this."
  enforced_by:          "core | none — an explicit statement for a term with NO schema: either CORE already enforces it, or there is genuinely nothing to check and this says why"
  poles:                "one axis (a contradictory PAIR), or a LIST of axes — a figure may be 1-dimensional, 2, 3 or more, and the gate derives the count rather than assuming it"
  facet_parity_with:    "<term> — this term and that one must carry the SAME facet keys (two arcs of one loop); one present without the other is a loose end"
  values_add:           "[<value>...] — GARDEN overlay only: APPEND values to a Tier-0 term's enum instead of replacing it, so the garden accounts only for what it added"
  compare_form:         "upper-trim — with governs_anchor: the anchor is compared in this form for uniqueness (whitespace removed, uppercased), and a stored value not already in it warns"
  value_in_registry:    "{registry, take} — with governs_anchor: the anchor value must be a ROW of that registry (a code of a published classification, 9.1)"
  inverse_of:           "<term>, or {term, cardinality: one-to-one | many-to-one} — this relation mirrors another and the gate holds the pair consistent so the convenience edge cannot drift from the fact. A BARE NAME means one-to-one and the mirror is enforced BOTH ways. `many-to-one` enforces only the functional direction: many instances point at one type, and the type cannot point back at all of them through a single mapping. Declare the cardinality; assuming a bijection is how a rule becomes unsatisfiable without anyone noticing."
term_form:
  attrs: [term, meaning, context_keys, schema, merge, anchor, enforced_by, exceptions, values_meaning, values_source, promotion, placement]
  meaning: "THE TERM RECORD: what a term of the law, of a profile or of a garden's `local_terms` may hold — its name, its meaning, where it is found, its schema, how it merges, how it anchors, what enforces it, its dated case law, the meaning and source of each value of an enum, and a garden term's promotion. Nothing else: a note a reader needs in order to apply the term is part of its `meaning`, and why the term is so is reasoning, kept apart from the law"
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
  issued: "an `identifier` written with `issuer: {bean: <org>}` is ISSUED: it identifies only together with the organisation that issued it — an employee number, a file number, a membership number. The same value from two issuers is two identities. A genos whose `identifier_forms` admit `issued` and not `assigned` refuses an identifier that is neither minted nor issued, because a number with no issuer would fuse two beings every issuer numbers alike"
  anchor_attrs: [key, value, class, establishing, observed, provenance, issuer]
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
  - { name: iso_date,      at: value_type, instead: "`position`: a position in time, in any calendar — the Gregorian day `2026-09-20` is one, written as before" }
  - { name: date,          at: value_type, instead: "`position`: a day is a position held to the day, written as before — `in: { type: position }`, or `in: { type: position, unit: day }` where the save writes the day for `now`" }
  - { name: moment,        at: value_type, instead: "`position` held to the minute: `in: { type: position, unit: minute }` — a moment is written as before, with its offset" }
  - { name: date_or_moment, at: value_type, instead: "`position`: a day, or a moment to the minute or finer, held to the unit its form is written at — `in: { type: position }`" }
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
  - { name: person_id, at: term, instead: "`identifier`: the one term for an identity a being is given, its value written as it was" }
  - { name: contract_id, at: term, instead: "`identifier`: the one term for an identity a being is given, its value written as it was" }
  - { name: event_id, at: term, instead: "`identifier`: the one term for an identity a being is given, its value written as it was" }
  - { name: session_id, at: term, instead: "`identifier`: the one term for an identity a being is given, its value written as it was" }
  - { name: program_id, at: term, instead: "`identifier`: the one term for an identity a being is given, its value written as it was" }
  - { name: design_id, at: term, instead: "`identifier`: the one term for an identity a being is given, its value written as it was" }
  - { name: doc_id, at: term, instead: "`identifier`: the one term for an identity a being is given, its value written as it was" }
  - { name: service_id, at: term, instead: "`identifier`: the one term for an identity a being is given, its value written as it was" }
  - { name: org_id, at: term, instead: "`identifier`: the one term for an identity a being is given, its value written as it was" }
  - { name: product_id, at: term, instead: "`identifier`: the one term for an identity a being is given, its value written as it was" }
  - { name: manifest_id, at: term, instead: "`identifier`: the one term for an identity a being is given, its value written as it was" }
  - { name: instance_id, at: term, instead: "`identifier`: the one term for an identity a being is given, its value written as it was" }
  - { name: emp_id, at: term, instead: "`identifier`: the one term for an identity a being is given, its value written as it was, with `issuer: {bean: <org>}`" }
  - { name: capability, at: aspect, instead: "`permission`: the aspect a being, an agreement or a grant takes a position on, and the attribute that takes it" }
  - { name: stance, at: attr, instead: "`permission`: an attribute on an aspect is named after the aspect" }
  - { name: target, at: attr, instead: "`to`: the far end an entry is directed at, as a treatment's and a clause's" }
  - { name: isced_f_2013, at: term, instead: "`identifier`, written as a coding of its scheme: `isced-f-2013:<code>` — a code a scheme's publisher assigned identifies the being that IS it, as any identity assigned outside every garden does" }
  - { name: isco_08, at: term, instead: "`identifier`, written as a coding of its scheme: `isco-08:<code>` — a code a scheme's publisher assigned identifies the being that IS it, as any identity assigned outside every garden does" }
  - { name: technology, at: term, instead: "`identifier`, written as a coding of its scheme: `technology:<code>` — a code a scheme's publisher assigned identifies the being that IS it, as any identity assigned outside every garden does" }
  - { name: git_host, at: bean, instead: "`located_at`, in the `git-remote` system — `{ system: git-remote, openness: here, at: <the remote> }`, or `host: { bean: <machine> }` alone where only the machine is known; where the code's own `git_remote` names its host, nothing: the host is read from it" }
  - { name: code_paths, at: bean, instead: "`located_at`: each tree a position in its host's filesystem, with the code profile's `role`, `scan_policy`, `stack` and `entrypoint` — and a tree of another code this one is read beside is that code's own location, reached through `depends_on`" }
  - { name: registration, at: bean, instead: "a contract `over` the domain: parties `registrant` and `registrar` (`external` where the garden holds no bean for one), `timing: { registration: <the day it began> }`, a clause `renewal` that falls due on the day it lapses with `notice: { count: 90, unit: day }` and the domain profile's `auto_renew`, and `words: { form: written, external: <whose terms> }`" }
  - { name: scheme, at: attr, instead: "`code`, which holds the code with the scheme it is a code of: `<scheme>:<code>`, one `coding`" }
# == ONE SENSE PER NAME: a name the law uses in more than one domain, and the one sense its uses share ==
senses:
  - { name: at,            sense: "a position — on a line, in a system or in a file — written in the form its place takes" }
  - { name: by,            sense: "who or what does it or did it: a person, a party, an instrument, a tool" }
  - { name: from,          sense: "where something starts: the position, system or field it is read or counted from" }
  - { name: holds,         sense: "what it holds — its contents, or the one place they are kept" }
  - { name: host,          sense: "the being a thing runs on, is kept on or was read at — the being a position's frame belongs to" }
  - { name: placement,     sense: "how a thing is placed in, at or among another: a row on its line, a being in or at its host" }
  - { name: id,            sense: "the name that identifies one of its kind once among its siblings: a bean's, a mapping's, a step's, an item's" }
  - { name: is,            sense: "what it is, as a classification: a scheme's process, a level of sensitivity" }
  - { name: kind,          sense: "which kind it is, from the list its place gives" }
  - { name: notes,         sense: "remarks beside it, in words or as entries of words" }
  - { name: of,            sense: "what it is of or concerns: a part, a copied thing, an amount it is a share of" }
  - { name: over,          sense: "what it is over or concerns: the beings of an agreement or a grant, the entries of a hearing" }
  - { name: path,          sense: "a way to one thing through a tree: of fields, or of files" }
  - { name: reason,        sense: "why, as one of a closed set of reasons" }
  - { name: rel,           sense: "the relation one thing has to another, by name" }
  - { name: role,          sense: "the part it plays, from the list its place gives" }
  - { name: notice,        sense: "how long before a day a reader is told of it: a clause's own, a feed's lead" }
  - { name: series,        sense: "a being's series of positions, or a pointer to one" }
  - { name: staleness_key, sense: "the value that, when it moves, makes what is kept stale" }
  - { name: steps,         sense: "the ordered steps it performs: a mapping's walk, a selection's operations" }
  - { name: title,         sense: "prose: the name a reader sees, as a bean's `title` is" }
  - { name: to,            sense: "where or whom toward: a party, a treatment's destination, the next step" }
  - { name: tool,          sense: "the executable a host runs, named by the host, as a mapping's `tool` is" }
  - { name: when,          sense: "the condition under which it holds or is taken" }
  - { name: who,           sense: "the person, party or being meant" }
  - { name: within,        sense: "the bounds it lies within: a place in a system, a window of time" }
# == PROVENANCE: the record every fact carries, declared ==
provenance_record:
  attrs: [src, by, as_of, from, garden, via]
  from_attrs: [src, by, as_of, at]
  origin: { as_of: { act: read, nature: soma, by: save } }
  meaning: "who said a fact and how they know — on a bean, an anchor or an entry. `from` names the records the fact was TAKEN or COMPUTED from — a map of name to record, or a list of records, each {src, by, as_of, at?} with `at` pointing at the input (`<section>.<key>`, {bean, field}, or `file:`); a generated fact weighs as the weakest of them. `garden` is the `garden_id` of the garden the record was made in, where that is not this one: stamped once, when a proposal carries the fact across, and never changed. `via` is the PATH after it: the gardens the record passed through, in order, each appended by the garden that passed it on and never rewritten; only the last must be a garden met, and a path holding the reader's own id is a loop, refused. `as_of` is the day the record was written down, and it is STAMPED (`as_of: stamped`): the day of a journal heading the same commit adds — read from the clock, as the heading is, and never typed. It is written `now`, and the save writes the day in its place. A record is matched by what it is (src, by, as_of), not where it sits, so one moved is not added; a record carrying ANOTHER garden's `garden` keeps the stamp that garden gave it; the merge engine's own record says `merged`."
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
# == ACTS: how a value came to be where it is ==
acts:
  - { act: made,    meaning: "made here, by the writer or a tool, from nothing given: prose, a name minted. It may hold a value found in nothing given" }
  - { act: derived, meaning: "computed from what was given: a count, a digest, a merge, an inference. It holds nothing its inputs did not, and can be no better than they were" }
  - act: read
    by:
      save:   "the clock, read BY THE SAVE and never typed: written `now`, and the save writes the reading of the journal heading it writes; a value a commit adds that is not the reading of a heading the same commit adds is refused. At a date or a moment only"
      reader: "the clock, read BY THE READER at the moment of reading: a reading's own now"
    meaning: "read off the world or a clock: a command's output, a machine's clock, a device's own report. With no `by`, by whoever recorded it: a reading typed is the recorder's report of what they read, and stands"
  - act: said
    by:
      law:    "by THE LAW: the schema owns the set of values — a row of a registry, a closed list, a position on an aspect, or a being, a part or a field a garden holds, which the gate resolves. Judged by the schema alone, whatever page the value was read on"
      garden: "by ANOTHER GARDEN, read from it at a commit it published and granted: the flow law judges it"
    meaning: "said by someone or stated in a document: a day agreed, an amount paid, a place, a yes. Its source is someone's words, and where it was read from is the flow law's to judge"
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
  - { crs: "EPSG:4326", body: earth, kind: geographic-2d, frame: dynamic, axes: [lat, lon],    ensemble_accuracy: { count: "2", unit: metre }, meaning: "WGS 84, latitude and longitude in degrees — what a satellite receiver reports — an ENSEMBLE of realisations, accurate to 2 m as EPSG states: no motion finer than that is read from it" }
  - { crs: "EPSG:4979", body: earth, kind: geographic-3d, frame: dynamic, axes: [lat, lon, h], meaning: "WGS 84 with ellipsoidal height in metres. Ellipsoidal height is NOT height above sea level" }
  - { crs: "EPSG:4978", body: earth, kind: geocentric,    frame: dynamic, axes: [x, y, z],     meaning: "WGS 84 geocentric: metres from the Earth's centre of mass" }
  - { crs: "EPSG:4258", body: earth, kind: geographic-2d, frame: static,  axes: [lat, lon],    meaning: "ETRS89: fixed to the Eurasian plate, so European ground keeps its coordinates. It and WGS 84 drift apart by about 2.5 cm a year" }
  - { crs: "EPSG:3857", body: earth, kind: projected,     frame: dynamic, axes: [x, y],        meaning: "Web Mercator: the plane nearly every web map is drawn on. For DRAWING; distances in it are wrong away from the equator" }
  - { crs: "EPSG:32639", body: earth, kind: projected,    frame: dynamic, axes: [e, n],        meaning: "WGS 84 / UTM zone 39N: metres on a plane, good within its six-degree zone. One of sixty; named because a projected system is where metres are honest" }
  - { crs: "EPSG:5773", body: earth, kind: vertical,      frame: static,  axes: [H],           meaning: "EGM96 height: metres above the geoid, which is what `above sea level` means" }
  - { crs: "EPSG:9990", body: earth, kind: geographic-2d, frame: dynamic, axes: [lat, lon], frame_epoch: "2015.0", meaning: "ITRF2020: the realisation plate motion is published in" }
  - { crs: "IAU_2015:30100", body: moon, kind: geographic-2d, frame: static, axes: [lat, lon], meaning: "the Moon (2015), planetocentric latitude and longitude on a sphere" }
  - { crs: "IAU_2015:49900", body: mars, kind: geographic-2d, frame: static, axes: [lat, lon], meaning: "Mars (2015), planetocentric latitude and longitude on a sphere" }
system_shape:
  neighbours: [none, counted, metered]
  reckoning:  [arithmetic, astronomical, observational, tabulated]
  crosswalk:  [computed, table, observed, none]
  day_begins: [midnight, sunset, noon]
  checked_by: [ipaddress-v4, ipaddress-v6]
  sources:
    reckoning:
      arithmetic:    { act: derived, nature: lekton }
      astronomical:  { act: read,    nature: soma }
      observational: { act: read,    nature: soma }
      tabulated:     { act: said,    nature: lekton }
    crosswalk:
      computed: { act: derived, nature: lekton }
      table:    { act: said,    nature: lekton }
      observed: { act: read,    nature: soma }
      none:     null
    datum:
      being:    { act: read, nature: soma }
      host:     { act: read, nature: [soma, lekton] }
      position: { act: said, nature: lekton }
system_registries:
  - { registry: anchor_systems,    key: system }
  - { registry: knowledge_schemes, key: scheme }
anchor_systems:
  - system: unix-filesystem
    dimension: place
    levels: open
    neighbours: none
    datum: host
    meaning: "a position in ONE NAMED HOST's UNIX filesystem. The host is part of the position: /home/user/tree on laptop-a and on laptop-b are different positions that print identically."
    pattern: '^(root:[a-z0-9][a-z0-9-]*(/[^:]*)?|[a-z0-9][a-z0-9.-]*:/.*)$'
    form_note: "root:<logical root>[/<relative path>] — resolved per host through that host's OWN root map, which is the form that survives a second machine; or <host>:<absolute path> stated outright where there is no root to hang it on"
    establishes: false
    why: "a path is reassignable and a tree can be checked out anywhere, so it CORROBORATES a location and never fixes it — the same rule that keeps `hostname` and `ip` corroborating-only"
  - system: git-remote
    dimension: place
    neighbours: none
    datum: host
    meaning: "a REPOSITORY as a client names it to fetch from: `<host>:<path>` as ssh writes it (`host-a:git/ledger.git`, `me@host-a:/srv/git/ledger.git`), or a URL (`https://example.org/ledger.git`). The host is part of the position, as a path's is: one path on two hosts is two repositories"
    pattern: '^([A-Za-z0-9._-]+@[a-z0-9][a-z0-9.-]*:[^ :][^ ]*|(?!root:)[a-z0-9][a-z0-9.-]*:([^/ :][^ ]*/[^ ]*|[^/ :][^ ]*\.git)|[a-z][a-z0-9+.-]*://[^ ]+)$'
    form_note: "the remote as `git remote -v` prints it, its host in lowercase. An ssh remote shows it names a repository — its user (`me@host-a:ledger`), or a path relative to the login with a `/` or a `.git` (`host-a:git/ledger.git`) — so it is never read as another system's `<name>:<value>`; a repository at an absolute path on a host is a position in that host's filesystem"
    establishes: false
    why: "a repository is mirrored and moved between hosts: where it is fetched from corroborates which code it holds, and the code's own identity is its `git_remote`"
  - system: git-object-graph
    dimension: place
    neighbours: counted
    datum: host
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
    restrictions: { lines: 1, order: partial, metered: time }
    meaning: "a calendar position with a stated offset. Civil time RESOLVES THROUGH a geographic position, which is why it does not establish on its own: an offset is minutes east of the prime meridian, and `Z` is that meridian's own time — no time here is absolute, each is read from a place."
    pattern: '^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2}(\.\d{1,3})?)?([+-]\d{2}:\d{2}|Z)?)?$'
    form_note: "YYYY-MM-DD[THH:MM[:SS[.sss]][+HH:MM|Z]] — the RESOLUTION actually held is stated separately in `unit` and is never inferred from how many digits were typed"
    establishes: false
    why: "a wall-clock reading without its geographic frame is ambiguous. The estate's own case: a cutoff computed on a +03 host was applied to UTC logs, and the watch reported zero hits while a campaign was running."
  - system: iso-week
    dimension: time
    calendar: iso8601
    reckoning: arithmetic
    day_begins: midnight
    resolves_through: geographic
    same_ground_as: [gregorian-civil]
    crosswalk: computed
    levels: [ { level: year }, { level: week }, { level: day, unit: day } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial, metered: time }
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
    resolves_through: geographic
    same_ground_as: [gregorian-civil]
    crosswalk: computed
    levels: [ { level: year }, { level: month, count: 12 }, { level: day, unit: day }, { level: hour, unit: hour }, { level: minute, unit: minute }, { level: second, unit: second }, { level: millisecond, unit: millisecond } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial, metered: time }
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
    resolves_through: geographic
    same_ground_as: [gregorian-civil]
    crosswalk: computed
    levels: [ { level: year }, { level: month, count: 12 }, { level: day, unit: day }, { level: hour, unit: hour }, { level: minute, unit: minute }, { level: second, unit: second }, { level: millisecond, unit: millisecond } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial, metered: time }
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
    resolves_through: geographic
    same_ground_as: [gregorian-civil]
    crosswalk: computed
    levels: [ { level: year }, { level: month, count: [12, 13] }, { level: day, unit: day }, { level: hour, unit: hour }, { level: minute, unit: minute }, { level: second, unit: second }, { level: millisecond, unit: millisecond } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial, metered: time }
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
    resolves_through: geographic
    same_ground_as: [gregorian-civil]
    crosswalk: computed
    levels: [ { level: year }, { level: month, count: 12 }, { level: day, unit: day }, { level: hour, unit: hour }, { level: minute, unit: minute }, { level: second, unit: second }, { level: millisecond, unit: millisecond } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial, metered: time }
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
    resolves_through: geographic
    same_ground_as: [gregorian-civil]
    crosswalk: computed
    levels: [ { level: year }, { level: month, count: 12 }, { level: day, unit: day }, { level: hour, unit: hour }, { level: minute, unit: minute }, { level: second, unit: second }, { level: millisecond, unit: millisecond } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial, metered: time }
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
    resolves_through: geographic
    same_ground_as: [gregorian-civil]
    crosswalk: observed
    levels: [ { level: year }, { level: month, count: 12 }, { level: day, unit: day }, { level: hour, unit: hour }, { level: minute, unit: minute }, { level: second, unit: second }, { level: millisecond, unit: millisecond } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial, metered: time }
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
    resolves_through: geographic
    same_ground_as: [gregorian-civil]
    crosswalk: observed
    levels: [ { level: year }, { level: month, count: 12 }, { level: day, unit: day }, { level: hour, unit: hour }, { level: minute, unit: minute }, { level: second, unit: second }, { level: millisecond, unit: millisecond } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial, metered: time }
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
    resolves_through: geographic
    same_ground_as: [gregorian-civil]
    crosswalk: table
    levels: [ { level: year }, { level: month, count: 12 }, { level: day, unit: day }, { level: hour, unit: hour }, { level: minute, unit: minute }, { level: second, unit: second }, { level: millisecond, unit: millisecond } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial, metered: time }
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
    resolves_through: geographic
    same_ground_as: [gregorian-civil]
    crosswalk: computed
    levels: [ { level: year }, { level: month, count: 13 }, { level: day, unit: day }, { level: hour, unit: hour }, { level: minute, unit: minute }, { level: second, unit: second }, { level: millisecond, unit: millisecond } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial, metered: time }
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
    resolves_through: geographic
    same_ground_as: [gregorian-civil]
    crosswalk: computed
    levels: [ { level: year }, { level: month, count: 13 }, { level: day, unit: day }, { level: hour, unit: hour }, { level: minute, unit: minute }, { level: second, unit: second }, { level: millisecond, unit: millisecond } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial, metered: time }
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
    resolves_through: geographic
    same_ground_as: [gregorian-civil]
    crosswalk: computed
    levels: [ { level: year }, { level: month, count: 13 }, { level: day, unit: day }, { level: hour, unit: hour }, { level: minute, unit: minute }, { level: second, unit: second }, { level: millisecond, unit: millisecond } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial, metered: time }
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
    resolves_through: geographic
    same_ground_as: [gregorian-civil]
    crosswalk: computed
    levels: [ { level: year }, { level: month, count: 12 }, { level: day, unit: day }, { level: hour, unit: hour }, { level: minute, unit: minute }, { level: second, unit: second }, { level: millisecond, unit: millisecond } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial, metered: time }
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
    resolves_through: geographic
    same_ground_as: [gregorian-civil]
    crosswalk: computed
    levels: [ { level: year }, { level: month, count: 12 }, { level: day, unit: day }, { level: hour, unit: hour }, { level: minute, unit: minute }, { level: second, unit: second }, { level: millisecond, unit: millisecond } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial, metered: time }
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
    resolves_through: geographic
    same_ground_as: [gregorian-civil]
    crosswalk: computed
    levels: [ { level: year }, { level: month, count: 12 }, { level: day, unit: day }, { level: hour, unit: hour }, { level: minute, unit: minute }, { level: second, unit: second }, { level: millisecond, unit: millisecond } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial, metered: time }
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
    resolves_through: geographic
    same_ground_as: [gregorian-civil]
    crosswalk: computed
    levels: [ { level: era }, { level: year }, { level: month }, { level: day, unit: day }, { level: hour, unit: hour }, { level: minute, unit: minute }, { level: second, unit: second }, { level: millisecond, unit: millisecond } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial, metered: time }
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
    resolves_through: geographic
    same_ground_as: [gregorian-civil]
    crosswalk: observed
    levels: [ { level: year }, { level: month, count: [12, 13] }, { level: day, unit: day }, { level: hour, unit: hour }, { level: minute, unit: minute }, { level: second, unit: second }, { level: millisecond, unit: millisecond } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial, metered: time }
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
    resolves_through: geographic
    same_ground_as: [gregorian-civil]
    crosswalk: observed
    levels: [ { level: year }, { level: month, count: [12, 13] }, { level: day, unit: day }, { level: hour, unit: hour }, { level: minute, unit: minute }, { level: second, unit: second }, { level: millisecond, unit: millisecond } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial, metered: time }
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
    resolves_through: geographic
    same_ground_as: [gregorian-civil]
    crosswalk: computed
    levels: [ { level: day, unit: day } ]
    neighbours: metered
    restrictions: { lines: 1, order: total, metered: time }
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
    resolves_through: geographic
    same_ground_as: [gregorian-civil]
    crosswalk: computed
    levels: [ { level: baktun }, { level: katun }, { level: tun }, { level: uinal }, { level: kin, unit: day } ]
    neighbours: metered
    restrictions: { lines: 1, order: total, metered: time }
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
    resolves_through: geographic
    same_ground_as: [gregorian-civil]
    crosswalk: observed
    levels: [ { level: year }, { level: month, count: 19 }, { level: day, unit: day } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial, metered: time }
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
    resolves_through: geographic
    same_ground_as: [gregorian-civil]
    crosswalk: observed
    levels: [ { level: year }, { level: month, count: 12 }, { level: decade }, { level: day, unit: day } ]
    neighbours: metered
    restrictions: { lines: 1, order: partial, metered: time }
    meaning: "the calendar of the French Republic: twelve months of thirty days in three ten-day decades, and five or six days over, the year beginning at the autumn equinox as observed from Paris. Declared because dated sources exist in it, and because its ten-day decade is a partition no other calendar here has."
    pattern: '^french-republican:\d+-\d{2}-\d{2}$'
    form_note: "`french-republican:<year>-<month>-<day>`; the days over are written as month 13"
    example: "french-republican:234-13-04"
    establishes: false
    why: "as for gregorian-civil"
  - system: unix-epoch
    dimension: time
    levels: [ { level: millisecond, unit: millisecond } ]
    datum: { system: gregorian-civil, at: "1970-01-01 00:00Z", direction: after }
    neighbours: metered
    restrictions: { lines: 1, order: total, metered: time }
    meaning: "a time position as milliseconds since 1970-01-01T00:00:00Z. It serves `beanger` records, whose ORDER is the thing being recorded — two operations in one session land in the same second, and a position that cannot separate them cannot order them."
    pattern: '^\d{13}$'
    form_note: "exactly 13 digits: epoch MILLISECONDS, never seconds. One length, one meaning — a 10-digit value would be a different unit wearing the same shape, which is the ambiguity `unit` was added to stop."
    establishes: false
    why: "a moment corroborates when something was done and never fixes which being did it. It differs from `gregorian-civil` in one useful way: it carries no offset, so it cannot be misread through a wrong one, as a UTC reading labelled +03 is."
  - system: kelvin-scale
    dimension: temperature
    neighbours: metered
    restrictions: { lines: 1, metered: temperature }
    meaning: "a temperature in kelvins, counted from absolute zero"
    pattern: '^K:\d+(\.\d+)?$'
    form_note: "`K:<kelvins>`"
    example: "K:309.55"
    establishes: false
    why: "a temperature says how hot, never what"
  - system: celsius-scale
    dimension: temperature
    same_ground_as: [kelvin-scale]
    crosswalk: computed
    neighbours: metered
    restrictions: { lines: 1, metered: temperature }
    meaning: "a temperature in degrees Celsius: K = C + 273.15, exactly"
    pattern: '^C:-?\d+(\.\d+)?$'
    form_note: "`C:<degrees>`"
    example: "C:36.4"
    establishes: false
    why: "as for kelvin-scale"
  - system: fahrenheit-scale
    dimension: temperature
    same_ground_as: [celsius-scale]
    crosswalk: computed
    neighbours: metered
    restrictions: { lines: 1, metered: temperature }
    meaning: "a temperature in degrees Fahrenheit: F = C × 9/5 + 32, exactly"
    pattern: '^F:-?\d+(\.\d+)?$'
    form_note: "`F:<degrees>`"
    example: "F:97.5"
    establishes: false
    why: "as for kelvin-scale"
  - system: geographic
    dimension: place
    neighbours: metered
    restrictions: { lines: 3, metered: length }
    meaning: "a position BY COORDINATES, in a named coordinate reference system, on the body that system is fixed to. THE ROOT OF PLACE: every other place system resolves through this one. Named here also because CIVIL TIME RESOLVES THROUGH IT — an offset is a geographic fact wearing a time costume."
    pattern: '^[A-Z][A-Z0-9_]*:[0-9]+(\+[0-9]+)?;-?\d+(\.\d+)?(,-?\d+(\.\d+)?){0,2}(@\d{4}(\.\d+)?)?$'
    form_note: "`<authority>:<code>;<coordinates>[@<epoch>]` — `EPSG:4326;35.6892,51.3890@2026.72`. A COORDINATE IS NEVER BARE: a plain `<lat>,<lon>` names no datum, no axis order and no body, so two readers can disagree by hundreds of metres and neither be wrong. Coordinates in the axis order the system declares; the epoch when the frame is dynamic. A VERTICAL system takes one coordinate (`EPSG:5773;-12.5`), and a COMPOUND one, `<horizontal>+<vertical code>`, three (`EPSG:4326+5773;10.1,20.2,-3.5`)."
    example: "EPSG:4326;35.6892,51.3890@2026.72"
    establishes: false
    why: "a coordinate says where something IS and never which thing it is: two beings can stand in one spot, and one being can move"
  - system: event-anchored
    dimension: any
    datum: named
    neighbours: counted
    meaning: "a position fixed by NEIGHBOURING EVENTS rather than by any coordinate — 'after the branch was pushed, before the cutover'. Fully positioned while carrying no calendar value at all. Declared because it is what makes this a registry rather than a two-item enum: SEQUENCE is the general structure and a coordinate system is one restriction of it."
    pattern: '^(after|before):[^<>]+$'
    form_note: "after:<position> or before:<position> — the position itself, a bean's id or a few words, and never a placeholder in angle brackets; state both as two entries when an interval is meant"
    establishes: false
    why: "an event anchor positions relative to other positions — it fixes an interval, never a point"
  - system: ordinal-number
    dimension: any
    datum: line
    neighbours: counted
    restrictions: { lines: 1, order: total }
    meaning: "a position COUNTED from the first of the line it is read on: `ordinal:1`, `ordinal:2` — the second node of a sequence, the third meeting of a series of them, the fifth seat of a row. Its line gives it its first: a series' or a repetition's `from`. A position standing alone has no line, and names nothing with it"
    pattern: '^ordinal:[1-9][0-9]*$'
    form_note: "`ordinal:` and a whole number from 1: `ordinal:2` — tagged, as a calendar's day is, because a bare number is a port's and a geohash's spelling too"
    example: "ordinal:2"
    establishes: false
    why: "an ordinal number says which of a line's positions, never which being"
  - system: network-segment
    dimension: place
    resolves_through: geographic
    levels: [ { level: network }, { level: segment } ]
    neighbours: counted
    meaning: "WHERE A BEING IS ATTACHED in a network's topology: a VLAN, a wireless network, an address range with a role. A segment is a PLACE (where you are), which is a different question from an address (where you answer) — those have their own registry, and a being keeps its address while moving between segments."
    pattern: '^[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9.:-]*$'
    form_note: "<network>/<segment>, e.g. an office network's guest VLAN or its wireless network for laptops. The network is named because two sites both have a `vlan-13` and they are not the same place."
    establishes: false
    why: "a being moves between segments — a laptop joins the guest network and then the staff one — so a segment corroborates where it is and never fixes which being it is"
  - system: windows-filesystem
    dimension: place
    levels: open
    neighbours: none
    datum: host
    meaning: "a position in ONE NAMED HOST's Windows filesystem. A SEPARATE SYSTEM from unix-filesystem, not a dialect of it: C:\\Users\\user\\source\\repos\\tree and /home/user/tree share no canonical form, and one system carrying two patterns is exactly the reinvention this registry forbids."
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
    establishes: false
    why: "an address names a DELIVERY POINT that is renumbered, renamed and shared — and one building has many"
  - system: local-frame
    dimension: place
    datum: host
    resolves_through: geographic
    neighbours: counted
    meaning: "a position in a frame that TRAVELS WITH ITS HOST: the third floor, room 12, rack 3 slot 7, a deck of a ship. ISO 19111 calls it an engineering system. It is where a thing is WITHIN something, and it keeps its meaning when the something moves — which is exactly what a coordinate does not."
    pattern: '^[a-z0-9][a-z0-9-]*#[^#]+$'
    form_note: "`<host or site>#<position within it>` — `head-office#floor-3/room-12`, `rack-a#u17`"
    example: "head-office#floor-3/room-12"
    establishes: false
    why: "rooms are renumbered and racks re-filled; and the frame itself may be moved"
  - system: along
    dimension: place
    resolves_through: local-frame
    neighbours: metered
    restrictions: { lines: 1, metered: length }
    meaning: "a distance ALONG ONE LINE A BEING LENDS (`lines`): down a core from its top, out along a radius from the pith, along a transect from its first mark. It keeps its meaning when the being moves, as a local frame does, and unlike a position within a frame it has a length"
    pattern: '^[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9-]*\+(0|[1-9][0-9]{0,39})(\.[0-9]{1,40})?$'
    form_note: "`<being>/<line>+<metres>` — `core-b/depth+1.2`, and its zero `core-b/depth+0`: metres always, whatever the resolution held, which is said beside it"
    example: "core-b/depth+0"
    establishes: false
    why: "a distance along a being says where on it, never which being"
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
    why: "codes are re-drawn by the postal operator that issues them, and one code covers many places"
  - system: relative
    dimension: place
    resolves_through: geographic
    neighbours: metered
    restrictions: { lines: 3, metered: length }
    datum: being
    meaning: "a position stated as metres EAST, NORTH and, where it says, UP from another being's own position, on the plane that touches the body there (a topocentric conversion, EPSG method 9837). It resolves through that being's geographic position at the same epoch, and that being must hold one"
    pattern: '^[a-z0-9][a-z0-9-]*\+-?\d+(\.\d+)?,-?\d+(\.\d+)?(,-?\d+(\.\d+)?)?$'
    form_note: "`<bean>+<east>,<north>[,<up>]`, each in metres — `marker-a+3.2,-1.5`"
    example: "marker-a+3.2,-1.5"
    establishes: false
    why: "an offset says where something is from its neighbour, never which thing it is"
  # == DEEP TIME: beyond every calendar's reach ==
  - system: bp-1950
    dimension: time
    neighbours: metered
    restrictions: { lines: 1, metered: time }
    datum: { system: gregorian-civil, at: "1950-01-01", direction: before }
    unit_symbols: { a: annus, ka: kilo-annus, Ma: mega-annus, Ga: giga-annus }
    meaning: "a time BEFORE THE PRESENT, where the present is 1950, the year radiocarbon ages are reported against: beyond every calendar's reach"
    pattern: '^bp1950:\d+(\.\d+)?(a|ka|Ma|Ga)$'
    form_note: "`bp1950:<count><symbol>` — `bp1950:3.93ka`; the symbol names the unit (`unit_symbols`)"
    example: "bp1950:3.93ka"
    establishes: false
    why: "an age says when, never what"
  - system: b2k
    dimension: time
    same_ground_as: [bp-1950]
    crosswalk: computed
    neighbours: metered
    restrictions: { lines: 1, metered: time }
    datum: { system: gregorian-civil, at: "2000-01-01", direction: before }
    unit_symbols: { a: annus, ka: kilo-annus, Ma: mega-annus, Ga: giga-annus }
    meaning: "a time before 2000, the zero an ice-core chronology counts from"
    pattern: '^b2k:\d+(\.\d+)?(a|ka|Ma|Ga)$'
    form_note: "`b2k:<count><symbol>`"
    example: "b2k:3.98ka"
    establishes: false
    why: "as for bp-1950"
  - system: ics-chronostrat
    dimension: time
    levels: [ { level: super-eon }, { level: eon }, { level: era }, { level: period }, { level: sub-period }, { level: epoch }, { level: age } ]
    neighbours: counted
    restrictions: { lines: 1, order: partial }
    cells_in: { registry: ics-chart, take: unit }
    boundaries_in: { registry: ics-gssps, take: boundary }
    same_ground_as: [bp-1950]
    crosswalk: table
    meaning: "a unit of the International Chronostratigraphic Chart: named cells on the line of deep time, each bounded by ages with the margins the chart states. A unit's base is FIXED (`fixing`) by a point in a rock section somewhere on the body, its age a reading of that point, or declared as an age with no point"
    pattern: '^ics:[A-Z][A-Za-z0-9]*$'
    form_note: "`ics:<unit>`, as the chart names it — `ics:Meghalayan`, `ics:CambrianStage2`"
    example: "ics:Meghalayan"
    establishes: false
    why: "a cell says roughly when, never what"
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

# == THE FORM OF EACH REGISTRY: its columns, which every row holds and which it may, and where a column's values come from ==
registry_forms:
  crown: { branch: required, root: optional, meaning: required }
  retired: { name: required, at: required, instead: required }
  senses: { name: required, sense: required }
  natures:
    nature: required
    meaning: required
    crown: required
    establishing_anchor_family: required
    min_establishing_anchors: required
  acts: { act: required, meaning: required, by: optional }
  bodies: { body: required, mean_radius_m: required, authority: required, meaning: required }
  reference_system_kinds: { kind: required, meaning: required }
  reference_frames: { frame: required, meaning: required }
  reference_systems:
    crs: required
    body: { required: true, in: { registry: bodies, take: body }, why: "a reference system is fixed to a body, and a latitude is a latitude ON something" }
    kind: { required: true, in: { registry: reference_system_kinds, take: kind }, why: "the classes ISO 19111 names" }
    frame: { required: true, in: { registry: reference_frames, take: frame }, why: "static or dynamic: whether a coordinate needs an epoch" }
    axes: required
    ensemble_accuracy: optional
    meaning: required
    frame_epoch: optional
  system_registries: { registry: required, key: required }
  anchor_systems:
    system: required
    dimension: required
    levels: optional
    neighbours: optional
    datum: optional
    meaning: required
    pattern: optional
    form_note: optional
    establishes: required
    why: required
    example: optional
    calendar: optional
    reckoning: optional
    day_begins: optional
    resolves_through: optional
    restrictions: optional
    same_ground_as: optional
    crosswalk: optional
    checked_by: optional
    transport: optional
    within: optional
    unit_symbols: optional
    cells_in: optional
    boundaries_in: optional
    overlay: optional
  roles: { role: required, meaning: required }
  operating_systems: { os: required, family: required, path_grammar: required, meaning: required }
  storage_formats: { format: required, layer: required, posix: optional, meaning: required }
  planes: { plane: required, meaning: required }
  net_protocols:
    protocol: required
    technology: { in: { registry: technology, take: code }, why: "a protocol names its entry in the catalogue of technologies, which carries its specification and the field of knowledge it belongs to — so a routing mechanism ledgered tomorrow hangs from the same tree as a mail server does today" }
    layer: required
    positions: optional
    meaning: required
    transport: optional
    default_ports: optional
    rides_on: optional
    synthesizes_link: optional
    plane: optional
    family: optional
    scope: optional
  dimensions: { dimension: required, meaning: required }
  quantities:
    quantity: required
    of: required
    scale: optional
    meaning: optional
    units_from: optional
    crosswalk: optional
  units:
    unit: required
    quantity: { required: true, in: { registry: quantities, take: quantity }, why: "a unit measures a quantity, and the quantity says what it is made of" }
    factor: required
    meaning: required
  leaf_orders:
    order: required
    suffix: optional
    exact: optional
    why: required
    system: optional
    also_systems: optional
    every_calendar: optional
  vacancies: { at: required, position: required, reason: required, why: required }
  figures:
    figure: required
    meaning: required
    requires: required
    extent: required
    extent_why: required
    holds: required
    holds_why: required
    restrictions: optional
    order_values: optional
    ends_values: optional
  accuracy_kinds: { kind: required, meaning: required }
  operations: { op: required, gives: required, takes: required, meaning: required, exact: optional, u_rule: optional }
  aggregates: { aggregate: required, meaning: required }
  placement: { code: required, level: required, parent: optional, takes: optional, meaning: required }
  comparators: { comparator: required, monotone: required, meaning: required }
  ordering_keys: { key: required, meaning: required, inputs: required, steps: required }
  value_types:
    type: required
    system: optional
    unit: optional
    pattern: optional
    refusal: required
    meaning: required
    dimension: optional
    any_system: optional
    exists: optional
    long_form: optional
    clock: optional
    origin: optional
    holds_no: optional
    but: optional
    lines_in: optional
    either: optional
    scheme_from: optional
    separator: optional
    inline_most: optional
    gaps: optional
  gap_tokens: { token: required, gap: required, meaning: required, takes: optional }
  layers:
    layer: required
    files: required
    beneath: { in: { registry: layers, take: layer }, acyclic: true, why: "a layer stands on the one beneath it, and never on itself through others: the chain from the manifesto down to the record" }
    holds: optional
    meaning: required
  methods: { method: required, meaning: required }
  flows:
    flow: required
    from: required
    to: required
    method: required
    grant: required
    why: required
    keeper: optional
    party: optional
    basis: optional
  pass_metadata: { key: required, in: required, meaning: required }
  tool_families: { family: required, meaning: required }
  verbs:
    verb: required
    family: { required: true, in: { registry: tool_families, take: family }, why: "a verb belongs to one family of what the tools are for, and `bin/daftar.py` lists the verbs by it" }
  aspects:
    aspect: required
    meaning: required
    figure: required
    poles: optional
    positions: optional
    lines: optional
    metered: optional
    order: optional
    acyclic: optional
    ends: optional
    domain: optional
    term_key: optional
  registry_files: { registry: required, file: required, key: required, format: optional }
  facets:
    facet: required
    depends_on: { required: true, in: { registry: facets, take: facet }, acyclic: true, rooted: true, why: "a facet depends only on facets the law declares, never on itself through others, and every facet but one reaches that one: the walk they form is the lattice ownership is faceted by, and `legal` is its root" }
    meaning: required
  knowledge_schemes:
    scheme: required
    classifies: required
    holding: optional
    licence: optional
    release: optional
    publisher: required
    url: required
    levels: required
    neighbours: required
    sources: required
    same_ground_as: optional
    crosswalk: optional
    within: optional
    sensitive: optional
    code_pattern: optional
    relations: optional
    labels: optional
  view_lenses: { lens: required, depth: required, form: required, max: required, meaning: required }
  view_archetypes: { archetype: required, meaning: required, when: required }
  gene:
    genos: required
    of_nature: required
    meaning: required
    ownership_form: optional
    identifier_forms: optional
    responsibility_form: optional
    takes_time_of: optional

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
    meaning: "the git wire protocol. It is usually carried — `host-a:git/ledger.git` and `vps-a:tree` are both git over ssh — so its protection is whatever carries it, and the row says so instead of claiming one."
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
    meaning: "the Domain Name System query protocol"
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
    meaning: "PPP over Ethernet: a WAN dial that runs directly on ethernet frames, with no IP transport or port of its own. Like wireguard it MANUFACTURES a link, which is what lets a tunnel name it in `carried_by`."

# == UNITS: the resolution a position is actually held to ==
dimensions:
  - { dimension: time,        meaning: "how long" }
  - { dimension: length,      meaning: "how far" }
  - { dimension: mass,        meaning: "how much matter" }
  - { dimension: information, meaning: "how much can be stored or carried" }
  - { dimension: money,       meaning: "how much value, in a currency" }
  - { dimension: temperature, meaning: "how hot: thermodynamic temperature, an SI base quantity" }
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
  - { quantity: density,      of: { mass: 1, length: -3 } }
  - { quantity: pressure,     of: { mass: 1, length: -1, time: -2 }, meaning: "a force on an area. A gauge pressure — above the air's — says so in its property, never in its unit" }
  - { quantity: volume-flow,  of: { length: 3, time: -1 } }
  - { quantity: plane-angle,  of: {}, meaning: "an angle in a plane: dimensionless and its own kind, as `ratio` and `level` are" }
  - { quantity: temperature-difference, of: { temperature: 1 }, meaning: "how much hotter: the measure of a region of the `temperature` aspect, as a duration is of `time`. A temperature READING is a position on that aspect, never this" }
  - { quantity: number,       of: {}, meaning: "how many things, counted: seats, stems, units of stock. Dimensionless and its own kind, apart from `ratio`, which is a share" }
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
  - { unit: centimetre, quantity: length, factor: [1, 100], meaning: "a hundredth of a metre" }
  - { unit: millilitre, quantity: volume, factor: [1, 1000000], meaning: "a thousandth of a litre" }
  - { unit: kilogram-per-cubic-metre, quantity: density, factor: [1, 1], meaning: "the coherent unit of density" }
  - { unit: gram-per-cubic-centimetre, quantity: density, factor: [1000, 1], meaning: "a gram in a cubic centimetre" }
  - { unit: pascal, quantity: pressure, factor: [1, 1], meaning: "a newton on a square metre" }
  - { unit: kilopascal, quantity: pressure, factor: [1000, 1], meaning: "a thousand pascals" }
  - { unit: millimetre-of-mercury, quantity: pressure, factor: [26664477483, 200000000], meaning: "the conventional millimetre of mercury, 133.322387415 Pa: mercury of density 13.5951 g/cm3 under standard gravity 9.80665 m/s2 (a definition, not one vendor's rounding)" }
  - { unit: cubic-metre-per-second, quantity: volume-flow, factor: [1, 1], meaning: "the coherent unit of a volume flow" }
  - { unit: litre-per-minute, quantity: volume-flow, factor: [1, 60000], meaning: "a litre each minute" }
  - { unit: degree, quantity: plane-angle, factor: [1, 1], meaning: "the coherent unit of plane-angle HERE: a radian is 180/π degrees, and π is no ratio of whole numbers" }
  - { unit: arcsecond, quantity: plane-angle, factor: [1, 3600], meaning: "a 3600th of a degree" }
  - { unit: kelvin, quantity: temperature-difference, factor: [1, 1], meaning: "a step of one kelvin, which is a step of one degree Celsius" }
  - { unit: julian-year, quantity: duration, factor: [31557600, 1], meaning: "365.25 days of 86400 seconds (IAU): a measure of fixed length, never a calendar year" }
  - { unit: annus, quantity: duration, factor: [6311385089, 200], meaning: "31556925.445 seconds (IUPAC-IUGS 2011): the year an age before the present is counted in; a measure of fixed length" }
  - { unit: kilo-annus, quantity: duration, factor: [31556925445, 1], meaning: "a thousand anni" }
  - { unit: mega-annus, quantity: duration, factor: [31556925445000, 1], meaning: "a million anni" }
  - { unit: giga-annus, quantity: duration, factor: [31556925445000000, 1], meaning: "a thousand million anni" }
  - { unit: millimetre-per-julian-year, quantity: speed, factor: [1, 31557600000], meaning: "what a plate or a plateau moves at" }
  - { unit: item, quantity: number, factor: [1, 1], meaning: "one counted thing" }
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
    why: "a release string is absorbed by a more precise one that starts with it and goes on at a component's boundary — a `.`, `-`, `_`, `+` or a space: `9` by `9.4`, never by `90`"
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
      Declared ahead of any occupant because "where does ntfs go" is
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
    why: "A duty two parties hold jointly, under an agreement. The mirror of the vacancy above: a facet answered for jointly arrives with a facet owned jointly, since responsibility pairs with ownership facet by facet."
  - at: "responsibility.entry_one_of"
    position: external
    reason: prediction
    why: "A duty held by a party outside this ledger. NOT an oversight and not symmetric with `owned_by.external`, which IS occupied — a rented VPS's `owned_by.legal` is `external: <provider>`, because the VPS is rented and the provider owns the machine. MODEL.md's rule is exactly this asymmetry: a rented VPS is owned by the provider and ANSWERED FOR by whoever runs it, because a duty must land on a being that can be asked. The position would be occupied by an obligation genuinely borne by an outside party — a provider's SLA that nobody here can be asked about."
  - at: "aspect:feasibility"
    position: necessary
    reason: prediction
    why: "Unavoidability — a being that CANNOT NOT have a capability. Unoccupied because every capability recorded so far is under someone's control, ours or a provider's. It is expected to arrive with the first capability imposed by a substrate that no party can switch off: a VPS provider that re-applies its own network metadata on every boot which is close, but that is provider POLICY and therefore contingent, not necessary."
  - at: "aspect:permission"
    position: omissible
    reason: prediction
    why: "Recording that a being MAY LACK something is low-information until a capability is contested — expected first where an agent might add a capability believing it required, e.g. marking DNSSEC omissible on an internal-only zone so nobody enables it for form's sake."
  # == THE DEFAULT POSITION, VACANT BECAUSE A DEFAULT NO LONGER OCCUPIES ==
  - at: "aspect:necessity"
    position: contingent
    reason: prediction
    why: "A contingent requirement — used but not needed — is the ordinary case for an optional integration, and is expected to arrive with the first one."
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
    why: "Expected and not hypothetical: a ledger's first rule is that it must survive being printed on paper and rescanned, and a codebase can exist as a printed listing or a disk in a drawer. It is the one system deliberately carrying `pattern: none`, so occupying it also exercises the deliberate-absence path."
  - at: "registry:anchor_systems"
    position: geographic
    reason: universal
    why: "THE ROOT OF PLACE (24.0, PLACE): every other place system resolves through it, civil time resolves through it, a position stated from another being is laid on it, and the nearest beings and a place's cells are read from it. Declared whole, whatever a garden has yet placed"
  - at: "registry:anchor_systems"
    position: event-anchored
    reason: universal
    why: "A position fixed only by its neighbours — 'after the call, before the cutover' — carrying no coordinate at all: sequence is the general structure, and a calendar is one restriction of it. Declared whole with the positions it sits beside: `timing.system` is occupied through gregorian-civil and unix-epoch. It is the form every garden needs for a happening whose day nobody said — the forms show it for exactly that — so it is universal, not a prediction: a garden standing on it is not warned."
  - at: "registry:anchor_systems"
    position: network-segment
    reason: prediction
    why: "WHERE A BEING IS ATTACHED in a network — a VLAN, a wireless network, an address range with a role. A segment is a place and not an address. A bean occupies it by stating which segment it is attached to, expected first where one network carries staff, guests and laptops on separate segments and the difference decides what a machine may reach."
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
  - { at: "registry:units", position: centimetre, reason: universal, why: "the measures a body, a sample or a machine is read in — a length, a volume, a density, a pressure, a flow, an angle — declared whole with their exact factors (24.0, step 3) so that no reading waits for its unit, and none is converted to a unit one vendor chose. The quantity machinery they belong to is occupied by every measured value" }
  - { at: "registry:units", position: millilitre, reason: universal, why: "the measures a body, a sample or a machine is read in — a length, a volume, a density, a pressure, a flow, an angle — declared whole with their exact factors (24.0, step 3) so that no reading waits for its unit, and none is converted to a unit one vendor chose. The quantity machinery they belong to is occupied by every measured value" }
  - { at: "registry:units", position: kilogram-per-cubic-metre, reason: universal, why: "the measures a body, a sample or a machine is read in — a length, a volume, a density, a pressure, a flow, an angle — declared whole with their exact factors (24.0, step 3) so that no reading waits for its unit, and none is converted to a unit one vendor chose. The quantity machinery they belong to is occupied by every measured value" }
  - { at: "registry:units", position: gram-per-cubic-centimetre, reason: universal, why: "the measures a body, a sample or a machine is read in — a length, a volume, a density, a pressure, a flow, an angle — declared whole with their exact factors (24.0, step 3) so that no reading waits for its unit, and none is converted to a unit one vendor chose. The quantity machinery they belong to is occupied by every measured value" }
  - { at: "registry:units", position: pascal, reason: universal, why: "the measures a body, a sample or a machine is read in — a length, a volume, a density, a pressure, a flow, an angle — declared whole with their exact factors (24.0, step 3) so that no reading waits for its unit, and none is converted to a unit one vendor chose. The quantity machinery they belong to is occupied by every measured value" }
  - { at: "registry:units", position: kilopascal, reason: universal, why: "the measures a body, a sample or a machine is read in — a length, a volume, a density, a pressure, a flow, an angle — declared whole with their exact factors (24.0, step 3) so that no reading waits for its unit, and none is converted to a unit one vendor chose. The quantity machinery they belong to is occupied by every measured value" }
  - { at: "registry:units", position: millimetre-of-mercury, reason: universal, why: "the measures a body, a sample or a machine is read in — a length, a volume, a density, a pressure, a flow, an angle — declared whole with their exact factors (24.0, step 3) so that no reading waits for its unit, and none is converted to a unit one vendor chose. The quantity machinery they belong to is occupied by every measured value" }
  - { at: "registry:units", position: cubic-metre-per-second, reason: universal, why: "the measures a body, a sample or a machine is read in — a length, a volume, a density, a pressure, a flow, an angle — declared whole with their exact factors (24.0, step 3) so that no reading waits for its unit, and none is converted to a unit one vendor chose. The quantity machinery they belong to is occupied by every measured value" }
  - { at: "registry:units", position: litre-per-minute, reason: universal, why: "the measures a body, a sample or a machine is read in — a length, a volume, a density, a pressure, a flow, an angle — declared whole with their exact factors (24.0, step 3) so that no reading waits for its unit, and none is converted to a unit one vendor chose. The quantity machinery they belong to is occupied by every measured value" }
  - { at: "registry:units", position: degree, reason: universal, why: "the measures a body, a sample or a machine is read in — a length, a volume, a density, a pressure, a flow, an angle — declared whole with their exact factors (24.0, step 3) so that no reading waits for its unit, and none is converted to a unit one vendor chose. The quantity machinery they belong to is occupied by every measured value" }
  - { at: "registry:units", position: arcsecond, reason: universal, why: "the measures a body, a sample or a machine is read in — a length, a volume, a density, a pressure, a flow, an angle — declared whole with their exact factors (24.0, step 3) so that no reading waits for its unit, and none is converted to a unit one vendor chose. The quantity machinery they belong to is occupied by every measured value" }
  - { at: "registry:units", position: kelvin, reason: universal, why: "a step on the temperature line: the measure of a region of the `temperature` aspect, never a reading of it (24.0, step 3). Declared whole with the three scales a reading is written on" }
  - { at: "registry:units", position: julian-year, reason: universal, why: "the fixed-length years deep time and plate motion are counted in — never a calendar year, which varies (24.0, step 3). Declared whole so that an age before the present and a drift of millimetres a year are written in the units their sciences publish in" }
  - { at: "registry:units", position: annus, reason: universal, why: "the fixed-length years deep time and plate motion are counted in — never a calendar year, which varies (24.0, step 3). Declared whole so that an age before the present and a drift of millimetres a year are written in the units their sciences publish in" }
  - { at: "registry:units", position: kilo-annus, reason: universal, why: "the fixed-length years deep time and plate motion are counted in — never a calendar year, which varies (24.0, step 3). Declared whole so that an age before the present and a drift of millimetres a year are written in the units their sciences publish in" }
  - { at: "registry:units", position: mega-annus, reason: universal, why: "the fixed-length years deep time and plate motion are counted in — never a calendar year, which varies (24.0, step 3). Declared whole so that an age before the present and a drift of millimetres a year are written in the units their sciences publish in" }
  - { at: "registry:units", position: giga-annus, reason: universal, why: "the fixed-length years deep time and plate motion are counted in — never a calendar year, which varies (24.0, step 3). Declared whole so that an age before the present and a drift of millimetres a year are written in the units their sciences publish in" }
  - { at: "registry:units", position: millimetre-per-julian-year, reason: universal, why: "the fixed-length years deep time and plate motion are counted in — never a calendar year, which varies (24.0, step 3). Declared whole so that an age before the present and a drift of millimetres a year are written in the units their sciences publish in" }
  - { at: "registry:units", position: item, reason: universal, why: "one counted thing — seats, stems, units of stock — the unit of the `number` quantity (24.0, N22), apart from `ratio`, which is a share. Occupied wherever an amount counts things" }
  - { at: "registry:anchor_systems", position: kelvin-scale, reason: universal, why: "a scale a temperature is READ on (24.0, step 3): the three are declared beside each other so that no scale is the one a reading must be converted to, each crossing to the others by exact arithmetic" }
  - { at: "registry:anchor_systems", position: celsius-scale, reason: universal, why: "a scale a temperature is READ on (24.0, step 3): the three are declared beside each other so that no scale is the one a reading must be converted to, each crossing to the others by exact arithmetic" }
  - { at: "registry:anchor_systems", position: fahrenheit-scale, reason: universal, why: "a scale a temperature is READ on (24.0, step 3): the three are declared beside each other so that no scale is the one a reading must be converted to, each crossing to the others by exact arithmetic" }
  - { at: "registry:facets", position: financial, reason: universal, why: "who pays for a being and is paid by it: in the standard because a stranger's garden expects it beside `legal`, `technical` and `experience`, the facets that are occupied" }
  - { at: "words.form", position: written, reason: universal, why: "an agreement's words, declared whole: written down, spoken aloud, or not yet put into words — the three ways any agreement stands, which a stranger keeping one expects to find. `words` is occupied through `spoken`; `written` is taken the day an agreement's text is kept in a `document`" }
  - { at: "words.form", position: unstated, reason: universal, why: "an agreement's words, declared whole: written down, spoken aloud, or not yet put into words — the three ways any agreement stands, which a stranger keeping one expects to find. `words` is occupied through `spoken`; `unstated` is an agreement that is named and whose terms nobody has put into words yet" }
  - { at: "series.placement", position: point, reason: universal, why: "where a series' row sits, declared whole: at a position, over a region, or at a position and over the stretch back to the row before or on to the next — the four ways an instrument or a hand places what it read" }
  - { at: "series.placement", position: bounds, reason: universal, why: "where a series' row sits, declared whole: at a position, over a region, or at a position and over the stretch back to the row before or on to the next — the four ways an instrument or a hand places what it read" }
  - { at: "series.placement", position: preceding, reason: universal, why: "where a series' row sits, declared whole: at a position, over a region, or at a position and over the stretch back to the row before or on to the next — the four ways an instrument or a hand places what it read" }
  - { at: "series.placement", position: following, reason: universal, why: "where a series' row sits, declared whole: at a position, over a region, or at a position and over the stretch back to the row before or on to the next — the four ways an instrument or a hand places what it read" }
  - { at: "series.entry_one_of", position: grid, reason: universal, why: "the forms a series takes, declared whole: positions by a rule, positions listed, or the whole series kept off git in the held layer — every recorded line is one of the three" }
  - { at: "series.entry_one_of", position: span, reason: universal, why: "the forms a series takes, declared whole: positions by a rule, positions listed, or the whole series kept off git in the held layer — every recorded line is one of the three" }
  - { at: "series.entry_one_of", position: held, reason: universal, why: "the forms a series takes, declared whole: positions by a rule, positions listed, or the whole series kept off git in the held layer — every recorded line is one of the three" }
  - { at: "steps.exit", position: true, reason: universal, why: "a walk's steps, declared whole: a way out, a pause that returns to where it was, and an end nothing follows — the three every case on a walk can meet" }
  - { at: "steps.resumes", position: true, reason: universal, why: "a walk's steps, declared whole: a way out, a pause that returns to where it was, and an end nothing follows — the three every case on a walk can meet" }
  - { at: "steps.final", position: true, reason: universal, why: "a walk's steps, declared whole: a way out, a pause that returns to where it was, and an end nothing follows — the three every case on a walk can meet" }
  - { at: "registry:anchor_systems", position: along, reason: universal, why: "a distance along a line a being lends — down a core, out along a radius, along a transect — the one place position that has a length and travels with its being" }
# == FIGURES: the shapes an aspect may take ==
figures:
  - figure: opposition
    meaning: "a CLOSED figure of contradictory pairs: finite positions, each naming its mutual complement, oriented by one or more axes (the count is derived from `poles`, never assumed)"
    requires: [poles, positions]
    extent: impossible
    extent_why: "the positions are modalities, not points on a line: nothing lies between `necessary` and `possible`, so there is no region to bound"
    holds: impossible
    holds_why: "a position of an opposition is a stance a being takes, and taking it is the whole of the fact: nothing further is held there"
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
    holds: possible
    holds_why: "a position of a sequence may HOLD what was found there — a flow at a moment, a porosity over a stretch of a core, a step a case has reached: a sequence whose positions hold is a series"
# == EXTENT ==
extent_form:
  in:      "optional: the positioning SYSTEM the region is stated in. A system may be metered where its aspect is not (`geographic` in metres), and then the region may carry a measure."
  of:      "the ASPECT whose domain this region lies in. Its figure must declare `extent: possible` — an opposition's positions are modalities with nothing between them, so a region on one is refused rather than silently allowed."
  from:    "optional: the position the region starts at, in the canonical form of one of that aspect's domain systems"
  to:      "optional: the position it ends at"
  lines:   "a region spans as many LINES as its measure's unit has powers of the metered dimension — one for a length, two for an AREA, three for a VOLUME — and never more than the system it is stated in has."
  measure: "optional: { count, unit } — how much of the domain it spans. A METERED aspect only: a stretch of a routine has no length, because `routine` declares `metered: none`, and the unit's dimension must be the one the aspect meters."
  level:   "optional, with `count` and `in`, instead of `measure`: a length counted in CELLS of that level of the system `in` names — a month, two ISO weeks — which a measure cannot say, since a month is 28 to 31 days. Where `from` is stated, the other end is the same place in the cell `count` cells on; where that cell has no such place, its last place, and the reader says so"
  count:   "with `level`: how many cells, a positive whole number"
  requires: "at least one of from / to / measure / level — a region with no bound at either end and no length is not a region; never both `measure` and `level`"
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
    A length in cells of a calendar's level is written `level` and `count` with `in`, and never as a `measure`.

# == RECURRENCE ==
recurrence_form:
  of:     "the SEQUENCE aspect the repetition runs along. An opposition has no neighbours, so nothing on one repeats."
  in:     "optional: the positioning SYSTEM it is counted in. Required by `each`, because a level belongs to its system."
  every:  "{ count } — every Nth NEIGHBOUR: needs only that positions have a next one. Or { count, unit } — every N UNITS: needs the aspect, or the system named, to be metered in that unit's dimension."
  each:   "<level> — the same place in EACH CELL of that level of the system named: each month, each week, each era."
  at:     "optional: where in the cell, as the system writes it — `15`, `W-5` — or a LIST of such places, each an occurrence (`[1, 4]`: the first and fourth day of each week of `iso-week`). Prose to the gate"
  lasts:    "optional: an extent — each occurrence is a REGION that begins at its position and lasts this long (RFC 5545's DTSTART with DURATION)"
  closures: "optional: a list of positions or extents on which no occurrence falls — dated closures, holidays — each in the form of the system named"
  from:   "optional: the position it starts at, in the form of the system named (with no `in:`, of a system the aspect holds), and a day its calendar has"
  to:     "optional: the position it ends at, written as `from` is"
  times:  "optional: how many occurrences in all, the first included — six instalments. With `to`, whichever comes first ends it"
  requires: "exactly one of `every` / `each`"
# == UNCERTAINTY: how well a value is known ==
uncertainty_form:
  u:        "{ count, unit } — the STANDARD uncertainty of the value (JCGM 100:2008, 2.3.1), in a unit of the value's own quantity, or of `ratio` for a relative one. A positive count: a value known exactly states none"
  accuracy: "{ count, unit, kind } — an accuracy AS ITS MAKER STATED IT, with its kind (`accuracy_kinds`), in place of `u`. A reader turns it into u and says that it did; a writer never does"
  where:    "INSIDE a quantity — `{count, unit, u}` or `{count, unit, accuracy}`; BESIDE a value that is not a quantity — a position, a series channel — as that entry's attributes `u` and `accuracy`, in the same two forms, and `u_<axis>` for one axis of a position where its axes are known apart (`u_vertical`)"
  absent:   "a value stating neither is exact as written. A reader combining it prints `u not stated` and invents none"
  requires: "at most one of `u` and `accuracy`"
accuracy_kinds:
  - { kind: bound,     meaning: "a limit the value lies within either way, as its maker states it: the smallest interval, or circle, that holds it (Darwin Core's coordinateUncertaintyInMeters). Read as a rectangular distribution: u = a/√3 per axis (JCGM 100:2008, 4.3.7)" }
  - { kind: radius-68, meaning: "the distance within which the value lies 68 times in 100, as a receiver reports it: one standard uncertainty on one axis, 1.5096 of them for a circular error on two" }
  - { kind: radius-95, meaning: "the distance within which it lies 95 times in 100: 1.96 standard uncertainties on one axis, 2.4477 for a circular error on two" }
  - { kind: unstated,  meaning: "an accuracy its maker gave with no probability: kept as said, and never read as a standard uncertainty" }
# == SELECTIONS: the one reading grammar ==
selection_form:
  inputs: "optional: values a reading takes from outside what the garden holds, one entry each, named, each with its `origin` (`schema_language.origin`). Read by the reader (`{act: read, nature: soma, by: reader}`) — the moment of the reading, from the clock; said by another garden (`{act: said, nature: lekton, by: garden}`) — a value read from it at a commit it published and granted (`garden`, `path`); any other — a value the ASKER gives, in the form `type` or `quantity` states, and the reading's line records it as the asker's, said. Who is asking is such a value until a guard signs the asker in. A step names an input `{input: <name>}`; a reading with an input is read only where the input is given"
  steps:  "the reading, in order: each step applies ONE operation of `operations`, to what earlier steps gave and to the beans the garden holds, with what that operation's row `takes`; the last step's result is the reading's. A step names earlier steps by `id`, or an input by its `name`, and never a later step, so a reading never loops. No formula is written and no string is evaluated"
  zone:   "optional: the civil time zone, a row of `time-zones`, in which a step that groups or compares by a calendar level reads a moment. A step that needs one refuses without it"
  result: "what the last step gives, by its operation's row: a set (of beans, entries or values), a truth (true, false or NOT KNOWN), a value with its u, an order, or groups. Where a truth is asked — a clause's `when`, a checklist's `met_by`, a grant's audience — a set holds when it is not empty, and NOT KNOWN does not hold"
  read:   "READ each time it is asked, by bin/dmreckon.py, and never written back as a fact. An act that fixes a reading — an invoice, a period closed, a verdict — records the commit and the moment it was read at (`pin_form`)"
operations:
  - op: select
    gives: set
    takes:
      genos:   { in: { registry: gene, take: genos }, meaning: "the beans of this genos" }
      of:      { in: { type: kebab }, meaning: "or the members of an earlier step's set" }
      entries: { in: { type: field_path }, meaning: "the entries at this path of each bean selected, instead of the beans" }
      where:   { in: any, meaning: "conditions, each `{path: <field_path>, <comparator>: <operand>}`; a member is selected when it meets every one (`comparators`)" }
    meaning: "the beans, or their entries, that meet every condition"
  - { op: intersect, gives: set, takes: { of: { required: true, in: { type: kebab } }, with: { required: true, in: { type: kebab } } }, meaning: "the members of both sets" }
  - { op: union,     gives: set, takes: { of: { required: true, in: { type: kebab } }, with: { required: true, in: { type: kebab } } }, meaning: "the members of either set" }
  - { op: minus,     gives: set, takes: { of: { required: true, in: { type: kebab } }, with: { required: true, in: { type: kebab } } }, meaning: "the members of the first set that are not in the second" }
  - { op: count,     gives: value, takes: { of: { required: true, in: { type: kebab } } }, meaning: "how many members a set holds — per group, of groups — in the unit `item`" }
  - { op: sum,       gives: value, takes: { of: { required: true, in: { type: kebab } }, path: { required: true, in: { type: field_path } } }, meaning: "the quantities at the path of every member added, exactly, by exact conversion within one quantity; a member whose value is not a quantity is named, and the sum is refused. Per group, of groups" }
  - { op: min,       gives: value, takes: { of: { required: true, in: { type: kebab } }, path: { required: true, in: { type: field_path } } }, meaning: "the least value at the path, and the member that holds it" }
  - { op: max,       gives: value, takes: { of: { required: true, in: { type: kebab } }, path: { required: true, in: { type: field_path } } }, meaning: "the greatest value at the path, and the member that holds it" }
  - { op: order,     gives: order, takes: { of: { required: true, in: { type: kebab } }, path: { required: true, in: { type: field_path } }, direction: { in: [ascending, descending] } }, meaning: "the members in the order of the value at the path, ascending unless it says; ties in the order of their ids" }
  - { op: group,     gives: groups, takes: { of: { required: true, in: { type: kebab } }, path: { required: true, in: { type: field_path } }, level: { in: { type: kebab } }, system: { in: { registry: anchor_systems, take: system, where: { dimension: [time] } } } }, meaning: "the members grouped by the value at the path — or, with `level` and `system`, by the cell of that level the moment at the path falls in, read in the reading's `zone`" }
  - { op: some,      gives: truth, takes: { of: { required: true, in: { type: kebab } }, where: { in: any } }, meaning: "whether some member meets every condition" }
  - { op: all,       gives: truth, takes: { of: { required: true, in: { type: kebab } }, where: { in: any } }, meaning: "whether every member meets every condition; of no members, true" }
  - { op: not,       gives: truth, takes: { of: { required: true, in: { type: kebab } } }, meaning: "the truth reversed; NOT KNOWN stays not known" }
  - op: compare
    gives: truth
    takes:
      of:   { required: true, in: { type: kebab } }
      with: { required: true, in: { type: kebab } }
      is:   { required: true, in: [less, at-most, equal, at-least, greater] }
      band: { in: { quantity: any }, meaning: "with `is: equal`: how far apart they may be and still be equal" }
    meaning: "whether two values stand as `is` says, exactly, by exact conversion within one quantity. With `band`: equal when |Δ| ≤ band and the difference is RESOLVABLE — k·u(Δ) ≤ band, k the law's `compatibility.multiple` — and NOT KNOWN when |Δ| ≤ band and it is not"
  - { op: read, gives: value, takes: { of: { in: { type: kebab } }, path: { required: true, in: { type: field_path } } }, meaning: "the one value at the path — of the one member of an earlier set, or of the bean the reading is read from — with its u; refused when the path holds none or several" }
  - { op: constant, gives: value, takes: { value: { required: true, in: { quantity: any } } }, meaning: "a value the reading states: a band, a limit, an allowance — with its u where it has one" }
  - { op: difference,  gives: value, exact: true,  u_rule: absolute, takes: { of: { required: true, in: { type: kebab } }, with: { required: true, in: { type: kebab } } }, meaning: "the first less the second, one quantity" }
  - { op: multiply,    gives: value, exact: true,  u_rule: relative, takes: { of: { required: true, in: { type: kebab } }, with: { in: { type: kebab } }, coefficient: { in: { type: kebab }, meaning: "a row of `coefficients`" }, count: { in: { type: count } } }, meaning: "the product of the first and one of `with`, `coefficient` or `count`; its quantity is the product of theirs" }
  - { op: divide,      gives: value, exact: true,  u_rule: relative, takes: { of: { required: true, in: { type: kebab } }, with: { required: true, in: { type: kebab } } }, meaning: "the first over the second" }
  - { op: power,       gives: value, exact: whole, u_rule: relative, takes: { of: { required: true, in: { type: kebab } }, exponent: { required: true, in: { type: count } } }, meaning: "the value to a power: exact for a whole exponent, ≈ otherwise" }
  - { op: square-root, gives: value, exact: false, u_rule: relative, takes: { of: { required: true, in: { type: kebab } } }, meaning: "the square root, ≈ unless the value is the square of one" }
  - { op: exp,         gives: value, exact: false, u_rule: derivative, takes: { of: { required: true, in: { type: kebab } } }, meaning: "e to the power of a number with no dimension: a model fitted in logarithms, ≈" }
  - { op: ln,          gives: value, exact: false, u_rule: derivative, takes: { of: { required: true, in: { type: kebab } } }, meaning: "the natural logarithm of a positive number with no dimension, ≈" }
  - { op: convert,     gives: value, exact: true,  u_rule: relative, takes: { of: { required: true, in: { type: kebab } }, unit: { required: true, in: { registry: units, take: unit } } }, meaning: "the value in another unit of its quantity, exactly" }
  - { op: lookup,      gives: value, exact: true,  u_rule: row, takes: { coefficient: { required: true, in: { type: kebab } }, where: { required: true, in: { type: field_path }, meaning: "the code that selects the row" } }, meaning: "the row of `coefficients` a code selects, with its own u" }
  - { op: elapsed,     gives: value, exact: true,  u_rule: resolution, takes: { of: { required: true, in: { type: kebab } }, with: { required: true, in: { type: kebab } }, unit: { required: true, in: { registry: units, take: unit } } }, meaning: "the extent from the second position to the first, of one time system; its u from the resolutions they were written to" }
  - { op: choose,      gives: value, exact: per-row, u_rule: per-row, takes: { computes: { required: true, in: { type: kebab }, meaning: "the property code a row of `mechanisms` computes" }, of: { in: { type: kebab }, meaning: "the being it is read for: an earlier set of one" } }, meaning: "the mechanism whose `valid` covers the case, and of those the one with the smaller validated error; the others print as the spread. None covers it: refused, saying why" }
  - { op: rotate,      gives: value, exact: false, u_rule: derivative, takes: { pole: { required: true, in: { type: kebab }, meaning: "the pole's rows of `coefficients`" }, of: { required: true, in: { type: kebab } } }, meaning: "the velocity, east and north, of a point on a body turning about an axis" }
  - { op: position-to, gives: value, exact: false, u_rule: derivative, takes: { of: { required: true, in: { type: kebab } }, system: { required: true, in: { registry: anchor_systems, take: system, where: { dimension: [place] } } } }, meaning: "a position in another reference system; refused where PROJ is absent" }
  - { op: within,      gives: set,   exact: true,  u_rule: none, takes: { of: { required: true, in: { type: kebab } }, path: { required: true, in: { type: field_path } }, extent: { in: extent }, place: { in: any } }, meaning: "the members whose position or moment at the path lies within the extent, or the place" }
  - { op: apportion,   gives: groups, exact: true, u_rule: none, takes: { of: { required: true, in: { type: kebab } }, amount: { required: true, in: { type: field_path } }, over: { required: true, in: { type: field_path } }, per: { in: { type: kebab } }, level: { in: { type: kebab } }, digits: { in: [true, false] } }, meaning: "each code's part of the members' amounts: each member's amount (at `amount`) shared over its entries at `over` — by an entry's share of its group's shares, the group being the codes under one ancestor at `per` (the scheme's first level where none is named), or by an entry's own amount — summed per code, or per the code's ancestor at `level`. Exact, in fractions. With `digits: true` each part is written in the currency's decimal places, the cents a split leaves over going to the parts with the largest remainders, the first code first — the one rule, so no two readings round a split two ways" }
  - { op: ancestor-at-level, gives: set, exact: true, u_rule: none, takes: { of: { required: true, in: { type: kebab } }, level: { required: true, in: { type: kebab } } }, meaning: "each code's ancestor at a level, by its scheme's `parent`" }
  - { op: neighbour-of, gives: set,  exact: true,  u_rule: none, takes: { of: { required: true, in: { type: kebab } }, relation: { in: { type: kebab }, meaning: "a registry of relations, rows {from, to, rel}" }, distance: { in: { quantity: length } } }, meaning: "the codes a relation's `adjacent` rows name beside each, or the beings within a distance (≈)" }
  - { op: at,          gives: value, exact: per-channel, u_rule: ties, takes: { series: { required: true, in: { type: field_path }, meaning: "`<bean>:<term>.<key>`" }, channel: { in: { type: kebab } }, position: { required: true, in: any } }, meaning: "what a channel holds at a position, as the channel says it is read between rows" }
  - { op: window,      gives: value, exact: per-channel, u_rule: absolute, takes: { series: { required: true, in: { type: field_path } }, channel: { in: { type: kebab } }, extent: { in: extent }, by: { in: { registry: aggregates, take: aggregate } } }, meaning: "what a stretch of the line holds: by one of these, or several as groups" }
  - { op: integral,    gives: value, exact: true,  u_rule: absolute, takes: { series: { required: true, in: { type: field_path } }, channel: { in: { type: kebab } }, extent: { in: extent }, base: { in: any, meaning: "a position on the channel's scale, from which each value is measured" } }, meaning: "the channel summed along the line: a sum's rows added, a point's trapezoids" }
  - { op: rate,        gives: value, exact: per-channel, u_rule: relative, takes: { series: { required: true, in: { type: field_path } }, channel: { in: { type: kebab } }, from: { required: true, in: any }, to: { required: true, in: any } }, meaning: "the change over the distance between two positions of the line" }
  - { op: trend,       gives: value, exact: false, u_rule: least-squares, takes: { series: { required: true, in: { type: field_path } }, channel: { in: { type: kebab } }, extent: { in: extent } }, meaning: "the fitted slope and its u; a slope that does not exceed k·u is never called a motion, and the span that would resolve it is said" }
  - { op: through,     gives: value, exact: true,  u_rule: ties, takes: { series: { required: true, in: { type: field_path } }, channel: { in: { type: kebab } }, position: { required: true, in: any }, back: { in: [true, false] } }, meaning: "a position read across a tie series, forward or back, never beyond the outermost ties" }
  - { op: gaps,        gives: set,   exact: true,  u_rule: none, takes: { series: { required: true, in: { type: field_path } }, channel: { in: { type: kebab } }, extent: { in: extent } }, meaning: "every stretch holding no value, with its reason" }
  - { op: travelled,   gives: value, exact: false, u_rule: derivative, takes: { series: { required: true, in: { type: field_path } }, channel: { in: { type: kebab } } }, meaning: "the length along a channel of positions" }
  - { op: join,        gives: set,   exact: per-channel, u_rule: absolute, takes: { series: { required: true, in: { type: field_path } }, with: { required: true, in: { type: field_path } }, channel: { in: { type: kebab } } }, meaning: "two series row by row: agree, compatible (within k·u), differ, or one only" }
  - { op: weigh,       gives: groups, exact: false, u_rule: none, takes: { weighing: { required: true, in: { key_of: weighings } } }, meaning: "the weights of a weighing's criteria (the principal eigenvector) and its consistency ratio" }
  - { op: used-within, gives: value, exact: true,  u_rule: none, takes: { of: { required: true, in: { type: kebab } }, path: { required: true, in: { type: field_path } }, within: { required: true, in: extent }, at: { required: true, in: any } }, meaning: "the length of the members' extents inside the window of `within` that ends at `at`; where the path holds a position, how many fall inside it" }
  - { op: conservation, gives: truth, exact: true, u_rule: none, takes: { walk: { required: true, in: { type: field_path }, meaning: "a path to a walk's `steps`" }, scheme: { required: true, in: { registry: knowledge_schemes, take: scheme } } }, meaning: "whether each step's `takes` and `gives` conserve every element and the charge, exactly; a substance with no formula is refused" }
comparators:
  - { comparator: is,        monotone: false, meaning: "the value at the path equals the operand: a literal, `{input: <name>}`, or `{step: <id>}` of a value" }
  - { comparator: in,        monotone: false, meaning: "the value is one of a list of operands" }
  - { comparator: at_least,  monotone: false, meaning: "not less than the operand: a number exactly, a quantity by exact conversion, a position through the day, or through the instant in the reading's `zone`" }
  - { comparator: at_most,   monotone: false, meaning: "not more than the operand, read as `at_least` is" }
  - { comparator: exists,    monotone: false, meaning: "the path holds a value" }
  - { comparator: absent,    monotone: false, meaning: "the path holds none" }
  - { comparator: reached,   monotone: true,  meaning: "the course at the path has at some moment held this step of its walk, or a step reachable from it by `next`: what has been reached stays reached" }
  - { comparator: at_step,   monotone: false, meaning: "the course's CURRENT step is this one" }
  - { comparator: refers_to, monotone: false, meaning: "a ref or a bean id at the path names this bean — the caller, a given value" }
mechanism_form:
  mechanism:  "kebab: the row's name, which names its source"
  computes:   "{ property: <scheme>:<code> (a `coding`), quantity, unit } — what it reads"
  inputs:     "[{ name, property: <scheme>:<code>, quantity, unit }] — each converted EXACTLY into the unit the source fitted it in"
  steps:      "the steps of `selection_form`, over the inputs by name"
  valid:      "{ where: [<scheme>:<code>], ranges: [{input, extent}] } — the domain the source fitted; outside it the reader REFUSES, says why, and names what would do"
  residual:   "{ sigma: {count, unit}, form: log | relative | absolute, validated: {count, unit}, persists: per-being | none | unknown } — the source's model error, its VALIDATED error where it states one, and whether one being's error repeats at its next reading; `unknown` is read both ways, and a residual that persists scales a growth too"
  known_bias: "optional prose, as the source states it"
  source:     "{ cite, locator, doi? }"
  terms:      "the terms the row is under, as NOTICE lists them"
coefficient_form:
  coefficient: "kebab"
  count:       "the value"
  unit:        "a unit"
  u:           "optional: its standard uncertainty, or `bounds: [low, high]`"
  where:       "[<scheme>:<code>] — the cases it applies to, each a `coding`"
  convention:  "optional true — fixed by agreement, not measured"
  source:      "{ cite, locator }"
  terms:       "as for a mechanism"
pin_form:
  commit: "the commit a reading was read at: an object id of the garden (7 to 40 hex digits), an ancestor of the commit that records the pin"
  at:     "the moment it was read at (a `position` held to the minute, read by the save): written `now`, and the save writes the moment of its journal heading — the clock a reading that reads the clock took"
  garden: "the `garden` bean of the garden read, where the reading was across gardens"
compatibility:
  multiple: 2
  source: "JCGM 200:2012 (VIM) 2.47: two results are compatible when their difference is 'smaller than some chosen multiple of the standard measurement uncertainty of that difference'"
  applies_to: "two values of ONE measurand that each state u: one property, of one being or part, at one moment, in one quantity"
  never: [count-of-things, money, anchors, codes, names]
  meaning: "what a reading and a merge's report call AGREEMENT within uncertainty. It orders and labels what a person is shown and never decides: two compatible values that differ stay two values, each with its speaker. A garden states another multiple in its VOCAB.md, with its judge named"
ordering_keys:
  - key: merge
    meaning: "a disagreement a merge shows a person: weight × |Δ| / (k · u of Δ) for a measured value, the weight alone for an exact one — after the Contract's classes F, E and D, which no weight reorders"
    inputs: [ { name: weight, origin: { act: said }, quantity: ratio }, { name: delta, origin: { act: said }, quantity: ratio, note: "|Δ|, in the unit of u" }, { name: u, origin: { act: said }, quantity: ratio } ]
    steps:
      - { id: k, op: constant, value: { count: 2, unit: one } }
      - { id: ku, op: multiply, of: u, with: k }
      - { id: z, op: divide, of: delta, with: ku }
      - { id: key, op: multiply, of: weight, with: z }
  - key: tests
    meaning: "a suite in the working loop: weight × how often it failed ÷ its measured seconds; every suite still runs at a release"
    inputs: [ { name: weight, origin: { act: said }, quantity: ratio }, { name: failed, origin: { act: said }, quantity: number }, { name: seconds, origin: { act: said }, quantity: duration } ]
    steps:
      - { id: w, op: multiply, of: weight, with: failed }
      - { id: key, op: divide, of: w, with: seconds }
  - key: controls
    meaning: "a guard: weight × its distance from checked"
    inputs: [ { name: weight, origin: { act: said }, quantity: ratio }, { name: distance, origin: { act: said }, quantity: ratio } ]
    steps:
      - { id: key, op: multiply, of: weight, with: distance }
  - key: improvements
    meaning: "an improvement: weight × the loss it removes, its cost beside"
    inputs: [ { name: weight, origin: { act: said }, quantity: ratio }, { name: loss, origin: { act: said }, quantity: ratio } ]
    steps:
      - { id: key, op: multiply, of: weight, with: loss }
  - key: effort
    meaning: "where a model's effort goes: importance × uncertainty — key items to the best model and a person, the rest to deterministic tools"
    inputs: [ { name: importance, origin: { act: said }, quantity: ratio }, { name: uncertainty, origin: { act: said }, quantity: ratio } ]
    steps:
      - { id: key, op: multiply, of: importance, with: uncertainty }
# == AGGREGATES: what a whole is, made of its parts ==
# == PLACEMENT: the line from place to location, and what a placement takes from where it is placed ==
placement:
  - { code: place,    level: place, meaning: "PLACED — in, at or among another: the ancestor of every placement. It says nothing yet of what is taken" }
  - { code: order,    level: mode,  parent: place, takes: none,  meaning: "among others in an order: a code under its parent, a node on a line. An order has room for any number" }
  - { code: presence, level: mode,  parent: place, takes: none,  meaning: "in a being without taking any of it: a record in a register, a memory in a mind, someone held in a heart" }
  - { code: habitat,  level: mode,  parent: place, takes: share, meaning: "kept by a being that gives it what it runs or rests on: a process on a machine, a repository on a server. It draws a share of what the host holds, and shares may be promised past it" }
  - { code: time,     level: mode,  parent: place, takes: room,  meaning: "at a position in time, a moment or a span: where the span is in a being's own hours — a meeting in the time of those present at it — it takes that time, which they spend on nothing else at once (RFC 5545's OPAQUE); in no one's hours, it takes none (TRANSPARENT)" }
  - { code: location, level: mode,  parent: place, takes: room,  meaning: "at a position in a place system, measured from a datum: a coordinate, a path, an address, a slot. Where the position is in a being's own frame it takes room there, which no other takes at once" }
aggregates:
  - { aggregate: sum,     meaning: "the parts added: two nodes of 2 are 4" }
  - { aggregate: product, meaning: "the parts multiplied: two nodes of 2 are 4 again, three of 2 are 8" }
  - { aggregate: mean,    meaning: "the sum shared equally over the parts: their sum divided by how many they are" }
  - { aggregate: min,     meaning: "the least of the parts" }
  - { aggregate: max,     meaning: "the greatest of the parts" }
  - { aggregate: count,   meaning: "how many parts there are, in the unit `item`: how long an ordinal line is" }
  - { aggregate: first,   meaning: "the part at the line's first position" }
  - { aggregate: last,    meaning: "the part at the line's last position" }
# == VALUE TYPES ==
value_types:
  - type: position
    dimension: time
    unit: day
    any_system: true
    clock: offset
    exists: { reckoning: [arithmetic] }
    long_form: timing
    refusal: "must be a POSITION in time, in the one form of the calendar it is stated in: a day (`2026-09-20`, `persian:1405-06-29`, `hebrew:5787-01-09`, `2026-W38-7`), or a moment to the minute or finer with the offset it was read at (`2026-10-28 14:05-05:00`, `persian:1405-08-06 14:35+01:00`) (Rule 6 paper-durable) — or the same position written long, as one entry of `timing`: `{ system: gregorian-civil, at: 2026-09-20, unit: day }`, or, where nobody said the day, `{ system: event-anchored, at: \"after:<what it followed>\", unit: day, note: <what is known of when> }`"
    meaning: "a POSITION IN TIME, in ANY calendar, held to the unit its form is written at: a day, or a moment to the minute or finer with the offset it was read at — no calendar is the one a position must be in, and a clock reading is never without its offset (`clock: offset`), since civil time is read from a place. `unit` is the coarsest a position is held to; an attribute held to a finer one says so beside the type (`in: { type: position, unit: minute }`), and that unit is also what the save writes for `now`. It is written SHORT, as its calendar writes it, or LONG as one entry of the term `long_form` names — `timing`, `{system, at, unit, by?, note?, where?}` — the same position, which also holds what the short form cannot: a day nobody said, placed by its neighbours (`event-anchored`), who read it, where it was, a note. A day its calendar does not have is no position: where the calendar's row is reckoned in one of the ways `exists.reckoning` names, the day a position names, written back in that calendar, is the position written, and a year the reckoning cannot reach is no year. So it is for every position held to a day — where a repetition starts and ends, a bound of a region in time."
  - type: kebab
    origin: { act: made }
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
  - type: field_path
    origin: { act: said, nature: lekton, by: law }
    pattern: '^(?:@occurrence|(?:[a-z0-9][a-z0-9-]*:)?(?:\*|[a-z0-9_][a-z0-9_-]*)(?:\[[a-z_][a-z0-9_]*=[^\]\s]+\])?(?:\.(?:\*|[a-z0-9_][a-z0-9_-]*)(?:\[[a-z_][a-z0-9_]*=[^\]\s]+\])?)*(?:>(?:\*|[a-z0-9_][a-z0-9_-]*)(?:\[[a-z_][a-z0-9_]*=[^\]\s]+\])?(?:\.(?:\*|[a-z0-9_][a-z0-9_-]*)(?:\[[a-z_][a-z0-9_]*=[^\]\s]+\])?)*)*)$'
    refusal: "must be a path into what beans hold — keys joined by `.`; `*` for every key of a map or entry of a list; `[<attr>=<value>]` for the entries holding that value; `>` to follow a ref to the bean it names and go on there; `<bean>:` first to start at another bean; or `@occurrence`. For example `parties[role=seller].who>title`"
    meaning: "a PATH into a bean's front matter, read by the one reader (bin/dmparse.py `path_read`; evaluated by bin/dmreckon.py). Read from the bean it is read from — the selected member, the occurrence, the bean that declares it — unless it names another. A list is gone into entry by entry. `@occurrence` is the moment an occurrence of an `each` clause entered its selection"
  - type: held_pointer
    pattern: '^root:[a-z0-9][a-z0-9-]*/[0-9a-f]{32}$'
    refusal: "must be `root:<logical root>/<32 lowercase hexadecimal digits>` — a key bin/dmheld.py mints, which says nothing of what it holds"
    meaning: "where material held OFF git is (`held_form`): a logical root each host resolves through its own `roots`, and an opaque key minted at random"
  - type: language_tag
    pattern: '^[a-z]{2,3}(-[A-Z][a-z]{3})?(-([A-Z]{2}|[0-9]{3}))?$'
    refusal: "must be a language as BCP 47 writes one: `fa`, `pt-BR`, `sr-Latn-RS`, `es-419`"
    meaning: "a language, as BCP 47 (RFC 5646) writes it: its language subtag, then its script and its region where they are needed"
  - type: coding
    pattern: '^[a-z0-9][a-z0-9-]*:\S+$'
    scheme_from: knowledge_schemes
    refusal: "must be a CODE WITH ITS SCHEME, written `<scheme>:<code>` — `isco-08:2522`, `technology:samba`, `analytic:orchard` — the scheme a row of `knowledge_schemes` and the code one of its codes"
    meaning: "a CODE OF A SCHEME, written with the scheme it is a code of: `<scheme>:<code>`. One capsule wherever a code is written — what an observation is of and what it found, what a step is and takes, what a channel holds, what a stance covers, where an amount belongs, what a being draws on, an identity assigned outside every garden. The scheme is a row of `knowledge_schemes`; the code is one of its codes, looked up where the scheme is held here and held to its form where it is held at its authority. The first colon ends the scheme, whose name has none."
  - type: rows
    separator: "\t"
    inline_most: 100
    gaps: gap_tokens
    refusal: "is not a table in its one form: a header line naming each column once, then one line per row, as many cells as the header, one tab between two, each line ending in a line feed alone — no empty line, no empty cell, no cell beginning or ending in a space. A value nobody read is a gap token (`gap_tokens`), never a blank"
    meaning: "a TABLE of rows, written in a bean as a block (`rows: |`): text, with one tab between two cells. What a cell means is its column's; a cell that holds no value says why, with a gap token. It is read and written by one reader and one writer, byte for byte, and a table of more than `inline_most` rows is warned about: its rows belong in the parts of a file"
# == GAP TOKENS: a cell that holds no value says why ==
gap_tokens:
  - { token: "-", gap: not-read,   meaning: "no reading was made here" }
  - { token: "?", gap: unreadable, meaning: "a reading was made, and it cannot be read here" }
  - { token: "<", gap: below,      takes: count, meaning: "below a limit: `<` and the limit's count, or a bare `<` for the channel's `limits.below`" }
  - { token: ">", gap: above,      takes: count, meaning: "above a limit, as `<` is below one" }
  - { token: "_", gap: absent,     meaning: "there is nothing here to read: a core not recovered, a ring never formed" }
  - { token: "#", gap: withheld,   meaning: "a value exists, and this copy does not carry it" }
# == THE JOURNAL ==
journal:
  path: log/journal.md
  heading_form: "## <when> · <who> · <what> — <when> in a declared calendar's own form, to the minute, with its offset (`2026-09-20 15:07+03:00`, `persian:1405-06-29 15:37+03:30`)"
  system: any
  unit_at_least: minute
  checks: added
  origin: { heading: { act: read, nature: soma, by: save } }
# == HELD: what a garden keeps off git ==
held_form:
  entry:   "an ENTRY of any term whose value is a list or an open map may be SEALED: `{held: <held_pointer>, basis?, until?}` and nothing else, in place of its attributes. The whole entry, its declaration included, is in the held layer; git keeps only this"
  key:     "in an open map, a sealed entry's key is `h-` and the first eight digits of its pointer's key: a key says nothing either"
  basis:   "a ref to what it is held on: the subject's own consent, an agreement. Required on a bean `about` any person but the gardener"
  until:   "optional: the day by which it is to be erased (a date); bin/dmheld.py warns before it"
  journal: "a commit that seals or erases an entry records it in one line, `- held: <bean> <key> added` or `erased`, which bin/dmheld.py writes, and says no more of it"
  never:   "the gate never reads a store: a store is checked where it is, by bin/dmheld.py and by the save — a gate that fails on one machine and passes on another is a gate people disable (sv:42)"
# == LAYERS: where material sits, and what stands on what ==
layers:
  - layer: manifesto
    files: true
    beneath: law
    holds: [MANIFESTO.md]
    meaning: "what daftar holds to, one clause to a sentence, read alone; the law carries it and names the clause it carries, and nothing else applies it"
  - layer: law
    files: true
    beneath: reasoning
    holds: [seed/std-vocab.md, VOCAB.md, GARDEN.md, MODEL.md, CHECKLIST.md, MERGE.md, seed/LANGUAGE, seed/RELEASE-SIGNERS,
            seed/PUBLIC-ALLOW, "seed/knowledge/*", seed/LICENSE.md, "seed/LICENSE-*"]
    meaning: "what is in force, in the present tense, applied alone: the vocabulary, a garden's own terms and its manifest, the model, the way a write is made, the merge, what a release ships and the keys it is signed with, the published classifications, and the terms the release's files are under"
  - layer: reasoning
    files: true
    beneath: journal
    holds: [seed/RATIONALE.md, RATIONALE.md]
    meaning: "why a law is as it is, keyed by the path of the item it supports"
  - layer: journal
    files: true
    beneath: history
    holds: [log/journal.md, seed/CHANGELOG.md]
    meaning: "what was done and why, entry by entry, appended and never rewritten"
  - layer: history
    files: true
    holds: ["captures/*"]
    meaning: "the exact record a journal is written from: the commits themselves, and the copies a bean points at; never summarised"
  - layer: queue
    files: true
    holds: [log/pending.md]
    meaning: "what waits for a person: proposed, parked and settled in place, and edited as it moves"
  - layer: guide
    files: true
    holds: [README.md, AGENTS.md, seed/README.md, seed/WELCOME.md, seed/COOKBOOK.md, seed/FORMS.md, "seed/*.template",
            "assets/*/README.md", "assets/*/templates/*"]
    meaning: "a way in for a reader: a reading order, a recipe, a form, an asset's guide and its templates; a value in one is an example's, never a fact"
  - layer: estate
    files: true
    holds: ["beans/*", "mappings/*", "series/*", "extracts/*"]
    meaning: "a garden's facts about what it keeps, each saying who said it and how they know, and the rows of its series and of the schemes it holds as extracts"
  - layer: gate
    files: true
    holds: ["bin/*", "test/*", "seed/germinate.*", .gitattributes, .gitignore, "assets/*/bin/*", "assets/*/lib/*"]
    meaning: "the law applied: the gate, the tools that read the law, an asset's code, the tests that hold them, and the repository's own settings"
  - layer: words
    files: true
    meaning: "a person's own words, or a document they gave. A garden places them, by a `standing` entry on a bean a person's own record carries (`asserted-by-human`): only a person makes material their words, and a tool or an agent cannot"
  - layer: work
    files: true
    meaning: "an agent's own plan, notes, handover or report; a garden places them"
  - layer: instructions
    files: false
    meaning: "what the person an agent works for asked of it, in one session"
  - layer: world
    files: false
    meaning: "what is read off the world outside a garden: a machine, a service, a command's output"
  - layer: clock
    files: false
    meaning: "the moment, read from the clock by a tool"
  - layer: self
    files: false
    meaning: "a model's own output, before anything records it"
  - layer: request
    files: false
    meaning: "what one request to a model holds"
  - layer: remote
    files: false
    meaning: "a party outside a garden that material is sent to: a hosted model, a service"
  - layer: public
    files: false
    meaning: "a public repository, where a garden's own material never goes"
  - layer: other-garden
    files: false
    meaning: "another garden, written only by its own gardener"
  - layer: held
    files: false
    meaning: "material a garden keeps OFF git — a document's bytes, a sealed entry, a series — in a store a host resolves through its `roots`, pointed at from a bean by a `held_pointer`; erasable per subject, and backed up on its own"
# == THE TOOLS, BY WHAT THEY ARE FOR: one entry, `bin/daftar.py <verb>`, and the family each verb belongs to ==
tool_families:
  - { family: law,     meaning: "read the law: its rules, its reasons, a term's form, the catalogue of its parts" }
  - { family: gate,    meaning: "judge: the gate, and the guards that run it where writes arrive" }
  - { family: write,   meaning: "make a change: a save with its journal entry, safe edits, sessions, the release adopted" }
  - { family: read,    meaning: "read the garden: its documents, a reading, what is owed, what has aged, where a thing is" }
  - { family: measure, meaning: "place and quantity: calendars, coordinates, units, published knowledge and its crosswalks" }
  - { family: between, meaning: "between gardens and places: proposals, merges, readings across, what passes where, what is held" }
  - { family: launch,  meaning: "daftar's own loop: a model called with every request logged" }
verbs:
  - { verb: rules,     family: law }
  - { verb: why,       family: law }
  - { verb: form,      family: law }
  - { verb: forms,     family: law }
  - { verb: catalog,   family: law }
  - { verb: review,    family: law }
  - { verb: facets,    family: law }
  - { verb: check,     family: gate }
  - { verb: parse,     family: gate }
  - { verb: public,    family: gate }
  - { verb: hook,      family: gate }
  - { verb: hub,       family: gate }
  - { verb: save,      family: write }
  - { verb: safe,      family: write }
  - { verb: journal,   family: write }
  - { verb: session,   family: write }
  - { verb: cursor,    family: write }
  - { verb: digest,    family: write }
  - { verb: upgrade,   family: write }
  - { verb: reform,    family: write }
  - { verb: install,   family: write }
  - { verb: garden,    family: read }
  - { verb: reckon,    family: read }
  - { verb: ledger,    family: read }
  - { verb: pos,       family: read }
  - { verb: seq,       family: read }
  - { verb: stale,     family: read }
  - { verb: where,     family: read }
  - { verb: cal,       family: measure }
  - { verb: geo,       family: measure }
  - { verb: units,     family: measure }
  - { verb: knowledge, family: measure }
  - { verb: crosswalk, family: measure }
  - { verb: propose,   family: between }
  - { verb: merge,     family: between }
  - { verb: across,    family: between }
  - { verb: pass,      family: between }
  - { verb: held,      family: between }
  - { verb: launch,    family: launch }
# == THE FLOW LAW: which passes between layers are granted ==
methods:
  - { method: edit,      meaning: "a writer changes a file, by hand or through a tool at the writer's word" }
  - { method: take-down, meaning: "a person's words put into a said value. How the words were carried is the pass's `form`, one of `words.form`'s own: written or spoken" }
  - { method: stamp,     meaning: "the save writes the clock's reading where `now` stood" }
  - { method: append,    meaning: "an entry added after the last, and nothing before it changed" }
  - { method: derive,    meaning: "a tool computes a value from the inputs it names" }
  - { method: record,    meaning: "a tool writes what it read off the world, with the reading's moment" }
  - { method: capture,   meaning: "a command's output kept as it came, its owner and its command named" }
  - { method: merge,     meaning: "the merge engine joins two copies of one being, keeping each value's source" }
  - { method: hold,      meaning: "material sealed into a store off git, git keeping only its pointer" }
  - { method: take,      meaning: "a peer's proposal read and taken in, its fingerprint recorded; the gardener's commit ratifies it" }
  - { method: make,      meaning: "a proposal made for a peer, from what the garden making it says" }
  - { method: pass-on,   meaning: "what a garden holds from another, made for a third, the passing garden's id appended to its path" }
  - { method: upgrade,   meaning: "a release's files laid into a garden, by germination or an upgrade" }
  - { method: publish,   meaning: "material pushed, or offered for merging, to a public repository" }
  - { method: render,    meaning: "material placed into a request to a model" }
  - { method: show,      meaning: "a tool prints material to whoever runs it" }
  - { method: send,      meaning: "material sent to a party outside the garden" }
  - { method: serve,     meaning: "a page or an action served to a viewer" }
flow_form:
  flow:   "the row's name, kebab, no other row's"
  from:   "the SOURCE: a layer, or a list of layers"
  to:     "the DESTINATION: a layer, or an origin `{act, nature?, by?}` — a value placed in the estate at a position of that origin. A row naming an origin is nearer than one naming a layer, and the more of `act`, `nature` and `by` it names, the nearer still"
  method: "a method, or a list of them"
  grant:  "granted | refused | ratified — `ratified` is refused until the gardener grants a named party, by a row of a garden's own `flows` (a RULE-CHANGE) with `party` and `basis`"
  keeper: "optional: `release` — the row holds only for a file the release keeps"
  why:    "why the row is as it is, in the present tense"
  closed: "a pass no row holds is REFUSED. Of the rows that hold a pass, the nearest decides, and of two as near, a refusal. A garden's own rows only add refusals, or grant a party where the standard says `ratified`: a garden never unguards the standard"
  guard:  "how far a row is guarded is COMPUTED, never typed: from the tools that say they check it (a tool's `GUARDS`) and where each runs — at every commit where the pre-commit hook runs it, at a push where the pre-push hook does, otherwise in that tool alone — and `hoped` where no tool checks it. A row checked at one release is checked at the next (bin/dmpass.py --flows)"
flows:
  - { flow: words-to-said, from: [words, instructions], to: { act: said }, method: take-down, grant: granted,
      why: "a said value's source is a person's words: a document they gave, or what they asked, recorded with who said it" }
  - { flow: law-owned, from: [law, guide, estate, words, instructions, work, self], to: { act: said, by: law }, method: [edit, take-down], grant: granted,
      why: "a value the law owns — a registry's row, a closed list's word — is judged by the schema alone, whatever page it was read on" }
  - { flow: model-output-is-no-word, from: [self, work], to: { act: said }, method: [edit, take-down, derive], grant: refused,
      why: "a model's own output, or an agent's own notes, is no one's words: a said value the agent wrote on its own say is a guess" }
  - { flow: examples-are-not-facts, from: guide, to: estate, method: [edit, take-down, derive, record], grant: refused,
      why: "a value in a guide is an example's: a name, a day or an amount copied from one into a bean is a fact nobody gave" }
  - { flow: copied-is-not-said, from: estate, to: { act: said }, method: edit, grant: refused,
      why: "a value copied from another bean has that bean for its source, not a person: it is cited in `from` and derived" }
  - { flow: derived, from: [estate, law, words, world, clock, history, other-garden], to: { act: derived }, method: [derive, merge], grant: granted,
      why: "a value computed from inputs it names is as strong as its weakest input" }
  - { flow: made-here, from: [self, work, instructions, words], to: { act: made }, method: edit, grant: granted,
      why: "prose, and a name minted, are made where they are written" }
  - { flow: clock-to-stamped, from: clock, to: { act: read, by: save }, method: stamp, grant: granted,
      why: "the save reads the clock and writes the reading, as it writes the journal heading beside it" }
  - { flow: stamped-is-not-typed, from: [self, work, words, instructions, guide, estate], to: { act: read, by: save }, method: [edit, take-down], grant: refused,
      why: "a day the save reads is never typed: a typed day is a guess, or a copy of an example's" }
  - { flow: world-read, from: world, to: { act: read }, method: [record, edit], grant: granted,
      why: "a reading of a machine, a service or a run, recorded by whoever took it, with its moment" }
  - { flow: world-captured, from: world, to: history, method: capture, grant: granted,
      why: "a command's output is kept as it came, with its owner and its command, so it can be taken again and compared" }
  - { flow: run-observed, from: history, to: { act: said }, method: record, grant: granted,
      why: "a result a captured run printed, a suite's verdict at a commit, is recorded as an observation that points at its capture, by a journalled save: the capture is the reading, and can be read again" }
  - { flow: merged, from: [estate, other-garden], to: estate, method: merge, grant: granted,
      why: "two copies of one being are joined with every value's source kept, and a subsumed value kept beside the winner" }
  - { flow: peer-taken, from: other-garden, to: estate, method: take, grant: granted,
      why: "import: authenticity is the receiver's, about the peer it met; what the peer said crosses one hop, the path recorded" }
  - { flow: peer-copied, from: other-garden, to: estate, method: edit, grant: refused,
      why: "another garden's facts come in through a proposal taken, whose fingerprint is recorded, never as a hand copy nobody can trace" }
  - { flow: peer-offered, from: estate, to: other-garden, method: make, grant: granted,
      why: "export: a person's name crosses only where their word reaches, and nothing is sold" }
  - { flow: peer-written, from: [estate, self, work], to: other-garden, method: edit, grant: refused,
      why: "another garden is written only by its own gardener: what this one would give it is a proposal" }
  - { flow: transit, from: other-garden, to: other-garden, method: pass-on, grant: granted,
      why: "transit: passed on as it came, the passing garden's id appended to the path; a path that holds the receiver is a loop" }
  - { flow: sealed, from: estate, to: held, method: hold, grant: granted,
      why: "material that must not sit in git is kept off it, where it can be erased per subject" }
  - { flow: unsealed, from: held, to: [estate, public, other-garden], method: [edit, make, publish], grant: refused,
      why: "sealed material comes back into git, or out of the garden, only as its pointer" }
  - { flow: sealed-read, from: held, to: request, method: [render, show], grant: ratified,
      why: "sealed material is read into a request only where the gardener grants it" }
  - { flow: journalled, from: [work, instructions, self, history], to: journal, method: append, grant: granted,
      why: "what was done and why is appended, entry by entry, beside the commit that did it" }
  - { flow: journal-rewritten, from: [work, instructions, self, history, journal], to: journal, method: edit, grant: refused,
      why: "a journal is appended and never rewritten: an entry changed after the fact is a record nobody can trust" }
  - { flow: queued, from: [work, instructions, self], to: queue, method: edit, grant: granted,
      why: "what waits for a person is proposed, parked and settled in place" }
  - { flow: law-ratified, from: [instructions, words], to: [law, manifesto], method: edit, grant: granted,
      why: "a change to the law is ratified by a person, and said distinctly as a RULE-CHANGE" }
  - { flow: story-in-law, from: [journal, history, reasoning, work], to: [law, manifesto], method: edit, grant: refused,
      why: "the law is applied alone, in the present tense: a story or a reason in it leans on a layer beneath" }
  - { flow: law-restated, from: law, to: [reasoning, guide, journal], method: edit, grant: refused,
      why: "a second statement of a rule disagrees with the first in time; a form is derived from the law, never copied" }
  - { flow: law-derived, from: law, to: guide, method: derive, grant: granted,
      why: "a form or a list is derived from the law by a tool, so it cannot disagree with it" }
  - { flow: released, from: public, to: [law, manifesto, reasoning, guide, gate, journal], method: upgrade, grant: granted,
      why: "a release's files are laid into a garden whole, and the commit says RULE-CHANGE" }
  - { flow: release-in-estate, from: public, to: estate, method: upgrade, grant: refused,
      why: "a release carries no garden's facts" }
  - { flow: kept-private, from: [estate, words, work, instructions, journal, queue, history, self], to: public, method: publish, grant: refused,
      why: "a garden's own material never goes to a public repository" }
  - { flow: release-public, from: [manifesto, law, reasoning, guide, gate], to: public, method: publish, grant: granted, keeper: release,
      why: "what the release keeps is public under its licences" }
  - { flow: composed-here, from: [manifesto, law, reasoning, journal, history, queue, guide, estate, gate, words, work, instructions, self], to: request, method: [render, show], grant: granted,
      why: "a request composed on this host keeps what it holds on this host, the model's own earlier turns among it" }
  - { flow: sent-out, from: [request, estate], to: remote, method: send, grant: ratified,
      why: "a hosted or remote party is refused until the gardener grants that party, with the basis the gardener's own law asks for sending there" }
  - { flow: served, from: estate, to: remote, method: serve, grant: granted,
      why: "a page or an action is served only to a viewer a grant opens it to, asked before each one" }
pass_form:
  from:        "where material came from, as a row's `from` names a layer: `{file: <path>}` (its layer is the map's), `{bean: <id>, at?: <dotted path>}` (the estate), `{garden: <id>}` (another garden), or `{layer: <a layer that holds no files>}`"
  to:          "where it went, in the same forms, as a row's `to`; a value is `{bean, at}`, and its position's origin is what the flow law judges"
  method:      "a row of `methods`"
  metadata:    "only counts, locators and git object ids, from `pass_metadata`: never the material — a day or an amount is not hidden by a hash, and is in the bean anyway"
  keys:        "a pass holds these four and nothing else"
  log:         "a session's passes, one JSON object to a line, in a file under `captures/passes/` that a session bean's `pass_log` names; it only grows"
  claim:       "a commit that stages a change to a pass log CLAIMS its session, and owes: the log extends the copy at HEAD; every pass it adds is one the flow law grants; every said value the commit adds to a bean has a pass whose `to` is that value; and a record `asserted-by-human` it adds has a pass from `words` or `instructions` into its bean. A commit that claims nothing owes none of it, and for it those rows are `hoped`"
  pointer:     "a value's own source, where one is kept: `provenance_of.<path>[].at` beside the value it names, or a record's `from[].at`, in the forms `provenance_record` gives. Where present it must resolve in the tree committed, and the flow law judges its layer against the value's origin; a value with none is `unrecorded`, and nothing is guessed for it"
pass_metadata:
  - { key: characters, in: count, meaning: "how long the material was, counted in characters" }
  - { key: seq,    in: count,  meaning: "the pass's place in its session, where the log's order is not enough" }
  - { key: turn,   in: count,  meaning: "the turn of the session it happened in" }
  - { key: oid,    in: oid,    meaning: "the git object id of the material, as `git hash-object` gives it" }
  - { key: form,   in: form,   meaning: "how a person's words were carried: a word of `words.form`" }
  - { key: party,  in: bean,   meaning: "the bean of the party it went to, where it left the garden" }
  - { key: quoted, in: count,  meaning: "how often the value a pass carries was found, as written, in its source; 0 where it was found nowhere quoted, and the pass is HOPED: the words may say it another way" }
  - { key: distinct, in: count, meaning: "how many of those finds were by a part of the value that names one thing — a day, an amount of three digits or more, eight characters or more; 0 where every find was by a short word or a small number, which is in everything: the attribution is weak" }
aspects:
  - aspect: necessity
    meaning: "what a being requires in order to do its work"
    figure: opposition
    poles: [[necessary, contingent], [possible, impossible]]
    positions:
      - { position: necessary,  complement: contingent, meaning: "without it the being cannot do its work at all" }
      - { position: contingent, complement: necessary,  meaning: "the being uses it, but could do its work without it" }
      - { position: possible,   complement: impossible, meaning: "the being could take it; nothing forbids it" }
      - { position: impossible, complement: possible,   meaning: "the requirement exists but the recorded target CANNOT satisfy it. Distinct from an ABSENT edge: a missing backup is a gap, while a backup that cannot work is worse, because the record makes it look present: a domain's backup MX record that names its own primary." }

  - aspect: permission
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

  - aspect: fixing
    meaning: "what fixes a boundary on a line: a mark in a being, or a value stated on the line itself"
    figure: opposition
    poles: [marked, declared]
    positions:
      - { position: marked,   complement: declared, origin: { act: read, nature: soma }, meaning: "fixed by a MARK in a being — a point in a rock section, a monument, a benchmark. The mark is the boundary; its value on the line is a reading of the mark, and a better reading moves the value and never the boundary" }
      - { position: declared, complement: marked,   origin: { act: said, nature: lekton }, meaning: "fixed by stating its value on the line: nothing in the world marks it, and a place named beside it is a reference, not the definition" }

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
    metered: length
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
  - aspect: ordinal
    meaning: "which in order: a position on the ORDINAL line — the first, the second — with nothing between two neighbours. It says which, never how many (a count is how many), and it is no time and no place, so what lies on it holds at none of them: two nodes of 2 whose whole is 4"
    figure: sequence
    lines: 1
    metered: none
    order: total
    acyclic: true
    ends: open-end
    domain: { systems: any }
  - aspect: temperature
    meaning: "how hot: a position on the one line of thermodynamic temperature, bounded below by absolute zero"
    figure: sequence
    lines: 1
    metered: temperature
    order: total
    acyclic: true
    ends: open-end
    domain: { systems: temperature }

# == PROFILES ==
# == KNOWLEDGE: published classifications as UNIVERSAL ANCHORS ==
registry_files:
  - { registry: isced-f-2013, file: seed/knowledge/isced-f-2013.tsv, key: code }
  - { registry: isco-08,      file: seed/knowledge/isco-08.tsv,      key: code }
  - { registry: technology,   file: seed/knowledge/technology.tsv,   key: code }
  - { registry: crosswalk-isco-08-isced-f-2013, file: seed/knowledge/crosswalk-isco-08-isced-f-2013.tsv, key: isco_08 }
  - { registry: currencies,   file: seed/knowledge/currencies.tsv,   key: code }
  - { registry: time-zones,  file: seed/knowledge/time-zones.tsv,  key: zone }
  - { registry: ics-chart,   file: seed/knowledge/ics-chart-2026-06.tsv, key: unit }
  - { registry: ics-gssps,   file: seed/knowledge/ics-gssps-2026-09.tsv, key: boundary }
  - { registry: substances,  file: seed/knowledge/substances.tsv,  key: code }
  - { registry: mechanisms,  file: seed/knowledge/mechanisms.yaml, key: mechanism, format: yaml }
  - { registry: crosswalk-fhir-r5-observation, file: seed/knowledge/crosswalk-fhir-r5-observation.tsv, key: fhir }
  - { registry: crosswalk-dwc, file: seed/knowledge/crosswalk-dwc.tsv, key: dwc }
  - { registry: coefficients, file: seed/knowledge/coefficients.yaml, key: coefficient, format: yaml }
# == FACETS: the aspects of ownership, one owner and one holder each ==
facets:
  - { facet: legal,      depends_on: [],      meaning: "who owns it in law, and answers for it there. Every other facet reaches it through `depends_on`" }
  - { facet: technical,  depends_on: [legal], meaning: "who runs and maintains it" }
  - { facet: experience, depends_on: [legal], meaning: "who designs how people meet it — its words, flows and look — and whose judgment of that decides" }
  - { facet: financial,  depends_on: [legal], meaning: "who pays for it and is paid by it" }
knowledge_scheme_form:
  holding:      "shipped | extract | at-authority — how its codes are held: shipped with the release in seed/knowledge/; a garden's own extract in extracts/, each edit a journalled write and not a RULE-CHANGE (F9); or held at the publisher and looked up there, checked here only by `code_pattern`"
  licence:      "the SPDX identifier of the terms its rows are under — `LicenseRef-<name>` where the publisher's terms have none"
  release:      "the publisher's release the rows are from"
  sensitive:    "special-category — every code of it is special-category material wherever it is written (a diagnosis, a procedure; F3); absent, not"
  code_pattern: "with `at-authority`: the form a code must take, a regular expression"
  relations:    "a registry of relations between its own codes, rows {from, to, rel}, `rel` one of part-of, requires, adjacent (N23); resolved by the `registry_links` rows the garden declares for it"
  labels:       "[{language, registry, attribution?}] — its labels in another language: a registry of {code, name} rows, and the words its publisher asks to be printed with them, verbatim (N25)"
knowledge_schemes:
  - scheme: isced-f-2013
    classifies: fields of knowledge (education and training)
    holding: shipped
    licence: CC-BY-SA-3.0-IGO
    release: "ISCED-F 2013 (field descriptions 2015)"
    publisher: UNESCO Institute for Statistics
    url: "https://uis.unesco.org/en/topic/international-standard-classification-education-isced"
    levels: [ { level: broad }, { level: narrow }, { level: detailed } ]
    neighbours: none
    sources: seed/knowledge/SOURCES.md
  - scheme: isco-08
    classifies: occupations
    holding: shipped
    licence: LicenseRef-ILO-ISCO-08
    release: "ISCO-08 (structure, 2012)"
    publisher: International Labour Organization
    url: "https://ilostat.ilo.org/methods/concepts-and-definitions/classification-occupation/"
    levels: [ { level: major }, { level: sub-major }, { level: minor }, { level: unit } ]
    same_ground_as: [isced-f-2013]
    crosswalk: table
    neighbours: none
    sources: seed/knowledge/SOURCES.md
  - scheme: substances
    classifies: substances by their chemical formula, for walks whose steps take and give them
    holding: shipped
    licence: CC0-1.0
    publisher: daftar (curated; each row a formula in Hill notation, a fact)
    url: "seed/knowledge/substances.tsv"
    levels: [ { level: substance } ]
    neighbours: none
    sources: seed/knowledge/SOURCES.md
  - scheme: technology
    classifies: established technologies (software, protocols, operating systems), each with its OFFICIAL documentation
    holding: shipped
    licence: CC-BY-4.0
    publisher: daftar (curated; every row names the project's own documentation, never a third party's)
    url: "seed/knowledge/technology.tsv"
    levels: [ { level: technology } ]
    within: [isced-f-2013]
    neighbours: none
    sources: seed/knowledge/SOURCES.md
  - scheme: placement
    classifies: how one being is placed in, at or among another — from the most general to the most bodily, each rung saying what a placement takes from where it is placed
    holding: shipped
    licence: CC-BY-4.0
    publisher: daftar (the law's own registry, `placement`)
    url: "seed/std-vocab.md"
    levels: [ { level: place }, { level: mode } ]
    neighbours: none
    sources: seed/RATIONALE.md
# == VIEW: the registries only the `view` profile reads ==
view_lenses:
  - { lens: orient,     depth: 0, form: story,        max: { stages: 5, words_per_stage: 14 },
      meaning: "what the drawn thing does and what it is built from, for someone who has never touched it: its purpose, three to five stages in the order work flows, its outcome, and each technology's own documentation. No address, port or live value" }
  - { lens: understand, depth: 1, form: schematic,    max: { elements: 18 },
      meaning: "how the parts co-operate, where the work is decided and where it is fragile: parts by what they do, flows as verbs, decisions as gates, boundaries where ownership or network changes. No live value, and no address unless the page is private (`view.visibility`)" }
  - { lens: operate,    depth: 2, form: health-chain, max: { tiles: 12 },
      meaning: "what the person on call must know first, now: the drawn thing's own vital sign in a shape native to it (a row of `view_archetypes`), the evidence beneath it, what the page cannot see, and where a person may act" }
  - { lens: inspect,    depth: 3, form: anatomy,      max: { cards: 12 },
      meaning: "what exactly the parts are and how that is known: a card of each part's own facts with their provenance, the steps, the wiring, and what is still open" }
view_archetypes:
  - { archetype: reservoir,    meaning: "a store filling toward its thresholds: how full, each threshold and what it does, the time to the next, what else fills it", when: "the risk is something filling up: a disk, a queue, a quota" }
  - { archetype: lanes,        meaning: "parallel paths, each a lane of hops coloured by state, with a verdict per lane", when: "the work goes through redundant paths that must each get through" }
  - { archetype: roster,       meaning: "the items it serves: how many are active, and a bar each for how much", when: "the question is who uses it and how much" }
  - { archetype: gauges,       meaning: "one dial per value against its warning and critical limits", when: "the work keeps values inside limits" }
  - { archetype: board,        meaning: "a fixed set of parts, each with its state and one fact, and the headline numbers", when: "a known set of parts must each be doing its job" }
  - { archetype: scoreboard,   meaning: "the watcher's own vital numbers and what is firing, or a calm 'nothing is firing'", when: "what is drawn is the watching itself" }
  - { archetype: funnel,       meaning: "a stream narrowing through its stages: how many reached each, where the rest stopped and why, then a roll call of the parts", when: "work enters, is judged at a series of stages, and leaves" }
  - { archetype: race,         meaning: "a run of a procedure against its deadline: the step it is at (a step of the procedure the view `draws`, in the order its `steps` list them), how long it has run, how long it still needs, and the verdict", when: "what is drawn is a bounded run that must end before a moment" }
  - { archetype: table,        meaning: "the members of a reading, or the rows of a series, one line each with a column per path: the report, and an offline file of it", when: "the question is which ones, and what each holds" }
  - { archetype: health-chain, meaning: "tiles in flow order with value, limit and trend, and the blind spots", when: "no shape native to what is drawn is designed yet" }
profiles:
  accounting:
    meaning: "for a garden that keeps accounts, in the words its field uses. Analytic accounting first: where each amount's cost or revenue belongs, along plans the garden keeps as its own scheme of codes — a plan is a code at the scheme's first level, `plan`, and an account one beneath it, `account`. What an account holds is READ (bin/dmreckon.py `apportion`), never stored. Its names are the field's: `analytic_distribution` is what an ERP's user already writes, and seed/COOKBOOK.md pairs each of the field's names with where it is kept"
    overlays:
      - term: transactions
        schema:
          attrs:
            analytic_distribution:
              meaning: "where this amount belongs: one entry per account of the garden's analytic scheme, each with its share (whole parts of the plan's whole) or its amount (which, in a plan, add up to the amount)"
              in:
                entries:
                  code:   { required: true, in: { type: coding }, meaning: "the account, with the garden's own analytic scheme it is in: `analytic:orchard`" }
                  share:  { in: { pattern: '^[1-9][0-9]{0,39}$' }, meaning: "its part of the whole, in whole parts, as a party's share of a cost is: 60 and 40 are three fifths and two fifths — a plan's shares are its whole" }
                  amount: { in: { quantity: money }, meaning: "instead of a share: its part, in the amount's currency" }
                  note:   { in: prose, meaning: "optional prose" }
                one_of: [share, amount]
                at_most_one_of: [[share, amount]]
          sums:
            - { whole: [charged, amount], parts: analytic_distribution.amount, per: { level: plan } }
      - term: clauses
        schema:
          attrs:
            analytic_distribution:
              meaning: "where what the clause asks belongs — a budget line: one entry per account, each with its share (whole parts of the plan's whole) or its amount (which, in a plan, add up to the clause's)"
              in:
                entries:
                  code:   { required: true, in: { type: coding }, meaning: "the account, with the garden's own analytic scheme it is in: `analytic:orchard`" }
                  share:  { in: { pattern: '^[1-9][0-9]{0,39}$' }, meaning: "its part of the whole, in whole parts, as a party's share of a cost is: 60 and 40 are three fifths and two fifths — a plan's shares are its whole" }
                  amount: { in: { quantity: money }, meaning: "instead of a share: its part, in the amount's currency" }
                  note:   { in: prose, meaning: "optional prose" }
                one_of: [share, amount]
                at_most_one_of: [[share, amount]]
          sums:
            - { whole: [amount], parts: analytic_distribution.amount, per: { level: plan } }
  code:
    meaning: "for a garden that manages source code: where its trees are and how an agent treats each, and the repository identity of a code bean"
    vacancies:
    - at: located_at.role
      position: vendored-dependency
      reason: prediction
      why: "No bean vendors a third-party tree into its own source today. Kept because vendoring is an ordinary state for a code estate, and without the position a vendored tree would be recorded as own-source, silently losing the distinction between the code the estate wrote and the code it carries."
    - at: located_at.role
      position: generated-artifact
      reason: prediction
      why: "No bean records a build-output tree yet. Kept because an artifact tree must never be indexed as own-source: it is derived, so re-analysing it teaches nothing the source did not already say."
    overlays:
      - term: located_at
        schema:
          required_on_gene: [codebase]
          attrs:
            role:         { in: [own-source, vendored-dependency, generated-artifact], meaning: "what the tree at this position is of the code bean: own-source (its own source) | vendored-dependency (another code's tree carried inside it) | generated-artifact (what its build made). A tree of another code that it is only read beside is that code's own location, reached through `depends_on`" }
            scan_policy:  { in: [index, reference-only, skim], meaning: "index (own code — walk fully) | reference-only (do NOT re-scan each session; consult analysis_cache, grep on demand only) | skim (structure only)" }
            stack:        { in: { type: kebab }, meaning: "language/runtime tag, e.g. python-django | csharp-dotnet (optional)" }
            entrypoint:   { in: prose, meaning: "manifest / solution / addin that roots the tree (optional)" }
          cells:
            - { when: { role: [own-source, vendored-dependency, generated-artifact] }, requires: [scan_policy] }
    terms:
    - term: git_remote
      meaning: "a source repository's remote URL (the crypto/logical identity of a code tree), written verbatim as the remote string (`host:path` or a scheme URL) with only its host lowercased"
      context_keys: ["git_remote"]
      anchor: { class: logical, establishing: true }
      merge: { cardinality: single, order: none }
      promotion: { status: candidate, note: "general (any code garden has repos) — REVIEW in the attrs-to-universal session" }

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
        Nothing should speak it. `impossible` rather than `prediction`, which is the whole point of
        registering it: MS-CHAPv2 and MPPE are broken by published attacks, so a pptp tunnel protects
        nothing while presenting as a VPN in every inventory that lists it. Declaring the position and
        refusing it is how the law states a standing decision that would otherwise exist only as an
        absence — and an absence is indistinguishable from nobody having thought about it.
    - { at: "registry:net_protocols", position: ipv4, reason: universal, why: "declared because the structure is general, not because an occupant is expected (CONTRIBUTING: a mechanism may precede its occupants)" }
    - { at: "registry:net_protocols", position: ipv6, reason: universal, why: "declared because the structure is general, not because an occupant is expected (CONTRIBUTING: a mechanism may precede its occupants)" }
    - { at: "registry:net_protocols", position: icmp, reason: universal, why: "declared because the structure is general, not because an occupant is expected (CONTRIBUTING: a mechanism may precede its occupants)" }
    - { at: "registry:net_protocols", position: arp, reason: universal, why: "declared because the structure is general, not because an occupant is expected (CONTRIBUTING: a mechanism may precede its occupants)" }
    - { at: "registry:net_protocols", position: dot1q, reason: universal, why: "declared because the structure is general, not because an occupant is expected (CONTRIBUTING: a mechanism may precede its occupants)" }
    - { at: "registry:net_protocols", position: stp, reason: universal, why: "declared because the structure is general, not because an occupant is expected (CONTRIBUTING: a mechanism may precede its occupants)" }
    - { at: "registry:net_protocols", position: lldp, reason: universal, why: "declared because the structure is general, not because an occupant is expected (CONTRIBUTING: a mechanism may precede its occupants)" }
    - { at: "registry:net_protocols", position: gre, reason: universal, why: "declared because the structure is general, not because an occupant is expected (CONTRIBUTING: a mechanism may precede its occupants)" }
    - { at: "registry:net_protocols", position: ipsec, reason: universal, why: "declared because the structure is general, not because an occupant is expected (CONTRIBUTING: a mechanism may precede its occupants)" }
    - { at: "registry:net_protocols", position: vxlan, reason: universal, why: "declared because the structure is general, not because an occupant is expected (CONTRIBUTING: a mechanism may precede its occupants)" }
    - { at: "registry:net_protocols", position: ospf, reason: universal, why: "declared because the structure is general, not because an occupant is expected (CONTRIBUTING: a mechanism may precede its occupants)" }
    - { at: "registry:net_protocols", position: is-is, reason: universal, why: "declared because the structure is general, not because an occupant is expected (CONTRIBUTING: a mechanism may precede its occupants)" }
    - { at: "registry:net_protocols", position: rip, reason: universal, why: "declared because the structure is general, not because an occupant is expected (CONTRIBUTING: a mechanism may precede its occupants)" }
    - { at: "registry:net_protocols", position: eigrp, reason: universal, why: "declared because the structure is general, not because an occupant is expected (CONTRIBUTING: a mechanism may precede its occupants)" }
    - { at: "registry:net_protocols", position: bgp, reason: universal, why: "declared because the structure is general, not because an occupant is expected (CONTRIBUTING: a mechanism may precede its occupants)" }
    - { at: "registry:net_protocols", position: vrrp, reason: universal, why: "declared because the structure is general, not because an occupant is expected (CONTRIBUTING: a mechanism may precede its occupants)" }
    - { at: "registry:net_protocols", position: dhcp, reason: universal, why: "declared because the structure is general, not because an occupant is expected (CONTRIBUTING: a mechanism may precede its occupants)" }
    - { at: "registry:net_protocols", position: ntp, reason: universal, why: "declared because the structure is general, not because an occupant is expected (CONTRIBUTING: a mechanism may precede its occupants)" }
    - { at: "registry:net_protocols", position: snmp, reason: universal, why: "declared because the structure is general, not because an occupant is expected (CONTRIBUTING: a mechanism may precede its occupants)" }
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
        `prediction` and not `impossible`: v6 is ordinary and arriving, and the position exists so that
        the day one endpoint takes it, the gate says the prediction came true instead of
        letting a whole address family appear with nothing noticing.
    terms:
    - term: endpoints
      meaning: >
        The listening surfaces this being offers: for each, the protocol spoken, the address system and
        address it answers at, the port, and what the channel protects. An endpoint entry is a STATEMENT
        THAT THE BEING ANSWERS THERE — which is why a `forbidden` position on one is a breach by itself.
      context_keys: [endpoints]
      placement: location
      schema:
        shape: list_of_entries
        attrs:
          protocol:         { required: true, in: { registry: net_protocols, take: protocol }, meaning: "which protocol is spoken here — a row of net_protocols, never an implementation name" }
          system:           { required: true, in: { registry: anchor_systems, take: system, where: { dimension: [place] } }, meaning: "the PLACE system the surface is stated in — `ipv4` or `ipv6` for a network address, `unix-filesystem` for a socket path. It selects the form `at` must take. Named `system`, as in `roots`, `located_at` and `timing`: `keyed_by` resolves a registry row by a field that exists on BOTH the entry and the row, so the two are one name by construction." }
          at:               { required: true, in: { form_of: anchor_systems, keyed_by: system, take: pattern }, meaning: "the address answered at, in that system's ONE canonical form" }
          exposure:         { in: [loopback, lan, link, internet], meaning: "loopback (this machine only) | lan (the local segment) | link (reachable only over a named link, e.g. the wireguard tunnel) | internet (bound to a public address directly)" }
          observed:         { origin: { act: read, nature: soma }, in: { type: position, unit: day }, meaning: "ABSOLUTE date the surface was checked. Endpoints age faster than almost anything else here." }
          confidentiality:  { in: { aspect: confidentiality, default: cleartext }, meaning: "the position on the confidentiality aspect — what the channel protects. Defaults to cleartext, because a channel nobody has said protects anything does not." }
          permission:       { in: { aspect: permission, default: permitted }, meaning: "the position on the permission aspect — whether this surface MAY exist at all" }
          transport:        { in: { registry: net_protocols, take: protocol, where: { layer: transport } }, default_from: { registry: net_protocols, keyed_by: protocol, take: transport }, meaning: "tcp | udp — which transport's port space `port` is a position in. Defaults to the protocol row's `transport`." }
          plane:            { in: { registry: planes, take: plane }, meaning: "data | control | management — what this is FOR. Stated where it matters: a management surface deserves a different exposure from a data one." }
          port:             { in: { form_of: anchor_systems, keyed_by: transport, take: pattern }, meaning: "the port: a position in the transport's port space, WITHIN the address beside it. One port per entry. Omitted where the protocol rides another (sftp over ssh) and has none of its own, and for a socket path, which has none at all." }
          via_link:         { in: { key_of: links }, meaning: "optional: the `links` key this surface is reachable over, when it is not reachable without it" }
          admitted_from:    { in: prose, meaning: "WHO may reach this surface, when not everyone who can reach its address may: the named sources the being itself admits, and where that is enforced. A second fact beside `exposure`, which says only WHERE the surface is bound. Absent means nothing restricts it." }
          note: { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" }
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
          observed:         { origin: { act: read, nature: soma }, in: { type: position, unit: day }, meaning: "ABSOLUTE date the link was checked" }
          peer:             { in: ref, meaning: "a {bean, field} ref to the other end. A link is MUTUAL, and has no direction: each end records the other as its peer, where a reach or a treatment names the end it is directed at, `to`. A REF, not a retyped address" }
          confidentiality:  { in: { aspect: confidentiality, default: cleartext }, meaning: "what the link protects, for everything carried over it" }
          plane:            { in: { registry: planes, take: plane }, meaning: "data | control | management — what this is FOR." }
          carried_by:       { in: { key_of: links }, meaning: "optional: the `links` entry this one rides over — a tunnel rides a WAN link rides an interface" }
          note: { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" }
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
          observed:   { origin: { act: read, nature: soma }, in: { type: position, unit: day }, meaning: "ABSOLUTE date the reach was verified to work" }
          to:         { in: ref, meaning: "a {bean[, field]} ref to what it reaches. A ref rather than an address, so the far end stays the one owner of its own address." }
          necessity:  { in: { aspect: necessity, default: necessary }, meaning: "the position on the necessity aspect — `necessary` if the being cannot do its work without it" }
          via_link:   { in: { key_of: links }, meaning: "optional: the link this reach must cross" }
          note: { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" }
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
          observed:    { origin: { act: read, nature: soma }, in: { type: position, unit: day }, meaning: "ABSOLUTE date the treatment was read off the device" }
          to:          { in: ref, meaning: "optional: a {bean, field} ref to where the treatment sends traffic" }
          permission:  { in: { aspect: permission, default: permitted }, meaning: "the position on the permission aspect. `required` is the one that earns this term: a server's outbound SPF identity can DEPEND on firewall mangle marks, and today that is a prose safety note nothing enforces." }
          note: { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" }
      merge: { cardinality: multi, order: by-kind+what }
  domain:
    meaning: >
      for a garden that holds delegated names — registered domains. The one class of fact that can lose a name
      outright is its registration, and a registration is an agreement: the registrant holds the name through a
      registrar until a day on which it lapses unless it is renewed — a contract `over` the domain, its parties
      `registrant` and `registrar`, its `timing` the `registration`, and a clause `renewal` that falls due on the
      day it lapses, with ninety days' `notice`: an unrenewed domain takes its DNS and its mail with it. The
      profile adds the one word of the field the core does not have. A garden with no domains inherits none of it.
    overlays:
      - term: clauses
        schema:
          attrs:
            auto_renew: { in: [enabled, disabled, unknown], meaning: "on the renewal of a registration: whether the registrar renews the name without being asked — enabled | disabled | unknown. `unknown` is the honest default: it is a registrar-ACCOUNT setting and does not appear in WHOIS, so it cannot be observed the way the dates can" }
    vacancies:
    - { at: "clauses.auto_renew", position: enabled, reason: universal, why: "whether the registrar renews the name by itself, declared whole — on, off, or not known — because every registration is in one of the three; a garden holding a few names takes one or two of them" }
    - { at: "clauses.auto_renew", position: disabled, reason: universal, why: "whether the registrar renews the name by itself, declared whole — on, off, or not known — because every registration is in one of the three; a garden holding a few names takes one or two of them" }
    - { at: "clauses.auto_renew", position: unknown, reason: universal, why: "whether the registrar renews the name by itself, declared whole — on, off, or not known — because every registration is in one of the three; a garden holding a few names takes one or two of them" }

  knowledge:
    meaning: >
      for a garden that says what things ARE in the world's shared terms: the field of knowledge a skill or a
      technology draws on (ISCED-F 2013), the occupation a role or a person's work is (ISCO-08), and the
      established technology a program, instance or host runs (with its official documentation). The codes are
      UNIVERSAL: the same in every garden, so knowledge merges across gardens that never met — and a being that IS one
      of them (an occupation, a field, a technology) is identified by it, `identifier: isco-08:2522`, a coding.
    terms:
    - term: knowledge
      meaning: "how this being stands to published knowledge: classified as an occupation, drawing on a field, using a technology"
      context_keys: [knowledge]
      schema:
        shape: list_of_entries
        attrs:
          code:    { required: true, in: { type: coding }, meaning: "the code, with the classification it is in: `isced-f-2013:0612`, `isco-08:2522`, `technology:samba`" }
          rel:     { required: true, in: [classified_as, draws_on, uses], meaning: "classified_as (this IS of that kind) | draws_on (this rests on that knowledge) | uses (this runs that technology)" }
          topic:   { in: prose, meaning: "optional: the concept inside the field this draws on" }
          note:    { in: prose, meaning: optional }
      merge: { cardinality: multi, order: by-code+rel }

  view:
    meaning: >
      for a garden that draws what it keeps: a page of drawings, each of a mapping or a bean the garden holds, read at
      four lenses, with live values beside the drawing and actions a host may run. Its asset is `assets/view/`, which a
      garden receives only while it extends this profile. A garden that draws nothing should inherit none of it.
    vacancies:
    - { at: "registry:view_archetypes", position: reservoir,    reason: universal, why: "the operate shapes the asset draws, declared whole; a garden takes the ones its drawings need" }
    - { at: "registry:view_archetypes", position: lanes,        reason: universal, why: "the operate shapes the asset draws, declared whole; a garden takes the ones its drawings need" }
    - { at: "registry:view_archetypes", position: roster,       reason: universal, why: "the operate shapes the asset draws, declared whole; a garden takes the ones its drawings need" }
    - { at: "registry:view_archetypes", position: gauges,       reason: universal, why: "the operate shapes the asset draws, declared whole; a garden takes the ones its drawings need" }
    - { at: "registry:view_archetypes", position: board,        reason: universal, why: "the operate shapes the asset draws, declared whole; a garden takes the ones its drawings need" }
    - { at: "registry:view_archetypes", position: scoreboard,   reason: universal, why: "the operate shapes the asset draws, declared whole; a garden takes the ones its drawings need" }
    - { at: "registry:view_archetypes", position: funnel,       reason: universal, why: "the operate shapes the asset draws, declared whole; a garden takes the ones its drawings need" }
    - { at: "registry:view_archetypes", position: race,         reason: universal, why: "the operate shapes the asset draws, declared whole; a garden takes the ones its drawings need" }
    - { at: "registry:view_archetypes", position: table,        reason: universal, why: "the operate shapes the asset draws, declared whole; a garden takes the ones its drawings need" }
    - { at: "registry:view_archetypes", position: health-chain, reason: universal, why: "the operate shapes the asset draws, declared whole; a garden takes the ones its drawings need" }
    - { at: "view_bindings.live", position: live-state,  reason: universal, why: "the three kinds of live value, declared whole" }
    - { at: "view_bindings.live", position: live-value,  reason: universal, why: "the three kinds of live value, declared whole" }
    - { at: "view_bindings.live", position: live-series, reason: universal, why: "the three kinds of live value, declared whole" }
    terms:
    - term: view
      meaning: "this bean is a page of drawings: the garden's own drawing module, the organisation it opens on, who reads it, the parts a reader looks up, which of a being's own facts a card shows, and the words a reader may hover. What it is called is its `title`; what it draws is its `views`; where its live values come from is its `view_monitors`"
      context_keys: [view]
      schema:
        shape: mapping
        attrs:
          drawings:  { required: true, in: { pointer: bean_field_pointer }, meaning: "`file:<path>` of the garden's own drawing module: the garden's code, never the law's" }
          opens_on:  { in: { bean_id: { gene: [org] } }, meaning: "the organisation the page opens on; absent, every organisation the reader may see" }
          visibility: { in: [public, private], meaning: "who reads the page. public (absent): anyone it is published to — no drawing shows an address, and a being's addresses are on its card, for a viewer who may see them | private: only the viewers its host signs in — at the understand lens each part shows its own address in its box, the one `reference` chooses from the being's own record, sent only to a viewer who may see that being; and a drawing's own text may show addresses, which every viewer of that drawing sees" }
          glossary:  { in: { prose: named }, meaning: "what a word on the page means, under the word" }
          reference:
            meaning: "the parts a reader looks up, one entry per being, in the order listed. The address that stands for a being is one the being itself states, and is chosen here, never stated here"
            in:
              entries:
                being:  { required: true, in: bean_id, meaning: "the part" }
                system: { in: { registry: anchor_systems, take: system, where: { dimension: [place] } }, meaning: "the place system whose position stands for it: the first the being states in that system, in `located_at`, its anchors or its `endpoints`, in that order" }
                what:   { in: prose, meaning: "one line: what the part is for, in this page's words" }
              keyed_by: being
          fields:
            meaning: "which of a being's own top-level facts a card shows, for a being of which genos, from which lens on"
            in:
              entries:
                genos: { required: true, in: { registry: gene, take: genos }, meaning: "the genos of the beings whose cards show it" }
                term:  { required: true, in: { pattern: '^[a-z][a-z0-9_]*$' }, meaning: "the name of a term the law declares" }
                shown_from: { required: true, in: { registry: view_lenses, take: lens }, meaning: "the first lens that shows it; every deeper lens shows it too" }
          note: { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" }
      merge: { cardinality: single, order: none }
    - term: view_monitors
      meaning: "the monitors a page's live values come from, one entry each. What a monitor watches is its own `reaches` and each target's own `endpoints`; which technology it runs is its own `knowledge` (`uses`), and the asset reads it through its adapter for that technology"
      context_keys: [view_monitors]
      schema:
        shape: list_of_entries
        attrs:
          monitor:  { required: true, in: bean_id, meaning: "the being that collects the values" }
          settings: { in: { pointer: bean_field_pointer }, meaning: "where that monitor states what only its technology needs, read by the adapter in the technology's own form: stated, not checked, until a term the law declares carries it" }
          note: { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" }
      merge: { cardinality: multi, order: by-monitor }
    - term: views
      meaning: "what the page draws, one entry per drawing under the key its drawing module draws it by: the mapping or bean it draws, the story of it in plain words, the question each lens asks, the operate lens's shape and what the shape reads, where its processes and pipes are stated, and where a person may act. A value named in it is a key of `view_bindings` on the same page"
      context_keys: [views]
      schema:
        shape: open_map_of_entries
        key_form: kebab
        attrs:
          draws:     { required: true, in: ref, meaning: "the mapping or bean this draws. What it is, and its steps, are its own: the page never restates them" }
          label:     { in: prose, meaning: "its name on the page; absent, the title of what it draws" }
          purpose:   { required: true, in: prose, meaning: "what it guarantees, in one sentence" }
          outcome:   { required: true, in: prose, meaning: "what is true when it works" }
          stages:
            required: true
            meaning: "three to five stages in the order work flows, each in plain words, with the beings that do it and the technologies it uses"
            in:
              entries:
                label:  { required: true, in: prose, meaning: "the stage, in a few words" }
                doer:   { required: true, in: prose, meaning: "who or what does it" }
                beings: { in: { entries: { being: { required: true, in: bean_id } } }, meaning: "the beings that do it" }
                uses:   { in: { entries: { technology: { required: true, in: { registry: technology, take: code } } } }, meaning: "the technologies it uses, each opening its own documentation" }
          questions:
            required: true
            meaning: "the question this drawing asks at each lens, in its own words; a lens it names none for asks the lens's own"
            in:
              entries:
                lens: { required: true, in: { registry: view_lenses, take: lens } }
                ask:  { required: true, in: prose }
              keyed_by: lens
          processes: { in: { pointer: bean_field_pointer }, meaning: "inspect: where the processes of what it draws are stated — a field of a being, read as the being states it" }
          pipes:     { in: { pointer: bean_field_pointer }, meaning: "inspect: where the pipes between those processes are stated, likewise" }
          actions:
            meaning: "where a person may act: the drawn element a button sits on and the tool it asks the host for. What a tool runs is the host's, never the ledger's"
            in:
              entries:
                element: { required: true, in: { type: kebab }, meaning: "the drawn element the button sits on, by the id its drawing gives it" }
                tool:    { required: true, in: { type: kebab }, meaning: "the tool, by the name the host's own configuration gives it" }
                confirm: { in: prose, meaning: "what the button asks before it runs" }
                acts_on: { in: bean_id, meaning: "the being it acts on, where that is not the element's" }
                inputs:
                  meaning: "what the tool is given beyond who pressed, the moment and the being acted on, which the host always hands it: each value by name, with its `origin` as a reading's inputs state it (`selection_form.inputs`) — the clock, read by the reader; any other, a value the person pressing types"
                  in:
                    entries:
                      name:     { required: true, in: { type: kebab } }
                      origin:   { required: true, in: origin, meaning: "`{act: read, nature: soma, by: reader}`, the clock; any other, a value the person pressing gives" }
                      type:     { in: { registry: value_types, take: type }, meaning: "the form of a value given" }
                      quantity: { in: { registry: quantities, take: quantity }, meaning: "the quantity a value given measures" }
                      note:     { in: prose }
                    keyed_by: name
                reason:      { in: [asked], meaning: "asked — the person pressing states a reason, which the host's audit records" }
                every:       { in: recurrence, meaning: "a schedule: the host runs it at each occurrence (`dmview run-scheduled`), as `answered_by`" }
                answered_by: { in: { bean_id: { gene: [person, org] } }, meaning: "with `every`: who answers for what it does when nobody presses — the actor its grant is asked for" }
                note: { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" }
          archetype: { required: true, in: { registry: view_archetypes, take: archetype }, meaning: "operate: the shape its vital sign is drawn in" }
          blind:     { required: true, meaning: "what the page cannot see of it, and why: never omitted", in: { entries: { what: { required: true, in: prose }, why: { in: prose } } } }
          notes:     { in: { entries: { note: { required: true, in: prose } } }, meaning: "operate: a line the person on call reads under the shape" }
          fill:      { in: { key_of: view_bindings }, meaning: "reservoir: how full it is" }
          thresholds: { in: { entries: { fullness: { required: true, in: { quantity: ratio } }, label: { required: true, in: prose } } }, meaning: "reservoir: the marks on its scale, as a share of the whole, and what each does" }
          forecast:  { in: { key_of: view_bindings }, meaning: "reservoir: how long until the next threshold" }
          also:      { in: { entries: { bind: { required: true, in: { key_of: view_bindings } } } }, meaning: "reservoir: what else fills it" }
          parts:     { in: { entries: { bind: { required: true, in: { key_of: view_bindings } } } }, meaning: "the values of the parts beneath the shape: the evidence" }
          lanes:     { in: { entries: { label: { required: true, in: prose }, hops: { required: true, in: { entries: { label: { required: true, in: prose }, bind: { required: true, in: { key_of: view_bindings } } } } } } }, meaning: "lanes: each path, and the hops it must get through in order" }
          per_item:  { in: { key_of: view_bindings }, meaning: "roster, gauges: the live-series that gives one value per item" }
          active_over: { in: { type: count }, meaning: "roster: in that value's unit, the value from which an item counts as active" }
          top:       { in: { type: count }, meaning: "roster: how many items are shown" }
          min:       { in: { type: count }, meaning: "gauges: in that value's unit, the low end of each dial" }
          max:       { in: { type: count }, meaning: "gauges: in that value's unit, the high end of each dial" }
          facts:     { in: { entries: { bind: { required: true, in: { key_of: view_bindings } } } }, meaning: "board: the headline numbers" }
          members:   { in: { entries: { label: { required: true, in: prose }, binds: { in: { entries: { bind: { required: true, in: { key_of: view_bindings } } } } }, fact: { in: { key_of: view_bindings } }, why: { in: prose }, being: { in: bean_id } } }, meaning: "board: its parts, each with the values that say its state, one fact, and why an unmeasured part is not measured" }
          numbers:   { in: { entries: { bind: { required: true, in: { key_of: view_bindings } } } }, meaning: "scoreboard, funnel, race: the headline numbers" }
          list:      { in: { key_of: view_bindings }, meaning: "scoreboard: the live-series of what is firing" }
          funnels:   { in: { entries: { label: { required: true, in: prose }, stages: { required: true, in: { entries: { label: { required: true, in: prose }, tally: { in: { key_of: view_bindings } }, selection: { in: { key_of: selections }, meaning: "or a reading of the page whose members are counted: a walk's step (`at_step`)" }, counts: { in: prose }, what: { in: prose }, stops: { in: { entries: { label: { required: true, in: prose }, bind: { required: true, in: { key_of: view_bindings } }, what: { in: prose } } } }, marks: { in: { entries: { label: { required: true, in: prose }, bind: { required: true, in: { key_of: view_bindings } }, what: { in: prose } } } } }, one_of: [tally, selection], at_most_one_of: [[tally, selection]] } } } }, meaning: "funnel: each stream, its stages in order with how many reached each — a live value, or the members of a reading — and what each counts, and where the rest stopped or were marked" }
          window:    { in: prose, meaning: "funnel: the span its counts cover, in words" }
          rollcall:  { in: { entries: { label: { required: true, in: prose }, per_item: { required: true, in: { key_of: view_bindings } }, idle: { in: { entries: { member: { required: true, in: any } } } }, notes: { in: { prose: named } } } }, meaning: "funnel: the parts called by name, each up or down, and the items known to carry nothing" }
          selection: { in: { key_of: selections }, meaning: "table: the members it lists, one line each — a reading of the page's own `selections`" }
          series:    { in: { pointer: bean_field_pointer }, meaning: "table: or the positions of one of a being's `series` (`{bean, field}`), one line each" }
          columns:   { in: { entries: { label: { required: true, in: prose }, path: { required: true, in: { type: field_path }, meaning: "a path in each member, or a channel of the series" } } }, meaning: "table: a column per path" }
          writes:    { in: { entries: { term: { required: true, in: { pattern: '^[a-z][a-z0-9_]*$' } }, attrs: { in: { entries: { attr: { required: true, in: { type: kebab } } } } } } }, meaning: "an entry form for those attributes of that term, built from the law's form of it, saved through bin/dmsave.py as the host with the person in `<who>`, after `write` is granted them; the gate judges it as any other commit" }
          renders:   { in: { entries: { template: { required: true, in: { pointer: bean_field_pointer } }, selection: { in: { key_of: selections } } } }, meaning: "a template of the garden (`file:<path>`) rendered from each member of a reading (`selection`; absent, the being drawn) into a document; once kept, a `document` bean with its `content_hash`" }
          feed:      { in: { entries: { selection: { required: true, in: { key_of: selections } }, notice: { in: extent } } }, meaning: "a calendar export (RFC 5545) of a reading's members, each at its `timing` or its clause's due, a notice `notice` before; every export is a pass the host audits" }
          step_at:   { in: { key_of: view_bindings }, meaning: "race: the value that says which step of the procedure the run is at — 0 before the first, n at the n-th of its `steps`" }
          elapsed:   { in: { key_of: view_bindings }, meaning: "race: how long it has run" }
          deadline:  { in: extent, meaning: "race: how long after its start it must be done — a length on `time`" }
          deadline_from: { in: { key_of: view_bindings }, meaning: "race: the value that says when it must be done, where that moves" }
          eta:       { in: { key_of: view_bindings }, meaning: "race: how long it still needs" }
          progress:  { in: { key_of: view_bindings }, meaning: "race: how much of it is done, as a share of the whole" }
          checkpoints: { in: { entries: { after: { required: true, in: extent }, label: { required: true, in: prose } } }, meaning: "race: marks on its time bar, each a length after its start" }
          correlate:
            meaning: "any shape: values drawn on one time axis, so what moves together is seen together"
            in:
              entries:
                title: { in: prose }
                traces: { required: true, in: { entries: { bind: { required: true, in: { key_of: view_bindings } } } }, meaning: "the values drawn, one trace each" }
                span:  { in: extent, meaning: "how far back the axis reaches — a length on `time`" }
                every: { in: recurrence, meaning: "how often a point is taken — every N units along `time`" }
                band:  { in: { key_of: view_bindings }, meaning: "a step value (as `step_at`) that shades every trace" }
                relate: { in: { entries: { across: { required: true, in: { key_of: view_bindings } }, measure: { required: true, in: { key_of: view_bindings } }, bins: { in: { type: count } }, at_step: { in: { type: count } }, keep: { in: [all, positive] } } }, meaning: "one value's mean across the bins of another, over the time drawn: only while the band is at `at_step` where it names one, and `positive` keeps the moments it is above zero" }
          note: { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" }
        cells:
          - { when: { archetype: reservoir },  requires: [fill, thresholds], why: "a reservoir answers with how full it is against its thresholds" }
          - { when: { archetype: lanes },      requires: [lanes],       why: "lanes answer with each path" }
          - { when: { archetype: roster },     requires: [per_item],    why: "a roster answers with the value of its items" }
          - { when: { archetype: gauges },     requires: [per_item],    why: "gauges answer with the value of their items" }
          - { when: { archetype: board },      requires: [members],     why: "a board answers with its parts" }
          - { when: { archetype: scoreboard }, requires: [numbers],     why: "a scoreboard answers with its numbers" }
          - { when: { archetype: funnel },     requires: [funnels],     why: "a funnel answers with its streams" }
          - { when: { archetype: race },       requires: [step_at],     why: "a race answers with the step the run is at" }
          - { when: { archetype: race },       expects: [elapsed],      why: "without how long it has run, the bar against the deadline cannot be drawn" }
          - { when: { archetype: table },      requires: [columns],     why: "a table answers with a column per path" }
      merge: { cardinality: multi, order: by-key }
    - term: view_bindings
      meaning: "the live values the page draws, each under a key the views name it by: which drawing and which of its elements it sits on, what kind of value it is, its unit and limits, and how each technology computes it. A value is read when the page is drawn, and never stored"
      context_keys: [view_bindings]
      schema:
        shape: open_map_of_entries
        key_form: kebab
        attrs:
          view:    { required: true, in: { key_of: views }, meaning: "the drawing it sits on" }
          element: { required: true, in: { type: kebab }, meaning: "the drawn element it sits on, by the id its drawing gives it" }
          live:    { required: true, in: [live-state, live-value, live-series], meaning: "live-state — whether the being answers, as its monitor reaches it | live-value — one number | live-series — many, each an item" }
          being:   { in: bean_id, meaning: "the being a live-state reads; absent, the being the element depicts" }
          label:   { in: prose, meaning: "its name on the page; absent, the element's" }
          short:   { in: prose, meaning: "its name where room is short" }
          unit:    { in: { registry: units, take: unit }, meaning: "absent, a bare number" }
          warn:    { in: { type: count }, meaning: "in its unit, the value from which it warns" }
          crit:    { in: { type: count }, meaning: "in its unit, the value from which it is critical" }
          item_names: { in: { prose: named }, meaning: "live-series: the page's name for an item, under the item" }
          query:
            meaning: "how each technology computes it, in that technology's own language, one entry per technology; its adapter refuses what it cannot read"
            in:
              entries:
                technology: { required: true, in: { registry: technology, take: code } }
                says:       { required: true, in: any, meaning: "the query, in the technology's own language" }
                items_by:   { in: any, meaning: "live-series: what tells its items apart, in the technology's own terms" }
              keyed_by: technology
          note: { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" }
        cells:
          - { when: { live: live-value },  requires: [query], why: "a number is computed by a monitor" }
          - { when: { live: live-series }, requires: [query], why: "a series is computed by a monitor" }
      merge: { cardinality: multi, order: by-key }

terms:
  - term: capabilities
    meaning: "what this being may or must be able to do: an OPEN map of capability name -> the permission taken on it"
    context_keys: ["capabilities"]
    schema:
      shape: open_map_of_entries
      key_form: kebab
      attrs:
        why:              { required: true, in: prose, meaning: "WHY this permission holds — the consequence of violating it, in prose an operator can act on" }
        permission:       { in: { aspect: permission, default: permitted }, meaning: "the position taken on the permission aspect (required | omissible | permitted | forbidden)" }
        feasibility:      { in: { aspect: feasibility, default: possible }, meaning: "the position on the feasibility aspect — whether the being CAN be in that state at all, independent of whether it may. `forbidden` + `possible` is a live risk; `forbidden` + `impossible` is already prevented by something else." }
        by:               { in: prose, meaning: "optional: who imposes it, when the enforcer is not us (e.g. a hosting provider)" }
        feasibility_why:  { in: prose, meaning: "optional: WHY the feasibility position holds — a sysctl is reversible, a kernel flag is not. Distinct from `why`, which is the reason for the PERMISSION" }
        code:             { in: { type: coding }, meaning: "the code of a published scheme this stance is on — and every code beneath it" }
        within:           { in: { entries: { system: { required: true, in: { registry: anchor_systems, take: system, where: { dimension: [place] } } }, at: { required: true, in: { form_of: anchor_systems, keyed_by: system, take: pattern } } } }, meaning: "the place it holds in" }
        note: { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" }
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
        note: { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" }
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
        note: { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" }
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
      values: [observed, inferred, stated-in-document, asserted-by-human, generated-by-tool]
    merge: { order: source, borrows: generated-by-tool }
    values_source:
      generated-by-tool:  { act: derived, nature: soma }
      inferred:           { act: derived, nature: lekton }
      observed:           { act: read,    nature: soma }
      stated-in-document: { act: said,    nature: lekton }
      asserted-by-human:  { act: said,    nature: empsychon }
    values_meaning:
      asserted-by-human: "a person said so, and answers for it. The top, because a person can be ASKED, and because the fact may be one only a person can know (who owns this, what was agreed). The guard protects this place and no other."
      stated-in-document: "a document states it — a contract, a letter, a register, a page — and the document is named in `from`. Words someone wrote and answers for, but the document cannot be asked: above what was read off the world, below a person who can be."
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
        as_of:           { required: true, origin: { act: read, nature: soma }, in: { type: position, unit: day }, meaning: "ABSOLUTE date the analysis was produced, YYYY-MM-DD (Rule 6 paper-durable)" }
        staleness_key:   { required: true, in: { pattern: "^([a-z0-9][a-z0-9._-]*@[0-9a-f]{7,40}|manual:.+)$" }, meaning: "the value that makes this entry VALID; when it MOVES, the entry is STALE. The FORM is the pattern this attribute declares, beside this sentence, and is not restated here: `<repo>@<object-id>`, a position in a named repository's object graph, or `manual:<why>` for what no key can track." }
        policy:          { required: true, in: [index, reference-only, skim], meaning: "index | reference-only | skim — how the analysed source is to be treated" }
        form:            { in: [summary_ref, inline, external], meaning: "summary_ref | inline | external — where the cached result physically lives" }
        covers_paths:    { in: { pattern: "^(root:[a-z0-9][a-z0-9-]*(/[^:]*)?|[a-z0-9][a-z0-9.-]*:([/A-Za-z]).*)$", soft: true, why: "a bare absolute path names no host — the same defect `code_paths.path` carries" }, meaning: "the code_paths path(s) this entry analysed — this is WHERE an agent re-checks staleness_key" }
        summary_ref:     { in: { pointer: bean_field_pointer }, meaning: "REQUIRED when form: summary_ref. A pointer, or a list of pointers, to the recorded result. Each pointer is either '<section>.<key>' (a field on THIS bean, gate-resolved), or {bean: <id>, field: <key>} (a field on ANOTHER bean, gate-resolved), or 'file:<path>' (an on-disk document)." }
        relevant_scope:  { in: prose, meaning: "optional: which part of a large covered tree matters to THIS bean (e.g. 'CE module: hr')" }
        digest:          { in: { pattern: "^[a-z0-9]+:[0-9a-f]{7,}$" }, meaning: "optional short content hash of the cached result itself" }
      cells:
        - { when: { form: summary_ref }, requires: [summary_ref] }
        - { when: { staleness_key: { starts_with: "manual:" } }, expects: [covers_paths], why: "an agent cannot tell where to re-check it" }
    merge: { cardinality: multi, order: by-cache-type }
    exceptions: []
  - term: weighings
    meaning: "a judge's weighing of criteria against each other, pair by pair (the analytic hierarchy process): only the judgments are written — the weights and their consistency are READ (bin/dmreckon.py weigh), never stored. A weighing orders what a person is shown; it never decides, hides or drops anything, and the Contract of Parts comes before every weight"
    context_keys: [weighings]
    schema:
      shape: open_map_of_entries
      key_form: kebab
      attrs:
        for:      { required: true, in: { registry: ordering_keys, take: key }, meaning: "what it orders" }
        judge:    { required: true, in: { bean_id: { gene: [person, org] } }, meaning: "whose judgment it is" }
        criteria: { required: true, in: { entries: { name: { required: true, in: { type: kebab } }, what: { required: true, in: prose } }, keyed_by: name }, meaning: "what is weighed, each in the words a person checks it against" }
        pairwise: { required: true, in: { entries: { a: { required: true, in: { type: kebab } }, b: { required: true, in: { type: kebab } }, judged: { required: true, in: { pattern: '^(1/)?[1-9]$' } }, why: { in: prose }, note: { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" } }, keyed_by: [a, b] }, meaning: "how much more `a` weighs than `b`, on Saaty's scale" }
        why_inconsistent: { in: prose, meaning: "why a consistency ratio above 0.10 stands" }
        note: { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" }
    merge: { cardinality: multi, order: by-key }
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
        since:     { in: { type: position }, meaning: "optional: ABSOLUTE date this owner came to hold the facet" }
        note:      { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" }
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
        since:     { in: { type: position }, meaning: "optional: ABSOLUTE date this holder came to answer for the facet" }
        note:      { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" }
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
    merge: { cardinality: single, order: none }
  - term: lives_in
    meaning: "the immediate habitat a token lives in/on; recursive (habitat may itself be a token); a DAG"
    context_keys: ["lives_in"]
    placement: habitat
    schema:
      shape: mapping
      required_on_gene: [instance]
      dag: true
      is_ref: true
      attrs:
        bean:  { required: true, in: id }
        takes: { in: { entries: { count: { required: true, in: { type: count } }, unit: { required: true, in: { registry: units, take: unit } } } }, meaning: "what this placement takes of what its host can hold (`capacity`), each a measure in a unit of the capacity's quantity: 2 rack units, 400 gigabytes. Only a placement whose rung takes (`placement`) takes anything" }
    merge: { cardinality: single, order: none }
  - term: capacity
    meaning: "what this being can hold of what is placed in it, each a measure: 42 rack units, 2 terabytes, 30 kilograms, 12 seats. A placement whose rung takes a share or room (`placement`) takes from it; one whose rung takes nothing — an entry in a register, a memory in a mind — never does, however many are placed there"
    context_keys: [capacity]
    schema:
      shape: list_of_entries
      attrs:
        count:     { required: true, in: { type: count }, meaning: "how much" }
        unit:      { required: true, in: { registry: units, take: unit }, meaning: "a unit of what is held: its quantity says what a placement's `takes` is measured in" }
        placement: { in: { registry: placement, take: code, where: { level: mode } }, meaning: "optional: the rung whose placements draw on it — `habitat` (a share), `location` (room); absent, every rung that takes" }
        note:      { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" }
    merge: { cardinality: multi, order: "by-unit+placement?" }
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
      canonical_note: "python ipaddress normal form (v4/v6); reject bad octets"
    anchor: { class: network, establishing: false }
    merge: { cardinality: single, order: cidr }
    exceptions:
      - { case: "shared/floating/VRRP/anycast IP", decision: "co-owned; own-bean+ref OR shared_identifiers", why: "many nodes answer for one address", acked: 2026-07-31 }
      - { case: "reused RFC1918 range on isolated LANs", decision: "qualify with the network it is on", why: "private ranges exist independently", acked: 2026-07-31 }
      - { case: "dotted-quad that is NOT an ip (v17.0.0.0, CIDR base)", decision: "only values under context_keys are ips; parse with ipaddress", why: "free-text mis-read as IPs", acked: 2026-07-31 }
      - { case: "IPv6 / abbreviated shorthand (.160)", decision: "canonical full form required; ipv6 deduped", why: "invisible to IPv4-only check", acked: 2026-07-31 }
  - term: shared_identifiers
    meaning: "the addresses this bean answers for together with other beans — a floating, VRRP or anycast address — each still written where the bean keeps its addresses; one address, one owner holds for every other"
    context_keys: [shared_identifiers]
    enforced_by: none
    merge: { cardinality: set, order: none }
  - term: hostname
    meaning: "a machine's OS hostname"
    context_keys: ["hostname", "identity.anchors[].hostname"]
    schema:
      governs_anchor: hostname
      value_pattern: '^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)*$'
      canonical_note: "lowercase; one label or dotted"
    anchor: { class: network, establishing: false }
    merge: { cardinality: single, order: none }
  - term: fqdn
    meaning: "a DNS-unique fully-qualified domain name. Logical: it ESTABLISHES a being whose family is logical (a domain, a service, a virtual-host) and only CORROBORATES a body (nature soma), whose matter identifies it — a replaced machine keeps its name. The nature's family decides; the bean writes the flag that follows"
    context_keys: ["fqdn"]
    schema:
      governs_anchor: fqdn
      value_pattern: '^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$'
      canonical_note: "IDNA + lowercase; at least two labels"
    anchor: { class: logical }
    merge: { cardinality: single, order: none }
  - term: mac
    meaning: "an IEEE MAC address of a NIC. Matter when burned into a physical NIC, and then it establishes; a virtual NIC's is assigned by the hypervisor and only corroborates — the nature decides"
    context_keys: ["mac", "*_mac"]
    schema:
      governs_anchor: mac
      value_pattern: '^([0-9a-f]{2}:){5}[0-9a-f]{2}$'
      canonical_note: "lowercase colon form"
    anchor: { class: hardware }
    merge: { cardinality: set, order: none }
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
  - term: identifier
    meaning: "the logical identity a being is GIVEN — as against one read off its matter (`serial`, `mac`), its address (`ip`, `fqdn`) or its content (`content_hash`). One of three forms, told apart by how it is written: a name a garden MINTS once, `<genos>:<name>` with the bean's own genos (`person:sam`, `contract:shared-purchase`, `session:<slug>`), qualified by the garden's id when it is to be known elsewhere; an id ASSIGNED outside every garden, written as its home writes it — a package name (`postfix`), a registry or tax number, the UID an invitation carries, a provider's or hypervisor's id, the id a manifest declares, a deployment coordinate `<product>@<host>[/<db>]`, a code a published scheme gives what it classifies, written as a coding (`isco-08:2522` an occupation, `technology:samba` a technology, and checked as one) — which identifies wherever it is written; or a number ISSUED by an organisation that identifies only together with it, written with `issuer: {bean: <org>}` — an employee number, a file number, a membership number. Which forms a genos admits is its row's `identifier_forms` in `gene`; a genos that names none admits all three. Whether it ESTABLISHES is the bean's to say: a document's reference establishes the document and corroborates a design it renders, and a module's name corroborates beside the `git_remote` that establishes. A person is never identified by a national or government number: that is a secret"
    context_keys: ["identifier"]
    enforced_by: core
    anchor: { class: logical, minted: true, issued: optional }
    merge: { cardinality: single, order: none }
  - term: pass_log
    meaning: "a session's record of what passed where (`pass_form`): one entry per log, holding a file under `captures/passes/`. A commit that stages a change to one claims the session"
    context_keys: [pass_log]
    schema:
      shape: open_map_of_entries
      key_form: kebab
      only_on_gene: [session]
      attrs:
        holds: { required: true, in: { pattern: "^file:captures/passes/[a-z0-9][a-z0-9-]*\\.jsonl$" }, meaning: "the log, a `file:` pointer into `captures/passes/`: one pass to a line, only ever appended to" }
        note:  { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes" }
    merge: { cardinality: multi, order: by-key }
  - term: email
    meaning: "an e-mail address a person or an organisation is reached at. Logical; whether it ESTABLISHES is the bean's to say, because an address is reassigned and a person outlives it"
    context_keys: ["email"]
    enforced_by: none
    anchor: { class: logical }
    merge: { cardinality: single, order: none }
  - term: phone
    meaning: "a telephone number a person or an organisation is reached at, in E.164: `+` and at most fifteen digits, the country code first. Logical; whether it establishes is the bean's to say, as for `email`. A third party's is held off git unless their own consent puts it in (F2); a digest of one is kept only on a host, never in the ledger"
    context_keys: ["phone", "identity.anchors[].phone"]
    schema:
      governs_anchor: phone
      value_pattern: '^\+[1-9][0-9]{1,14}$'
      canonical_note: "`+` and the digits, country code first, nothing between them"
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
  - term: id
    meaning: "a bean/mapping identifier = its filename stem (garden-local; NOT identity)"
    context_keys: ["bean", "mapping"]
    enforced_by: core
    exceptions:
      - { case: "duplicate legit human names (two hosts both called 'file-server')", decision: "ids disambiguate via genos-prefix+slug; anchor to serial/asset-tag; title may repeat (warn)", why: "labels collide; ids must not", acked: 2026-07-31 }
      - { case: "device replaced, role kept", decision: "role bean (stable) vs device bean (serial-anchored); retired → deprecated + role re-points via replaces:", why: "not silent id reuse", acked: 2026-07-31 }
  - term: ref
    meaning: "the LINK FORM {bean|mapping: <id>[, field: <key>]} — a pointer to the single owner of a value. The relations that USE this form declare themselves (see refs, depends_on, and a garden's own edges)."
    context_keys: []
    enforced_by: core
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
    meaning: "who said each value and how they know, keyed by the same dotted path merge_conflicts uses: {path: [{value, src, seen_in?, subsumed?, at?}]}. A subsumed value appears here and NOWHERE else, because the document carries only the winner. `at` is the value's own source, a pointer in the forms `provenance_record.from` gives (`pass_form.pointer`): where it is present it resolves, and the flow law judges it"
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
        accepted: { in: { type: position }, meaning: "the day this party accepted. Where they accepted and nobody said the day: `{ system: event-anchored, at: \"after:<what it followed>\", unit: day }`, placed by what it followed. Whose word it is, is the entry's provenance: the party's own word, or another person's report of it — never an inference" }
        during:   { in: extent, meaning: "when this party was a party, where that is not the agreement's whole life" }
        note:     { in: prose, meaning: "optional prose" }
        acting_for: { in: { key_of: parties }, meaning: "the party this one acts for: what it does binds that party — an employee, a lawyer, a parent" }
        declined:   { in: { type: position }, meaning: "the day this party refused the agreement, or withdrew from it; whose word it is, is the entry's provenance" }
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
        note: { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" }
    merge: { cardinality: set, order: none }
  - term: words
    meaning: "an agreement's own words: whether they were written, spoken, or not yet put into words; where they are; and the day it was agreed"
    context_keys: [words]
    schema:
      shape: mapping
      required_on_gene: [contract]
      attrs:
        form:   { required: true, in: [written, spoken, unstated], meaning: "written — a text exists, and `at` names the document that holds it, or `external` where it is held outside the garden | spoken — agreed aloud; `at` may name the happening | unstated — the agreement is named, and its terms have not been put into words" }
        at:     { in: ref, meaning: "the `document` that holds its text, or the `event` at which it was said" }
        external: { in: prose, meaning: "where its text is held, when the garden holds no document of it: the registrar's registration agreement, a bank's terms for a card — named as the record can name it, as a party the garden holds no bean for is" }
        agreed: { in: { type: position }, meaning: "the day it was agreed, in any calendar" }
        note:   { in: prose, meaning: "optional prose" }
      cells:
        - { when: { form: written }, requires: [[at, external]], why: "a written agreement can be found: name the document that holds it, or say where its text is held outside the garden" }
    merge: { cardinality: single, order: none }
  - term: clauses
    meaning: "what an agreement asks of its parties, one clause each: an open map keyed by a short name. A clause is a position on the `permission` aspect — required (must), omissible (need not), permitted (may), forbidden (must not) — the square of obligation a being's capabilities already take. A clause with no `by` is a rule of the agreement that binds every party"
    context_keys: [clauses]
    schema:
      shape: open_map_of_entries
      key_form: kebab
      expiry: { attr: due, relative: falls_due, lapses: during, condition: when, permission: permission, repeats: every, unless: { state: [met, waived, broken] }, notice: { of: time, measure: { count: 7, unit: day } },
                why: { required: "a clause falls due, and from that day the party it is owed to is owed it", permitted: "a permission opens: from that day the party may", forbidden: "a prohibition begins: from that day the party must not", omissible: "a clause the party need not keep comes into force" },
                lapses_why: { required: "an obligation's window closes: what was not done by then was not done in time", permitted: "a permission lapses: after that day the party may no longer", forbidden: "a prohibition ends: after that day it binds no longer", omissible: "a clause the party need not keep ends" } }
      at_most_one_of: [[due, falls_due], [by, by_role]]
      attrs:
        what:   { required: true, in: prose, meaning: "the clause in words, as its parties would say it" }
        by:     { in: { key_of: parties }, meaning: "the party it binds" }
        to:     { in: { key_of: parties }, meaning: "the party it is owed to" }
        within:  { in: extent, meaning: "with `amount`: the window the amount is counted within — a length that slides (`measure`), or cells of a level (`level`, `count`): ninety days within any hundred and eighty, twenty days in each year" }
        used_by: { in: { key_of: selections }, meaning: "with `within`: the entries whose extents use the allowance — a person's stays, their leave" }
        permission: { in: { aspect: permission, default: required }, meaning: "required | omissible | permitted | forbidden" }
        amount: { in: { quantity: any }, meaning: "how much, where it is measured — money, time, anything. Absent while unknown, and `what` then says how it will be known" }
        due:    { in: { type: position }, meaning: "the day, or the moment, it falls due — the first, when it repeats" }
        notice: { in: { quantity: duration }, meaning: "how long before it falls due a reader is told — this clause's own, where the agreement's (seven days) is too short: ninety days before a name lapses, sixty before a lease ends" }
        every:  { in: recurrence, meaning: "how it repeats: each month of a calendar, six times" }
        when:
          meaning: "what brings it into force, where that is not a day: a reading that holds — an entry made under another clause, a step reached, anything a selection says — or the condition in words, where no reading says it yet"
          in: { entries: { selection: { in: { key_of: selections } }, said: { in: prose } }, one_of: [selection, said], at_most_one_of: [[selection, said]] }
        state:  { in: [in-force, met, waived, broken, disputed], meaning: "in-force — it holds and is not yet discharged; the reading when it is silent | met | waived — released by the party it is owed to | broken | disputed — the parties disagree that it holds" }
        note:   { in: prose, meaning: "optional prose" }
        each:      { in: { key_of: selections }, meaning: "the clause OCCURS once for each bean or entry this selection holds — each sale, each booking — from the moment it entered; an occurrence never leaves: a refund is its own clause, the reverse, occurring for each refund. Its selection uses only conditions an occurrence cannot lose (`comparators[].monotone`)" }
        of:        { in: { type: field_path }, meaning: "with `each`: the path, read FROM each occurrence, to the amount this clause's `amount` is a share of — `over.thing>clauses.fee.amount`" }
        falls_due: { in: { entries: { from: { required: true, in: { type: field_path } }, after: { in: extent }, before: { in: extent }, at: { in: { pattern: '^[A-Za-z0-9-]+$' } } }, one_of: [after, before], at_most_one_of: [[after, before]] }, meaning: "instead of `due`: when it falls due RELATIVE to another position, read each time and never stored — `from` a path to a position (`@occurrence`, a moment of `timing`, another clause's `due`), `after` or `before` it by an extent (a measure, or cells of a level), then `at` the place the system writes in the cell reached (`10`), as `recurrence_form.at` names one" }
        during:    { in: extent, meaning: "the window in which it holds: a permission lapses at its end; an obligation holds within it" }
        by_role:   { in: { type: kebab }, meaning: "instead of `by`: every party whose `role` is this, each bound alike" }
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
        day:      { in: { type: position }, meaning: "the day it happened, where known" }
        paid_by:
          required: true
          meaning: "who paid, and how much each paid — one entry per party. A single payer may leave `amount` out: they paid the whole"
          in: { entries: { party: { required: true, in: { key_of: parties } }, amount: { in: { quantity: money } }, note: { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" } }, keyed_by: party }
        borne_by:
          meaning: "who bears it, one entry per party, in whole-number shares: two to one is 2 and 1. Absent: whoever paid bears it"
          in: { entries: { party: { required: true, in: { key_of: parties } }, share: { required: true, in: { pattern: '^[1-9][0-9]{0,39}$' } }, note: { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" } }, keyed_by: party }
        under:    { in: { key_of: clauses }, meaning: "the clause it was made under, or keeps" }
        through:  { in: ref, meaning: "the card, account or agreement it moved through — itself an agreement with whoever issued it" }
        category: { in: prose, meaning: "the person's own word for what kind of spending it was" }
        note:     { in: prose, meaning: "optional prose" }
        during:   { in: extent, meaning: "the period it is for: a month's fee, a season's share" }
        settles:  { in: { entries: { clause: { required: true, in: { key_of: clauses } }, occurrence: { required: true, in: { pattern: '^[a-z0-9][a-z0-9-]*(:[a-z0-9_][a-z0-9_-]*(\.[a-z0-9_][a-z0-9_-]*)*)?$' } }, amount: { in: { quantity: any } }, note: { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" } }, keyed_by: [clause, occurrence] }, meaning: "which occurrences of which clauses it settles, and how much of each: one payment across two rates, each under its own clause. With `settles`, `under` may be left out" }
        pin:      { in: { entries: { commit: { required: true, origin: { act: read, nature: soma }, in: { pattern: '^[0-9a-f]{7,40}$' } }, at: { required: true, origin: { act: read, nature: soma, by: save }, in: { type: position, unit: minute } }, garden: { in: { bean_id: { gene: [garden] } } } } }, meaning: "the commit and the moment the reading it settles was read at (`pin_form`)" }
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
    meaning: "the ordered steps a mapping performs: a WALK, whose steps say who acts at each, how long each usually takes, which are ways out, pauses and ends, and why a case may move into each"
    context_keys: [steps]
    schema:
      on_sequence: routine
      attrs:
        id:      { required: true, in: { type: kebab }, meaning: "the step's name, once in its walk" }
        do:      { required: true, in: prose, meaning: "what is done at the step, in words" }
        next:    { in: { entries: { to: { required: true, in: { type: kebab }, meaning: "the step it leads to" }, when: { in: prose, meaning: "when this way on is taken: said by each of two or more" }, note: { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" } } }, meaning: "the ways on from the step: a CLOSED neighbourhood, these and no others" }
        by:      { in: { type: kebab }, meaning: "who acts at the step: a key of the `parties` of the being whose course reaches it" }
        usually: { in: extent, meaning: "how long the step usually takes: an extent on `time` with a `measure`, `{ of: time, measure: {count, unit} }`, or counted in cells of a calendar's level, `{ of: time, in: <system>, level: <level>, count: <n> }` (`extent_form.level`)" }
        exit:    { in: [true], meaning: "a way out, reached from any step with no `next` naming it: withdrawn, cancelled, lost" }
        resumes: { in: [true], meaning: "a PAUSE, reached from any step with no `next` naming it: the move after it returns to the step it was entered from, or takes a way out" }
        final:   { in: [true], meaning: "an end nothing follows: a move after it is refused. An end that is not final may be left, and the case taken up again" }
        reasons: { in: any, meaning: "the reasons a move into this step may cite, as a list of kebab words, each once. Its form is the walk's to judge" }
        is:      { in: { type: coding }, meaning: "the published process the step is, where a scheme names one" }
        takes:   { in: { entries: { code: { required: true, in: { type: coding }, meaning: "the code, with its scheme" }, amount: { in: { quantity: any }, meaning: "how much, where it is measured" } }, keyed_by: code }, meaning: "what one run of the step takes in, each once" }
        gives:   { in: { entries: { code: { required: true, in: { type: coding }, meaning: "the code, with its scheme" }, amount: { in: { quantity: any }, meaning: "how much, where it is measured" } }, keyed_by: code }, meaning: "what one run of the step gives out, each once" }
        note: { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" }
    merge: { cardinality: single, order: none }
  - term: courses
    meaning: >
      Where this being stands on a WALK over time: each entry is a COURSE, a series along `time` whose positions are the
      moments of its `moves` and whose value at each is a step of the walk it names. Where the being stands now, how
      long it has stood there and who acts next are read from the moves, never stored.
    context_keys: [courses]
    schema:
      shape: open_map_of_entries
      key_form: kebab
      attrs:
        walk: { required: true, in: ref, meaning: "the document whose `steps` the course moves along: `{ mapping: <id> }`" }
        note: { in: prose, meaning: "optional prose" }
    merge: { cardinality: multi, order: by-key }
  - term: moves
    meaning: >
      Each move of this being along one of its `courses`: the step it reached, at what moment, who moved it, and why.
      A move is kept and never rewritten; where the being went next is the next move.
    context_keys: [moves]
    schema:
      shape: list_of_entries
      moves_along: course
      attrs:
        course:  { required: true, in: { key_of: courses }, meaning: "the course moved along: a key of `courses` on this bean" }
        at:     { required: true, origin: { act: read, nature: soma, by: save }, in: { type: position, unit: minute }, meaning: "the moment of the move, read from the clock: written `now`, and the save writes the moment of its journal heading" }
        step:   { required: true, in: { type: kebab }, meaning: "the step reached: a step of the course's walk" }
        by:     { required: true, in: bean_id, meaning: "who moved it" }
        reason: { in: { type: kebab }, meaning: "why, as one of the reasons the step reached lists in its `reasons`" }
        why:    { in: prose, meaning: "why, in words: owed where the walk's `next` does not offer the move" }
        note: { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" }
    merge: { cardinality: multi, order: by-course+at+step }
  - term: items
    meaning: "what a CHECKLIST asks for, one item each (a mapping of `kind: checklist`): what it is, who provides it, when it is needed, and what meets it. A checklist is a set and not a walk: its items have no order, and items of which any one will do share a `one_of`"
    context_keys: [items]
    schema:
      shape: list_of_entries
      attrs:
        id:          { required: true, in: { type: kebab }, meaning: "the item's name, once in its checklist" }
        do:          { required: true, in: prose, meaning: "what is asked for, in words" }
        by:          { in: { type: kebab }, meaning: "who provides it: a key of the `parties` of the being it is asked of" }
        needed_when: { in: { key_of: selections }, meaning: "when the item is needed: while the selection holds — a key of `selections` on this bean, or `<bean>:<key>` on another. Absent, it always is" }
        met_by:      { in: { key_of: selections }, meaning: "what meets the item: the beans the selection holds for — a key of `selections` on this bean, or `<bean>:<key>` on another" }
        one_of:      { in: { type: kebab }, meaning: "a group of alternatives: the items that share this name are met when any one of them is" }
        note:        { in: prose, meaning: "optional prose" }
    merge: { cardinality: multi, order: by-id }
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
    placement: location
    schema:
      shape: list_of_entries
      required_on_gene: [document]
      at_most_one_of: [[u, accuracy]]
      attrs:
        system:    { required: true, in: { registry: anchor_systems, take: system, where: { dimension: [place] } }, meaning: "which anchor system of place this position is stated in — it selects the form the position must take" }
        openness:  { required: true, in: [here, elsewhere, unreachable, unknown], meaning: "here (reachable from the machine that recorded it) | elsewhere (reachable, and NOT from here) | unreachable (known, and cannot be reached) | unknown (nobody has established where it is — beyond the being it is in, where `host` names one)" }
        observed:  { origin: { act: read, nature: soma }, in: { type: position, unit: day }, meaning: "ABSOLUTE date this location was checked. A location ages: a tree is moved, a branch is checked out elsewhere, a printout is filed." }
        u:          { in: { quantity: length }, meaning: "the position's HORIZONTAL standard uncertainty (`uncertainty_form`); for a position on one vertical axis, its only one" }
        u_vertical: { in: { quantity: length }, meaning: "the standard uncertainty of its height, where it states one: where most local ground motion is, and where a receiver is worst" }
        accuracy:   { in: { entries: { count: { required: true, in: { type: count } }, unit: { required: true, in: { registry: units, take: unit } }, kind: { required: true, in: { registry: accuracy_kinds, take: kind } } } }, meaning: "instead of `u`: the horizontal accuracy as the receiver stated it, with its kind" }
        zone:       { in: { registry: time-zones, take: zone }, meaning: "the civil time zone in force at this position, a zone of the IANA time zone database: an offset is READ from it for a moment, never stored (N8)" }
        at:        { in: { form_of: anchor_systems, keyed_by: system, take: pattern }, meaning: "the position itself, in that system's ONE canonical form. Required unless openness is `unknown`, which is precisely the case where there is no position to state." }
        note:      { in: prose, meaning: "optional prose — the only place a `physical` address can live, since that system declares no canonical form" }
        mobility:  { in: [fixed, free], meaning: "fixed — the being does not move, and is not moved, while `during` holds (a rooted tree, a set mark); free — it moves. Rootedness is a position over a time, never a kind" }
        during:    { in: extent, meaning: "when the being was at this position: a transplant is two entries, each with its window" }
        host:      { in: ref, meaning: "the being whose own frame the position is in — the machine a path is on, the server a repository is fetched from, the rack a slot is in. Stated alone where the position within it is not known (`openness: unknown`); beside `at`, it is the being the position names, and agrees with it" }
        takes:     { in: { entries: { count: { required: true, in: { type: count } }, unit: { required: true, in: { registry: units, take: unit } } } }, meaning: "what this placement takes of what its host can hold (`capacity`), each a measure in a unit of the capacity's quantity: 2 rack units, 400 gigabytes. Only a placement whose rung takes (`placement`) takes anything" }
      cells:
        - { when: { openness: here }, requires: [at] }
        - { when: { openness: elsewhere }, requires: [at] }
        - { when: { openness: unreachable }, requires: [at] }
    merge: { cardinality: multi, order: "by-system+at?" }
  - term: fixes
    meaning: "the boundaries of a system's cells this being FIXES by a mark in it (`fixing: marked`): each at a position along one of its own lines, and each the same boundary the system's table says is marked here — the two ends are held to each other"
    context_keys: [fixes]
    schema:
      shape: open_map_of_entries
      key_form: kebab
      attrs:
        system:   { required: true, in: { registry: anchor_systems, take: system }, meaning: "the system whose cells' boundaries its table (`boundaries_in`) lists" }
        boundary: { required: true, in: prose, meaning: "the boundary, as the system's table names it: the base of that cell" }
        level:    { required: true, in: { system: along }, meaning: "where on this being the mark is, along one of its own `lines`" }
        note: { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" }
    merge: { cardinality: multi, order: by-key }
  - term: lines
    meaning: "the LINES this being lends to positions along it (`along`): each with the point it starts from and the way it runs, once"
    context_keys: [lines]
    schema:
      shape: open_map_of_entries
      key_form: kebab
      attrs:
        zero:   { required: true, in: prose, meaning: "the point of the being the line starts from: the top of a core as it was taken, the pith of a stem" }
        toward: { required: true, in: prose, meaning: "which way it runs" }
        note:   { in: prose, meaning: "optional prose" }
    merge: { cardinality: multi, order: by-key }
  - term: timing
    meaning: >
      When something happened, as an OPEN map of moment-name -> a position in a time anchor system at a
      STATED resolution, and, where it is known, where (`where`). The resolution is declared, never inferred
      from how many digits were typed, so two positions whose resolutions overlap can be known to be
      unordered rather than silently ordered. One entry is also the long form of every day the law holds.
    context_keys: [timing]
    placement: time
    schema:
      shape: open_map_of_entries
      key_form: kebab
      required_on_gene: [session, event]
      attrs:
        system:  { required: true, in: { registry: anchor_systems, take: system, where: { dimension: [time, any] } }, meaning: "the time anchor system — gregorian-civil for a calendar reading, event-anchored for a position fixed only by its neighbours" }
        at:      { required: true, in: { form_of: anchor_systems, keyed_by: system, take: pattern }, meaning: "the position, in that system's ONE canonical form" }
        unit:    { required: true, in: { registry: units, take: unit }, meaning: "the resolution ACTUALLY HELD. `2026-08-07T05:21` recorded at unit: minute means the second is not known — not that it was zero." }
        by:      { in: prose, meaning: "optional: who or what read the clock, when that is not the bean's default provenance" }
        where:
          meaning: "WHERE the moment was: one place position beside its time — a moment is in time and in place together, and civil time is read from a place. The form a being's place takes (`located_at`), without what is a being's alone: whether it can be reached, and how long it stayed"
          in:
            entries:
              system: { required: true, in: { registry: anchor_systems, take: system, where: { dimension: place } }, meaning: "the place system it is stated in" }
              at:     { required: true, in: { form_of: anchor_systems, keyed_by: system, take: pattern }, meaning: "where, in that system's one form" }
              zone:   { in: { registry: time-zones, take: zone }, meaning: "the civil time zone in force there: the moment's offset is READ from it, never stored (N8)" }
              u:      { in: { quantity: length }, meaning: "how well the place is known: its standard uncertainty (`uncertainty_form`)" }
              note:   { in: prose, meaning: "optional prose" }
        note:    { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" }
    merge: { cardinality: multi, order: by-key }
  - term: series
    meaning: >
      What this being holds ALONG A SEQUENCE: each entry is a series, a line whose positions hold values. Its positions
      are given by a rule (`grid`, a recurrence) or listed (`span`, an extent, from whose `from` each row writes its
      offset in `unit`s); `holds` names what each position holds, one channel per column; the rows are one table. A
      series is the world along a line, at the position where it held.
    context_keys: [series]
    schema:
      shape: open_map_of_entries
      key_form: kebab
      series: true
      entry_one_of: [grid, span, held]
      attrs:
        grid:     { in: recurrence, meaning: "the positions BY RULE: a recurrence with a `from` and no `to` or `times`, striding by a measure or by a level with a length; row n is at occurrence n, the first at `from`, and the last row is its end" }
        span:     { in: extent, meaning: "the positions LISTED: the region the rows lie in, whose `from` is offset 0; each row writes its offset" }
        unit:     { in: { registry: units, take: unit }, meaning: "the resolution held, and what an offset counts: a row's offset and a grid's stride are whole numbers of it. On a COUNTED line (its system's neighbours counted) no unit is stated: an offset there is a count of neighbours, and nothing measures it" }
        placement: { in: [point, bounds, preceding, following], meaning: "where a row sits on the line: point — at its position, the reading when silent | bounds — over a region, a listed row writing its `from` and `to`, a grid's row n over [n, n+1) strides | preceding — at its position, over the region back to the row before | following — at its position, over the region on to the next" }
        holds:
          meaning: "the CHANNELS: what a position holds, one column each — a measured value, a position, or a code"
          in:
            keyed_by: name
            at_most_one_of: [[u, accuracy]]
            entries:
              name:       { required: true, in: { type: kebab }, meaning: "the column's heading, once in its series" }
              quantity:   { in: { registry: quantities, take: quantity }, meaning: "a MEASURED value: the quantity every cell is of, counted in `unit`" }
              unit:       { in: { registry: units, take: unit }, meaning: "with `quantity`, the one unit every cell is counted in; with `system` and `from`, what an offset from `from` counts" }
              system:     { in: { registry: anchor_systems, take: system }, meaning: "a POSITION: every cell is a position in this system, in its one form less the channel's `prefix` and `suffix` — or, with `from` and `unit`, a whole offset from `from`" }
              from:       { in: { form_of: anchor_systems, keyed_by: system, take: pattern }, meaning: "with `system` and `unit`: the position an offset of 0 is" }
              prefix:     { in: { type: text }, meaning: "with `system`: what every cell's position begins with, written once here" }
              suffix:     { in: { type: text }, meaning: "with `system`: what every cell's position ends with, written once here" }
              scheme:     { in: { registry: knowledge_schemes, take: scheme }, meaning: "a CODE: every cell is a code of this published scheme" }
              stands_for: { required: true, in: [point, mean, sum, min, max, state, instant], meaning: "what a cell stands for over its row's place: point — the value at the row's position | mean, sum, min, max — over the row's region | state — the value holds from the row until the next, or over the row's region | instant — something happened at the row's position, and nothing is held between rows" }
              between:    { in: [none, linear], meaning: "what is read between two rows: none, the reading when silent | linear — on a straight line between two neighbouring readings of a point, only where the line and the channel are both metered" }
              u:          { in: { quantity: any }, meaning: "the standard uncertainty of every cell, in a unit of what the cell measures: a value read with it is printed to its digits" }
              accuracy:   { in: { entries: { count: { required: true, in: { type: count }, meaning: "the accuracy stated: an accuracy with no number states nothing" }, unit: { required: true, in: { registry: units, take: unit }, meaning: "its unit" }, kind: { required: true, in: { registry: accuracy_kinds, take: kind }, meaning: "its kind, a row of `accuracy_kinds`" } } }, meaning: "an accuracy as its maker stated it, with its kind (`uncertainty_form`), never beside `u`: the reader turns it into an uncertainty, a writer never does" }
              persists:   { in: [none, offset, scale, unknown], meaning: "whether one cell's error repeats in the next: none | offset — a common offset, which cancels in a difference | scale — a common relative error, which scales a difference | unknown, read both ways" }
              monotone:   { in: [increasing, decreasing], meaning: "the channel never goes back along the line: a row that does is refused, unless its cell is excluded" }
              limits:     { in: { entries: { below: { in: { type: count }, meaning: "what a bare `<` is below" }, above: { in: { type: count }, meaning: "what a bare `>` is above" } } }, meaning: "the limits a bare `<` or `>` in a cell stands for" }
              property:   { in: { type: coding }, meaning: "WHAT the channel is of, as a code of a published scheme, so that two gardens' channels meet by code and never by name" }
              note:       { in: prose, meaning: "optional prose" }
        rows:     { in: { type: rows }, meaning: "the table, inline: its header names the position columns (`at`, or `from` and `to` under `bounds`; none on a grid) and each channel once, then one line per row. Absent, the rows are the parts `series/<bean>/<key>/<part>.tsv`: a grid's part named by the number of its first row, a listed series' by any kebab name" }
        excluded: { in: { entries: { at: { required: true, in: { type: count }, meaning: "the row: its offset on a listed series (its `from` under `bounds`), its number on a grid, the first 0" }, channel: { in: { type: kebab }, meaning: "the cell's channel; absent, every cell of the row" }, by: { required: true, in: bean_id, meaning: "the judge who set it aside" }, why: { required: true, in: prose, meaning: "why" }, note: { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" } } }, meaning: "a cell SET ASIDE by a judge: kept and shown, and read by no operation" }
        held:     { in: { pattern: '^root:[a-z0-9][a-z0-9-]*/[A-Za-z0-9][A-Za-z0-9._-]*$' }, meaning: "the whole series is kept OFF GIT, in the held layer, under this opaque pointer, and the entry says nothing else" }
        whole:
          meaning: "what the series is AS A WHOLE, made of what its positions hold: the value, the channel it is made of, and how (`by`, an aggregate) — two nodes of 2 are a whole of 4 `by: sum`, and of 4 `by: product`. Checked exactly, in fractions, against the rows; a row that holds a gap leaves a whole that cannot be checked, and says so"
          in:
            entries:
              value: { required: true, in: { quantity: any }, meaning: "the whole, a measured value in a unit of the channel's quantity (`count` is in `item`)" }
              of:    { required: true, in: { type: kebab }, meaning: "the channel it is made of, by its name" }
              by:    { required: true, in: { registry: aggregates, take: aggregate }, meaning: "how the parts make the whole" }
        note:     { in: prose, meaning: "optional prose" }
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
        system:    { required: true, in: { registry: anchor_systems, take: system, where: { dimension: [place] } }, meaning: "which filesystem system this host resolves the root in — pinned to the grammar this host's `os` declares, so it is checked rather than merely stated" }
        at:        { required: true, in: { form_of: anchor_systems, keyed_by: system, take: pattern }, meaning: "the literal position this root means HERE, host named, in that system's canonical form" }
        observed:  { origin: { act: read, nature: soma }, in: { type: position, unit: day }, meaning: "ABSOLUTE date the resolution was checked — a tree gets moved" }
        note:      { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" }
        keeps:           { in: [none, personal, special-category], meaning: "the most sensitive material this root may hold as a store of the held layer — `none` for material that is neither; absent, the root is no store" }
        controller:      { in: { bean_id: { gene: [person, org] } }, meaning: "who controls the store: the subject, for special-category material (D4)" }
        confidentiality: { in: { aspect: confidentiality, default: cleartext }, meaning: "whether the store protects what is in it at rest" }
        readable_from:   { in: [this-host, lan, remote], meaning: "where what is in it can be read from: this host only, its network, or a party outside the garden (a synced folder)" }
        backup:          { in: prose, meaning: "how the store is backed up, now that git no longer is its backup" }
      cells:
        - { when: { keeps: special-category, confidentiality: cleartext, readable_from: remote }, verdict: in_breach, why: "special-category material stored in cleartext where a party outside the garden reads it" }
    merge: { cardinality: multi, order: by-key }
  - term: roles
    meaning: "the jobs this being does, each a row of the `roles` registry"
    context_keys: [roles]
    schema:
      shape: list_of_entries
      attrs:
        role:      { required: true, in: { registry: roles, take: role }, meaning: "which job — a registry row, so a typo is an error and not a new role" }
        observed:  { origin: { act: read, nature: soma }, in: { type: position, unit: day }, meaning: "ABSOLUTE date the role was confirmed to be one this being actually performs" }
        why:       { in: prose, meaning: "optional: what this being does in that role that another in the same role would not" }
        note: { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" }
    merge: { cardinality: multi, order: by-role }
  - term: os
    meaning: "the operating system this machine runs — a row of the `operating_systems` registry. Its release is not part of the value: it is written in `owns.os_release`, beside the day it was read"
    context_keys: [os]
    schema:
      shape: scalar
      values_from: "registry:operating_systems[].os"
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
        observed:    { origin: { act: read, nature: soma }, in: { type: position, unit: day }, meaning: "ABSOLUTE date the layout was read off the machine" }
        carried_by:  { in: { key_of: volumes }, meaning: "the `volumes` key beneath this one. A local key and NOT a ref: the stack is intra-bean, which is why it joins no acyclic check." }
        uuid:        { origin: { act: read, nature: soma }, in: { pattern: "^[0-9A-Za-z][0-9A-Za-z:-]*$" }, meaning: "the volume's own identifier, as its format reports it. The datum a rebuild needs and the one that survives a device rename." }
        at:          { in: { pattern: "^(/[^ ]*|[A-Za-z]:[/\\\\].*)$" }, meaning: "where it is mounted, in this machine's path grammar. Absent for a volume that holds no filesystem — a LUKS container or an LVM member is mounted nowhere." }
        note: { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" }
    merge: { cardinality: multi, order: by-key }

  - term: beanger
    meaning: >
      A per-datum ledger: what a datum IS, which field on this bean holds its CURRENT value, how to read
      it, and the append-only log of every operation on it — each stamped to the millisecond, attributed,
      and linked to the one before. It is one field's own log, at the moment it was recorded: what the
      world held along a line — a reading at each moment, a porosity at each depth — is a `series`.
    context_keys: [beanger]
    schema:
      shape: open_map_of_entries
      key_form: kebab
      attrs:
        defines:  { required: true, in: prose, meaning: "WHAT this datum is, structurally — the part that stays true across every value it will ever hold. Written so a reader who has never seen the machine can tell which reading would refresh it." }
        tracks:   { required: true, in: { pointer: bean_field_pointer }, meaning: "a pointer to the field holding the CURRENT value — `<section>.<key>` on this bean. The value is NOT copied here: it lives in one place and this names it." }
        source:   { required: true, in: prose, meaning: "the exact command or file the value is read from, so the next scan reads THE SAME THING. Without it a differing value cannot be told from a differing METHOD — as when /sys/class/net reports a bond's MAC where ethtool -P reports the NIC's." }
        records:
          required: true
          meaning: "the append-only log, OLDEST FIRST. Each record is an entry, and is held to these attributes like any other."
          in:
            entries:
              seq: { required: true, in: { pattern: "^[1-9][0-9]*$" }, meaning: "1-based position in this datum's log. The identity `prev` points at." }
              at: { required: true, origin: { act: read, nature: soma }, in: { system: unix-epoch }, meaning: "the moment of the RECORD, epoch MILLISECONDS (see the `unix-epoch` anchor system). Milliseconds because two operations in one session can land in the same second and their order is the thing being recorded." }
              unit: { in: { registry: units, take: unit }, meaning: "the resolution the moment was ACTUALLY held to — a row of `units`. Defaults to millisecond for anything this ledger stamped itself. A record reconstructed from a date carries `unit: day` and an `at` of that day's midnight, so that thirteen digits of apparent precision cannot be mistaken for thirteen digits of knowledge. This is the same rule `timing` applies." }
              op: { required: true, in: [add, change, remove, confirm], meaning: "add | change | remove | confirm. `confirm` is the only one that does not move the value." }
              value: { in: any, meaning: "the value AS OF this record. Present on add and change; on `confirm` it is omitted, because repeating an unchanged value is the duplication this design removed. On `remove` it is omitted for the same reason — the outgoing value is already on the record before." }
              prev: { in: { pattern: "^([1-9][0-9]*|None)$" }, meaning: "the `seq` of the record before, or null on the first. The BACK link only: forward is list order, and storing both would let them disagree." }
              who: { required: true, in: { pattern: "^((agent|tool|human):[^ ].*|[^ :][^:]* \\(.+\\))$", soft: true, why: "attribution has one convention across the ledger" }, meaning: "who performed it, in `provenance.by` form — `sam (operator)` for a person, `agent:<model>/<garden>` for an agent. One convention for attribution across the ledger, not a second." }
              from_where:
                meaning: "the CURSOR the operation was performed FROM: `{host, session, guide}` — which machine, which working session, and which context the person working had in attention. All three are bean refs where a bean exists."
                in:
                  entries:
                    host: { in: bean_id, meaning: "which machine" }
                    session: { in: bean_id, meaning: "which working session" }
                    guide: { in: bean_id, meaning: "which context the person working had in attention" }
              to_where: { in: ref, meaning: "what the operation was performed ON, as a bean ref, where that differs from the bean carrying the beanger. Absent for a plain local read." }
              why: { in: prose, meaning: "optional: what caused the change. Load-bearing on `change` and `remove`, where the value alone does not say what happened." }
        note: { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" }
    merge: { cardinality: multi, order: by-key }

  - term: workspace
    meaning: "the working copy and branch a session commits from, on a named host"
    context_keys: [workspace]
    placement: location
    schema:
      shape: mapping
      required_on_gene: [session]
      attrs:
        host:       { required: true, in: ref, meaning: "a {bean} ref to the machine the session ran on. A session is not portable: its shell history, its reachability and what it could measure all belong to one machine." }
        system:     { required: true, in: { registry: anchor_systems, take: system, where: { dimension: [place], datum: host } }, meaning: "the filesystem the working copy is in — the host's own: `unix-filesystem`, `windows-filesystem`" }
        at:         { required: true, in: { form_of: anchor_systems, keyed_by: system, take: pattern }, meaning: "the working copy, as a position in that system's one form — `root:` form where a root exists, so it resolves on a second machine rather than reading as a literal path that is not there." }
        branch:     { required: true, in: { pattern: "^[A-Za-z0-9][A-Za-z0-9._/-]*$" }, meaning: "the git branch it commits to. `session/<slug>` by convention; `master` for a session that works the main copy directly." }
        opened_at:  { origin: { act: read, nature: soma }, in: { system: unix-epoch }, meaning: "epoch milliseconds, stamped by bin/dmsession.py. A session's own start is the one moment nobody should be estimating." }
        note: { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" }
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
        source:         { required: true, in: prose, meaning: "the EXACT command that produced it, so it can be produced again and compared. The same argument `beanger.source` makes: naming the command is what gets it run." }
        taken_at:       { required: true, origin: { act: read, nature: soma }, in: { system: unix-epoch }, meaning: "epoch milliseconds — a capture with no moment cannot be told from a guess." }
        staleness_key:  { required: true, in: prose, meaning: "how a reader decides whether this still holds: a config version, a change counter, a hash of the live export. The same job `analysis_cache.staleness_key` does for code, which is where this shape comes from rather than being invented beside it." }
        redactions:     { required: true, in: prose, meaning: "WHAT WAS REMOVED and why. REQUIRED. Write `none — the source emits no secrets` explicitly if that is true; the point is that it is a claim, not a default." }
        holds:          { required: true, in: prose, meaning: "the content itself for something small, or a `file:` pointer into the garden for something large. Large captures do not belong inline: a bean must stay legible on paper, and a 900-line router export is not." }
        restores:       { in: prose, meaning: "optional: what this capture would let somebody rebuild, and what it would NOT. The honest half is usually the second." }
        supersedes:     { in: { key_of: capture }, meaning: "optional: the `capture` key on this bean that this one replaces" }
        note:           { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" }
    merge: { cardinality: multi, order: by-key }

  - term: observations
    meaning: "what was found of a being, one entry per reading, modelled on ISO 19156: a PROPERTY coded in a published scheme, OF this being or a coded part of it, PRESENT or absent, AT a moment or DURING a stretch, with its RESULT — a value with its u, a code, a position, an extent — how it was read, and BY whom. A reading made again is another entry: growth, drift and recovery are read, never stored. The world at the moment it held; `beanger` is one field's own change log at the moment it was written. An entry that ANSWERS another is a verdict on it, and one observer gives one verdict on one entry"
    context_keys: [observations]
    schema:
      shape: open_map_of_entries
      key_form: kebab
      entry_one_of: [at, during, answers]
      at_most_one_of: [[value, code, position, extent], [at, during]]
      attrs:
        property:  { in: { type: coding }, meaning: "what was observed: a code of a published scheme — never a garden's own word — so that two gardens' readings meet. Every reading states one; a verdict takes it from the entry it answers" }
        of:        { in: { type: coding }, meaning: "the part of this being the reading is of, as a code; absent, the whole being" }
        presence:  { in: [present, absent], meaning: "present — found (the reading when silent); absent — looked for and not found: a list that does not name it, a sign not seen. An absent entry states no result" }
        at:        { in: { type: position }, meaning: "when it held: the moment of the phenomenon, at the unit its form is written in — not when it was written down, which is provenance" }
        during:    { in: extent, meaning: "when it held, where that is a stretch: a day's intake, a season's growth" }
        value:     { in: { quantity: any }, meaning: "a measured result, with its `u` or `accuracy` inside it" }
        code:      { in: { type: coding }, meaning: "a classified result" }
        position:  { in: { entries: { system: { required: true, in: { registry: anchor_systems, take: system }, meaning: "the system the position is in" }, at: { required: true, in: { form_of: anchor_systems, keyed_by: system, take: pattern }, meaning: "the position, in that system's one form" }, u: { in: { quantity: any }, meaning: "its standard uncertainty" } } }, meaning: "a result that is a position: a temperature on a scale, an age before the present" }
        extent:    { in: extent, meaning: "a result that is a region" }
        method:    { in: { type: coding }, meaning: "how it was read, as a code" }
        by:        { in: bean_id, meaning: "who or what observed it — a person, an instrument — as a bean, so that its standing can be read (N19)" }
        answers:   { in: { type: field_path }, meaning: "the entry this one is a verdict on, `<bean>:observations.<key>` (N20)" }
        answer:    { in: [confirms, disputes, abstains], meaning: "with `answers`: confirms | disputes | abstains — asked, and would not say" }
        retracted: { in: { type: position }, meaning: "the day its own observer withdrew it: kept, and read by no reading after that day. A retraction is its observer's own word, so the entry carries a provenance of its own, stated by a person" }
        sample:    { in: bean_id, meaning: "a specimen taken from this being that it was read on" }
        pin:       { in: { entries: { commit: { required: true, origin: { act: read, nature: soma }, in: { pattern: '^[0-9a-f]{7,40}$' } }, at: { required: true, origin: { act: read, nature: soma, by: save }, in: { type: position, unit: minute } }, garden: { in: { bean_id: { gene: [garden] } } } } }, meaning: "the commit and the moment the readings it rests on were read at (`pin_form`, N2)" }
        note:      { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes" }
      cells:
        - { when: { answer: [confirms, disputes, abstains] }, requires: [answers], why: "a verdict names the entry it is a verdict on" }
    merge: { cardinality: multi, order: by-key }

  - term: hearings
    meaning: "a disagreement heard before it is ruled on: the entries that disagree, each speaker's own statement, and the ruling — which the gate refuses until every speaker of the entries has been heard"
    context_keys: [hearings]
    schema:
      shape: open_map_of_entries
      key_form: kebab
      attrs:
        over:   { required: true, in: { entries: { path: { required: true, in: { type: field_path }, meaning: "`<bean>:<term>.<key>`" } } }, meaning: "the entries that disagree, each `<bean>:<term>.<key>`" }
        heard:  { in: { entries: { speaker: { required: true, in: bean_id, meaning: "who spoke" }, said: { required: true, in: prose, meaning: "what they said, in their own words" }, at: { in: { type: position }, meaning: "when" }, note: { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" } }, keyed_by: speaker }, meaning: "each side's statement, in their own words" }
        ruling: { in: { entries: { by: { required: true, in: { bean_id: { gene: [person, org] } }, meaning: "who ruled" }, what: { required: true, in: prose, meaning: "the decision" }, at: { in: { type: position }, meaning: "when" }, note: { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" } } }, meaning: "the decision, by whom" }
        note:   { in: prose, meaning: "optional prose" }
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
        found:        { in: { type: position }, meaning: "ABSOLUTE date the finding was first made." }
        resolution:   { in: prose, meaning: "on `resolved` / `superseded`: WHAT settled it. A closed risk that does not say how is a risk a reader must re-open to trust." }
        resolved:     { in: { type: position }, meaning: "ABSOLUTE date it was settled." }
        note:         { in: prose, meaning: "optional: history, partial resolutions, and what a reader would otherwise re-derive." }
    merge: { cardinality: multi, order: by-key }
  - term: selections
    meaning: "the readings this bean declares (`selection_form`): which beans or entries of the garden it selects and what it computes from them — how many, whether any, which first, how much — each under a name a clause, a checklist, a grant or a page names it by (`key_of: selections`). Read by bin/dmreckon.py each time, never stored"
    context_keys: [selections]
    schema:
      shape: open_map_of_entries
      key_form: kebab
      attrs:
        what:   { required: true, in: prose, meaning: "what it selects, in the words a person checks it against" }
        inputs:
          meaning: "what it takes from outside what the garden holds (`selection_form.inputs`)"
          in:
            entries:
              name:     { required: true, in: { type: kebab } }
              origin:   { required: true, in: origin, meaning: "`{act: read, nature: soma, by: reader}`, the clock; `{act: said, nature: lekton, by: garden}`, another garden; any other, a value the asker gives" }
              type:     { in: { registry: value_types, take: type }, meaning: "with `given`: the form of the value" }
              quantity: { in: { registry: quantities, take: quantity }, meaning: "with `given`: the quantity it measures" }
              garden:   { in: { bean_id: { gene: [garden] } }, meaning: "with `garden`: the garden read" }
              path:     { in: { type: field_path }, meaning: "with `garden`: what is read there, `<bean>:<path>`" }
              note:     { in: prose }
            keyed_by: name
        zone:   { in: { registry: time-zones, take: zone }, meaning: "the civil time zone a calendar level is read in (`selection_form.zone`)" }
        steps:  { required: true, in: any, meaning: "the operations, in order, each `{id, op, ...}` with what its row of `operations` takes — judged against that row by bin/dmreckon.py's check, called by the gate" }
        note:   { in: prose }
    merge: { cardinality: multi, order: by-key }
  - term: standing
    meaning: "the layer a file of a garden sits in, for a file the law's `layers` do not place: a garden's own words, an agent's handover, a document of its own. An entry that places a file the law places elsewhere is refused"
    context_keys: [standing]
    schema:
      shape: list_of_entries
      attrs:
        doc:      { required: true, in: { pattern: '^file:\S+$' }, meaning: "the file, or a pattern of files matched as a release's list of what it ships is matched: a star crosses a slash" }
        standing: { required: true, in: { registry: layers, take: layer, where: { files: true } }, meaning: "the layer, one that holds files" }
        why:      { required: true, in: prose }
        since:    { in: { type: position }, meaning: "the day the file took this place" }
        note: { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" }
    merge: { cardinality: set, order: none }
  - term: sensitivity
    meaning: "how much harm this bean can do a person if it leaves the garden, where a person RAISES it above what the law derives. What is derived is never stored (bin/dmpass.py `sensitivity`): SPECIAL-CATEGORY — a code of a scheme marked `sensitive`, or a capture or series such a bean points at; PERSONAL — a record `about` a person who is not the gardener, or an observation of one. A mark below the derived one is a safety change (Contract E): only a person's own word lowers it"
    context_keys: [sensitivity]
    schema:
      shape: mapping
      attrs:
        is:  { required: true, in: [none, personal, special-category], meaning: "none | personal | special-category" }
        why: { required: true, in: prose }
    merge: { cardinality: single, order: none }
  - term: consent
    meaning: "the agreement in which this person consented to be kept by name in the git of the garden that holds it: a `contract` whose `parties` hold them with `accepted`, their own word. None is needed from a person who keeps a garden this one has met — the owner of a `garden` bean here, who gave their name in the exchange of ids that peered the two, trusted there by the gardener who recorded it (class F) — nor from a party who accepted an agreement held here. A person's name crosses to another garden only as far as their word reaches: `bin/dmpropose.py make` refuses the rest, and the other garden's gate asks again. Without either, a person who is not the gardener is kept in git only under an opaque id, and what names or reaches them is held off git (`held_form`); their future whereabouts are held off git whatever they consented to"
    context_keys: [consent]
    schema:
      shape: mapping
      only_on_gene: [person]
      attrs:
        bean: { required: true, in: { bean_id: { gene: [contract] } }, meaning: "the agreement in which they accepted" }
    merge: { cardinality: single, order: none }
  - term: about
    meaning: "the persons this record concerns — its data subjects — whoever owns the record or its copies: a certificate about a client, a note about a colleague. Whom it is personal to, what a person may ask to be shown, and what an erasure for them takes are read from it"
    context_keys: [about]
    schema:
      shape: list_of_entries
      attrs:
        who:  { required: true, in: { bean_id: { gene: [person] } }, meaning: "the person it concerns" }
        note: { in: prose }
    merge: { cardinality: multi, order: by-who }
  - term: grants
    meaning: "who, besides the gardener, may read, write, act on or ratify what: one grant each. CLOSED BY DEFAULT: nobody but the gardener may do what no grant opens. A grant is the decision of whoever holds it — the gardener's on the gardener's own bean, a person's on her own bean for her own record, an agreement's on its bean, over its own bean and what a party who accepted it owns or is the record of, and over nothing else. A `forbidden` grant is a refusal no `permitted` one passes: held by the gardener, a ceiling; held by a person on her own bean, her own no. Read by bin/dmpass.py (`may`) and by no copy"
    context_keys: [grants]
    schema:
      shape: open_map_of_entries
      key_form: kebab
      attrs:
        act:       { required: true, in: { pattern: '^(read|write|act:[a-z0-9][a-z0-9-]*|ratify:[A-K])$' }, meaning: "read | write — change it through a save | act:<tool> — run that tool, by the name the host's configuration gives it | ratify:<class> — decide that class of the Contract of Parts (MODEL.md) for what it is over, as the gardener's own act" }
        over:      { in: { key_of: selections }, meaning: "the beans it is over, a selection; absent, the bean that holds the grant" }
        positions: { in: { entries: { path: { required: true, in: { type: field_path } } } }, meaning: "which positions of them: `title`, `located_at`, `observations.*`; absent, every position — `title`, `summary`, the body and every term" }
        audience:  { required: true, in: { entries: { who: { in: { bean_id: { gene: [person, org] } } }, selection: { in: { key_of: selections } } }, one_of: [who, selection], at_most_one_of: [[who, selection]] }, meaning: "to whom: a person or an organisation the garden holds, or every member of a selection" }
        permission: { in: { aspect: permission, default: permitted }, meaning: "permitted — it opens; forbidden — nothing opens what it covers" }
        during:    { in: extent, meaning: "when it holds, on `time`; absent, from now on" }
        reason:    { in: [asked], meaning: "asked — each use states a reason, which the guard records" }
        why:       { required: true, in: prose }
        note: { in: prose, meaning: "optional prose. THE place for it: an entry holds only declared attributes, so a remark is written here and never as a new key" }
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
    identifier_forms: [minted, issued]
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
    identifier_forms: [minted]
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
    meaning: "words or figures fixed in a form that can be kept and handed on: a statement, a letter, a scanned sheet, a conversation kept as a transcript. Identified by its home's reference (`identifier`) or by its content (`content_hash`); where its copies are is `located_at`. What must not be kept whole — a card number — stays out of it, and a redacted copy of its lines is a `capture` on it."
  - genos: event
    of_nature: lekton
    ownership_form: [crown]
    takes_time_of: [present, host]
    meaning: "a happening between people at a time: a meeting, a dinner, a party, a conversation in which something was agreed. When is `timing`; who took part is `refs`, each naming what they were in `rel` — present, invited, host, paid, or any other part a person played. A happening between people is owned by none of them — it may end at the crown — and whoever hosted it answers for it."
---
# daftar — Tier-0 Universal Standard Vocabulary

The portable, estate-agnostic classification shared by every garden — the abstract model of *types* (data + process) and *anchors* (identity classes). Gardens pin a version in their own `VOCAB.md` / `GARDEN.md` and add only local terms/exceptions there.

**Anchor classes.** An anchor establishes identity if and only if it carries `establishing: true`. Which classes may establish for a bean is stated once, in the front matter: the classes are the `anchor_class` term's values, each nature's family is its row in `natures`, and `identity_policy.establishing_family` says the gate holds a confirmed bean to it. This prose restates none of them. See `MODEL.md`.

**Growth:** a garden-local term that proves general is **promoted** here by a pull request to the daftar repository (`CONTRIBUTING.md`): propose, show the neighbourhood, a person ratifies, and the version moves. Its version history is `seed/CHANGELOG.md`.

