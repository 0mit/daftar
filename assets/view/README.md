# view — a page of drawings, with the garden's live values beside them

`view` is the asset of the `view` profile. A garden that extends the profile receives it at `assets/view/`, and a
garden that leaves the profile has it taken away:

    python3 bin/dmupgrade.py <the release GARDEN.md records> --extend view     # or --retract view
    python3 seed/germinate.py <new-garden> --gardener <id> --profile network --profile knowledge --profile view

Extending a profile is a RULE-CHANGE, the gardener's to ratify: the upgrade writes `extends_profiles` in VOCAB.md,
brings the asset, journals it and runs the gate, and commits nothing. The asset's files are the release's; an edit to
one is a RULE-CHANGE, as an edit to any tool the release ships is.

## What it draws

A **page** is the one bean that carries `view`. It names the garden's own **drawing module** (`view.drawings`, a
`file:` pointer to a Python file inside the garden, with no `..`) — the garden's code, never the release's — and lists
what it draws in `views`, one entry per drawing, under the key the module draws it by.

**The drawing module is code the view host runs**, and so is every adapter under `lib/sources/`: whoever may change
one may run code on the host, and the host runs it again on each new commit that passes `dmview check`. So a garden
served to more than its gardener keeps the module the gardener's — at a hub, `bin/dmhub.py` asks `ratify:G` for a
change to it, to the name `view.drawings` gives, and to any Python file — and the host serves a clone only the hub
writes to. Each entry `draws` a mapping (a procedure) or a bean the garden holds, and says:

- its **story**, for someone who has never touched it: `purpose`, three to five `stages` (each with the `beings` that
  do it and the technologies it `uses`, each opening its own documentation), and its `outcome`;
- the **question** it asks at each lens (`questions`);
- its **operate shape** (`archetype`, a row of the law's `view_archetypes`) and what the shape reads;
- what the page **cannot see** of it (`blind`, never omitted), and where a person may **act** (`actions`);
- where the processes and pipes of what it draws are stated (`processes`, `pipes`: a pointer each, into the being's
  own record) — a process a row of `{proc, user, role, config}`, a pipe a row of `{from, to, channel, at, config}`,
  either with a `rail` (the direction work moves), a `note`, and `state: idle` where it exists and carries nothing.

A drawing is read at four **lenses**, the law's `view_lenses`: orient (a story), understand (the drawing itself),
operate (the shape's vital sign), inspect (a card of each part's own facts, the wiring, the steps). `view.fields` says,
per genos, which of a being's own facts its card shows, from which lens on; `view.reference` lists the parts a reader
looks up, each with the place system whose position stands for it. The position is the being's own — its
`located_at`, its anchors, its `endpoints` — and the page chooses it, never states it.

A drawing carries **no address**. The kit's `node()` takes an address argument and never draws it; a being's
addresses are on its card, for a viewer who may see them. `dmview check` refuses a drawing whose text shows one.

## The drawing module

    from view_kit import node, store, gate, flow, elbow, tag, action_btn, band, gauge, ribbon, boundary, figure, note

    def orders():
        b = [node(20, 50, 180, 48, "Customer", "places an order", cls="ext"),
             node(380, 50, 200, 48, "Oven", "bakes the order", bean="oven-a"), ...]
        return ("Orders", figure(600, 170, "".join(b), "an order, baked"), "A <b>caption</b>.", "The claim.")

    COMPOSERS = {"orders": orders}

Every kit call records what it drew: its pattern, its id (the slug of its label, unique in the drawing — pass
`eid=` to choose one), its box and the being it depicts (`bean=`). A binding and an action address an element by that
id; `dmview elements <view>` lists them. A node's bar is coloured by the nature of the being it depicts, or by `cls`:
`ext` (outside the garden's hands), `accent` (the one point the drawing turns on), `off` (wired, not running).
`templates/drawings.py` is a module to start from. The meaning of each pattern, for the legend, is the kit's own
(`view_kit.PATTERNS`).

## The operate shapes, and what each reads

A value a shape reads is the key of a `view_bindings` entry on the page.

| archetype | reads |
|---|---|
| reservoir | `fill`, `thresholds` (a share of the whole, and what each does), `forecast`, `also`, `parts` |
| lanes | `lanes` (each path, and the hops it must get through) |
| roster | `per_item` (a live-series), `active_over`, `top`, `parts` |
| gauges | `per_item`, `min`, `max` |
| board | `facts`, `members` (each part, the values that say its state, one fact, why an unmeasured part is not measured) |
| scoreboard | `numbers`, `list`, `parts` |
| funnel | `funnels` (each stream's stages, stops and marks), `window`, `numbers`, `rollcall` |
| race | `step_at` (0 before the first step, n at the n-th of the procedure it draws), `elapsed`, `eta`, `progress`, `deadline` (an extent) or `deadline_from`, `checkpoints`, `numbers`, `parts` |
| health-chain | nothing of its own: a tile per bound element, and a blind spot for every part nothing measures |
| table | the members of one reading (`selection`) or the rows of one series (`series`, a `{bean, field}` pointer), one line each, and its `columns` (a field path of each member, or a channel and `at`) |

Any shape may add `correlate`: values on one time axis (`traces`), how far back (`span`, an extent) and how often
(`every`, a recurrence), a step value that shades every trace (`band`), and one value binned against another
(`relate`). The gate refuses a shape without what it answers with, a length written as a bare number, and a stride
on a walk with no meter.

## Live values, and the monitors they come from

A **binding** (`view_bindings`) sits on one element of one drawing and is one of three kinds: `live-state` (whether
a being answers, as its monitor reaches it), `live-value` (one number) or `live-series` (many, each an item). Its unit
is a row of the law's `units` — a unit the law does not have is a row the garden adds to `units` in VOCAB.md — and its
`warn` and `crit` are counts in that unit. How it is computed is one `query` entry per technology, in that
technology's own language.

The page's **monitors** (`view_monitors`) are beings the garden holds. What a monitor watches is its own `reaches` and
each target's own `endpoints`; which technology it runs is its own `knowledge` (`uses`). The asset reads it through
the **adapter** for that technology: `lib/sources/<code>.py`, named by a code of the technology catalogue. The first
adapter reads Prometheus; `http` reads one JSON document at JSON Pointers (a device's own API, a runner's status
file); another technology is read by an adapter beside it, and a binding may give a query for each. What only one technology needs sits where the monitor's `settings` pointer points, read by its adapter as the
adapter's own docstring says.

An adapter is a module with `TECHNOLOGY` (its catalogue code) and these functions: `describe(binding)` (the query that
computes a shown number: its path), `check_binding(binding)` and `check_monitor(monitor)` (what it cannot read),
`selector(scope)` (a viewer's scope in its own language), `values(url, binds, selector)` and
`history(url, binds, selector, hours, step, now)` (what the served page shows), `alerts(settings, beings, binds)`,
and, where it deploys anything, `bundle(monitor, views, out)`.

## Commands

    python3 assets/view/bin/dmview.py check                       # the page against the law and its drawings
    python3 assets/view/bin/dmview.py elements <view>             # a drawing's elements
    python3 assets/view/bin/dmview.py report --out map/page.html  # the offline page, with the author mode
    python3 assets/view/bin/dmview.py import view-selection.json  # the author mode's selection, written and journalled
    python3 assets/view/bin/dmview.py bundle --out <dir>          # a monitor's deployment, written by its adapter
    python3 assets/view/bin/dmview.py serve-init --config <file> --user <name> [--bean <person>] [--orgs "*"|org-a] [--shared] [--no-actions]
    python3 assets/view/bin/dmview.py serve --config <file>       # the served page and the action executor
    python3 assets/view/bin/dmview.py render <view> --out <dir> [--member <bean>] [--keep --who <who>]
    python3 assets/view/bin/dmview.py ics <view> --out <file.ics> --config <file> [--user <name>]
    python3 assets/view/bin/dmview.py run-scheduled --config <file> [--at <day>]   # what a host's daily timer calls

`check` refuses what the gate cannot: a page term written on a bean that does not carry `view`, a binding on an
element the drawing does not have, an action on an element that is not a button, `processes` without `pipes`, a race
that draws a procedure which branches, a drawing that shows an address, a value no monitor of the page can compute, a
monitor whose technology no adapter here reads. It warns where a lens holds more than its row allows, and where a
monitor reaches a being it cannot probe.

## Tables, forms, documents and calendars

A drawing may give more than a picture, each declared on its `views` entry and judged by the gate:

- `writes`: an entry form per term, its `attrs` among the law's attributes of that term. The served page adds the entry
  to a bean through bin/dmsave.py, as the viewer's being; the gate judges it, and a refused save is undone and its
  message shown. The offline report shows no form.
- a `table`'s lines as CSV: beside the report (`report` writes `<stem>.<view>.csv`), and from the host (`/api/csv`).
- `renders`: a template of the garden (`file:<path>`, each `{{ path }}` a field path of the member) rendered per member
  of a reading (`selection`; absent, the being drawn) by `render`; `--keep` keeps each as a `document` bean named by its content_hash, saved through dmsave.
- `feed`: a reading whose members' `timing` (and clauses' `due`) are one calendar, with a `notice` before each; `ics`
  writes it for a viewer of the host, as the flow law's `served` pass, audited, and refused where a member's title and
  moment are not granted that viewer.
- an action with `every` (a recurrence) runs on its schedule as the being `answered_by` names, asked like a press.

## The served page, closed by default

`serve` reads the host's own configuration (`templates/serve.json` shows its shape) for who may sign in, and the
LEDGER for what each may see and do: each viewer is a being of the garden (`bean`), and one function answers every
question, `view_serve.Host.may(user, bean, act, positions, write)`, by asking bin/dmpass.py `may` of the grants the
ledger holds. The documentation the page sends, a table's lines, the values it reads, every action and every write
pass through it; where only a part of a bean is granted (`positions`), only that part is sent.

- The host's configuration is a ceiling under the law, never a key. A viewer's `orgs` name the organisations they may
  see, or `"*"` for every one, leaving the ledger alone to decide.
- A being's organisation is read from its record: the bean of genos `org` that owns it in law, or, for a being owned
  `via` another, that other's. A being no organisation can be derived for is under the ceiling of a viewer scoped to
  organisations only through `"shared": true` (every such being) or `"beans": [<id>, …]` (those by name).
- A viewer acts or writes only with `"actions": true`, where a grant opens it (`act:<tool>`, `write`), with a tool the
  host's `tools` names. A tool the host has not enabled runs as a dry run. Every attempt is written to the host's audit
  log, with the answer that decided it.
- `monitors` gives each monitor's address (`{"<being>": {"url": …}}`); `history`, where a history page exists, the
  base its links open.

The server reads the ledger again when its head moves, and starts itself again on a new head or a new release only
once `check` passes on it.
