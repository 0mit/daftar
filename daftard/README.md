# daftard

`daftard`, one per machine, serves the daftar gardens it holds (its design is cited by section, `§`, and is not part of
this repository), **one daemon per garden** (the operator, 2026-10-14): `daftard serve` is the machine's daftard, which
starts and keeps one `daftard serve --garden <name>` for each garden in daftard.json, each holding its garden in memory
on a loopback port of its own (`listen` per garden; else the machine's port + 11 + its place) and its garden's lock
(`<git dir>/daftard.lock`: a second daemon for one garden is refused). The machine's own address is the front door that
opens each garden's daemon by a one-time code of its own; the served handplace's listener and Odoo's origin stay the
machine's, asking each garden's daemon its questions (`/internal/call`, the machine's key). A garden's daemon ends when
the machine's is gone. **Answers held:** a question that reads is answered from the daemon's memory at the garden's
version (internal/web/held.go), in well under a millisecond; a change — committed, staged or edited — moves the
version, and what was asked lately is asked again in the background. This is the MVP:

- **The handplace:** the gardener's pages on 127.0.0.1, built from the widget toolbox (`web/widgets`: exact numbers and
  money, isolated text, Persian digits, the Vazirmatn font). Its navigation is seven pages, one a problem the garden
  solves (`web/app/pages/seven.js`): what needs me now, the people and their cases, time, money (who owes whom, drawn
  as flows), the books, the company report, and what passes between gardens — each made of the parts that solved it
  before, one part at a time; an old page's address opens the page that holds it. Arrows are chosen by meaning
  (`web/toolbox/direction.js`, the daftar release's view widget): in Persian `next` points left.
- **A garden's own pages (`handplace: "view"`):** a garden whose handplace is its page beans has those as its
  navigation, in the order the garden places them; each page is read, scoped to the person reading, drawn and written
  by the view's own code from the release the garden runs — the worker builds the page with the view's scoping
  (`view_serve.Host`'s own), the browser draws it with the release's runtime, renderers and widgets, loaded as files
  from the garden's `assets/view/lib` (`/release/<garden>/…`, its scripts, styles and font and nothing else of the
  garden), and a Save goes to the view's one write path, signed where a person sits. The chrome — the garden, its sync,
  who sits, the notices and «منتظر شما» — stays daftard's, in the garden's language and direction. The view's own page
  of a page bean is `/view?g=<garden>&page=<bean>`, running only the scripts its asset declares, by their hashes. Each
  person reading sets their own way of reading there — calendar, digits, hour cycle, first day of the week and zone as
  one BCP 47 tag, and how a day is written and a currency named — checked by the garden's own view and kept on this
  machine (`readers.json` in the state folder, by garden and person), never in the garden or a commit; `daftard prefs
  export <garden> <person> [--out FILE]` writes them as a bean (the view's `reader_preferences`, written by the garden's
  own release) to keep or carry, and `daftard prefs import FILE [<garden>]` reads one back, losing nothing. Every
  garden stays `legacy` (the pages above) until its gardener moves it, and keeps exactly that surface: a view garden's
  addresses (`/api/view/page`, `/api/view/write`, `/api/prefs`, `/release/<garden>/…`) answer a legacy garden 404, and
  its `/view` is the dashboard's own page, as before.
- **The board (`/board?g=<garden>`):** one being or several, the cursor, kept still while the aspect around it turns —
  the view profile's archetype `cursor`. The page is daftard's (`web/board/`), drawn with three.js beneath the beings'
  HTML; what it shows is read by the garden's own release (`assets/view/lib/view_board.py`) through the worker's
  `board_aspects`, `board_lens`, `board_being` and `board_find`: the law's aspects of the profiles the garden takes,
  over its beans and every store its host keeps. Its answers are never held, since a store changes without the garden's
  version moving; it only reads, and a bean's statements on a sheet are shown to its gardener, or to a reader the
  garden's own grants open the bean to. A garden that takes no view profile has no board.
- **Sync and exchange:** each garden kept in step with its hub, with its exchange rounds run where the gardener has
  consented. This takes over from the old dashboard's loop.
- **Guided errors:** every refusal or failure gets a reference, a message, and whom to follow it up with. The whole
  detail is kept off git for whoever's privileges cover it (`daftard error <ref>`).
- **Push, don't poll:** a page reads its garden again only when the garden's commit changed (`/api/events`), and not
  while hidden.
- **Nothing shows a window:** every child process is started hidden (`internal/proc`), and the Windows build is a GUI
  binary.
- **The person at the keyboard (design §6):** each writer's key, under their own passphrase, signs their saves; on a
  shared account a sitting is begun with that passphrase and reading is closed to the gardener's sitting
  (`internal/sitting`). Where a garden names no hub, the machine's own key signs what the machine did itself — a merge
  with no conflict — as the host bean named by a garden's `machine`.
- **A garden hub signs what daftard writes on its own:** each garden hub has its own key, made once when the hub is
  initialized — by the garden's own `bin/hub.py install` on its working copy (`daftard install --hub <bean>` runs it) —
  in this account's state folder under `hubs/<garden id>/`, never in the garden or any repository of it. A merge with no
  conflict, an exchange round under a standing consent and a routine's records are authored as the hub's bean
  (daftard.json `hub`) and signed with that key, whose fingerprint the gardener adds to that bean (`/api/keys/hub`
  shows it, and whether the garden names it yet); a hub takes them as far as that bean's grants go, like any writer's
  (`internal/hubkey`). daftard signs as the hub only while the garden's last commit names the key on that bean, since a
  hub judges a merge's writer at its first parent: before then it merges nothing on its own. What a person decides is
  never signed with it. A garden that names no hub keeps the machine's own key, where it names its `machine`.
- **Every machine a peer (§7):** a garden of the core is kept in step by its own `bin/sync.py` (fetch, judge by the
  hub's rules, merge what passes); a merge is the hub's or a person's, never nobody's.
- **Leads (§8):** what waits, and for whom, read from the garden each time — decisions, cases, obligations, failures
  a reading shows, open sessions, forms' answers, passkeys to name — as notices on the machine, and off it only through
  a channel the garden's flow law grants. A decision is a need not met on the bean it concerns (core 3.7), read by the
  garden's own bin/waiting.py, its landing `/go/<garden>/pending/<bean>.<need>`, where the gardener meets it (`meet`,
  known by their `say`, read back by the one judge before it is saved); and an entry of log/pending.md still proposed
  (every decision, in a garden of a core before 3.7). A notice lives as long as the daftard that raised it, and a daftard started
  with `DAFTARD_NOTIFY=off` (every test's) raises none: each is a line of its log.
- **Ratified actions (§9):** an action's plan shown on its lead, ratified or declined there, in the person's sitting
  (the garden's `bin/act.py`).
- **A machine's routines (§14; CONTRACT §3, §5, §8):** where a garden's settings say `routines: true`, each minute the
  garden's own `bin/routines.py tick` runs what falls due on this machine — only a walk the garden grants this machine
  `enact` of, each run a course on the walk, waiting on its interlocks, never forced — with the machine's signing; each
  tool the garden places here is probed on its catalogue's cadence (`probe_seconds`, 30, at the fastest), its latest
  readings served at `/api/probe` and a 14-day series kept in the state folder; after each round the garden's
  `bin/routines.py cross` writes what crossed (a health lead). One log line per routine acted on (`internal/routines`).
- **The served handplace (§10.1):** beyond this machine, over TLS, for the people a garden's grants name: signed in by
  a link sent through a granted mail channel or by a passkey their own bean names (`internal/served`,
  `internal/passkey`); each read asked of the garden's `may`. A passkey whose signature counter does not grow is a
  copy of its authenticator, and signs nobody in; each one's last counter is the machine's, kept in the state folder
  (`passkey-counts.json`), never in the garden. **Served forms (§10.5):** a person without a garden
  answers a form opened to them; their words wait outside the garden until the gardener's save takes them.
- **A register read live (§10.2, §15.6):** a garden may keep no copy of some records at all — people who keep no
  garden, in an organisation's own Odoo — and daftard serves its client all the same: where daftard.json names a
  `register` for a garden (`series` from 19, `url`, `db`, and `bean`, the garden's bean of the register), the client's
  data calls are asked of the register itself on each call, by Odoo's JSON-2, as a read-only account whose API key is
  in the state folder (`registers/<garden>.key`, 0600; never in git, a page, a log or a command line); plain HTTP only
  on this machine's loopback. Who may read the register is who may read its bean, by the garden's own `may`; every
  domain is ANDed with the reader's grants; every field a call names is held to what the garden captured; a write, or
  any call not a read, never reaches the register; the register's own words in a refusal are never repeated; nothing it
  answers is kept. Where the register ranks a model the way people type (its captured fields carry `suggest_index`), a
  many2one's suggestions are the register's own ranking (`python/register.py`). **By more than one route**, for a
  register whose host sits behind an unstable link (`internal/register`): `routes` in the order to try them, in place
  of `url` (which stays one route) — `{"via": "https", "url": …}`, TLS verified, or `{"via": "ssh", "host": …, "port":
  22, "user": …, "to": "127.0.0.1:8069"}`, a forward daftard runs itself with the system's ssh: no configuration file
  but its own options, only the route's key (`registers/<garden>.ssh`, 0600) and only its host's key pinned
  (`registers/<garden>.known_hosts`, refused at load where it pins none), a loopback port it picks, keepalives, started
  again with backoff when it ends, ended with daftard. Each route's health is the register's `/web/health`, asked with
  no key every 20 s and at once after a failure; a route is healthy until it misses twice. A read goes by the first
  healthy route, and one that fails at the connection (never an HTTP answer) is asked once more of the next — only
  reads ever reach a register; a page waits 30 s at most, and is told at once when no route is healthy. `/health`
  shows each route (healthy or not, since when, its last error's kind, which answered last), `daftard status` where
  each goes, and daftard.log each transition — never a key, never a record. No proxy the environment names is used,
  and no redirect followed.
- **Odoo's own client (§10.2):** a series' Community web client, taken by `importers/odoo/client.py`, served at
  `/odoo?g=<garden>` with the views the garden captured (`importers/odoo/views.py`) and every call it makes answered
  by the garden's worker (`python/odoo_rpc.py`: Odoo's domain language, search, groups summed exactly, the search
  panel), in the garden's language; read-only while daftard answers no write. Its records are the garden's, read by the law's
  crosswalks (`core/law/crosswalks.yaml`, through the garden's own `core/crosswalk.py`). **Every answer is made of what
  the reader may read** (§10.2): each call is answered over one reading of the beans the reader's grants open now (the
  garden's own `may`), so no record, count, sum, group, search-panel counter or name in a many2one is made of anything
  else; their favourites are their own, kept beside their labels. **History** (§10.3): the page can be opened, or moved,
  as of a day, a moment or a commit (`/odoo?g=…&asof=…`, and a systray item on the page), every call then answered from
  the garden's beans at that commit, by today's grants; a form's chatter is its bean's history, each change with its
  journal entry and each statement with the act that knows it. The client runs on an origin of its own, `localhost:<odoo_listen port>`, never the handplace's: the
  handplace's `/odoo` is only its door, sending the page there by a one-time token that becomes a short session for
  one garden, series and reader, so a captured view can never act with the machine's key. **Series 19** (`/odoo?g=…&series=
  19.0`): the same, with what 19 asks differently — its routes under `/odoo/<path>`, its menus and translations with no
  path segment, the bundles it loads by name when a page needs one (taken with the client), its session's view names
  and mail store, its data calls by named arguments and its redesigned groups (held to a 19 instance's own answers,
  `test/odoo19/`); and never `browser_cache_secret`, so 19's client keeps nothing it was shown on the reader's disk.

- **Places (§12):** what a person types into a place is answered while they type (`/api/places`): the garden's own
  places first — each being whose `be … as: location` or `as: place` holds a coordinate in EPSG:4326 or an
  OpenStreetMap element — then the place bundles this machine holds (`internal/places`: place_responder's index, ranked
  exactly as the Python it translates; each bundle checked against its manifest), offline. Beyond the machine
  (`/api/places/far`, a self-hosted Photon) a lookup goes only to a party the garden's flow law grants (`sent-out`),
  carrying what was typed and nothing of the garden — and never for a place that says where a person will be: a page's
  sealed field, a happening, a being that holds an `attend` or a place held off git. The reader's own position goes
  only when they ask. No query and no position is logged or kept.

In the MVP, `daftard` reads and writes a garden through that garden's own Python model and tools
(`python/garden_worker.py`), so the garden's model and gate decide everything about its facts. The Go index that reads
gardens natively comes later.

## Build

daftard is the Go module `github.com/0mit/daftar/daftard`, in this folder of daftar's repository: it is built, and
released, at the same commit as the law and the tools its worker runs. From this folder:

    go build ./cmd/daftard                                              # this machine
    GOOS=windows GOARCH=amd64 go build -ldflags "-H=windowsgui" ./cmd/daftard   # Windows, no console

Go's standard library, and one package beside it: `golang.org/x/text/unicode/norm` (with `x/text/transform`, which it
imports), v0.42.0, vendored in `vendor/` and pinned by `go.mod`, `go.sum` and `vendor/modules.txt`. Place search folds
what a person types by Unicode's NFKC and NFKD, which the standard library does not have (`internal/places`; design
§12, decided 2026-10-11). It is the one exception in Go. The board's page carries three.js 0.186.1 (MIT), its
`build/three.module.js` and `build/three.core.js` unchanged in `web/vendor/three-0.186.1/` with its licence and where it
came from (`SOURCE.txt`), built into the binary beside the pages. Nothing else is taken from outside, and nothing is
fetched to build.

## Use

    daftard install --garden <path> --python <python> --title "<title>" --name <n> [--sync] [--exchange] [--routines] \
                    [--steward "who:title:reach"] [--no-service]   # daftard.json, and what keeps daftard running
    daftard serve | open | status | stop | error <E-XXXX-XXXX> | version | help

A garden's own `python3 bin/install.py --daftard` runs this for it (INSTALL.md): it lays the binary in the state folder
(`bin/daftard`), built from this folder where Go is and taken from the release's assets where it is not, and then asks
`daftard install` for the garden it is run in, with `--routines`. An install again keeps what `daftard.json` holds —
the machine's settings, the other gardens, and of this garden all that no flag names — and refuses a file that does not
read rather than write over it. What keeps daftard running, unless `--no-service`: on Windows the logon task «Daftar»,
the desktop icon «دفتر» and `daftar:` links; on Linux the systemd user unit `daftard.service` (`systemctl --user`;
`loginctl enable-linger` to run it with nobody logged in) and `daftar:` links where there is a desktop; on macOS the
launchd agent `daftar.daftard` in `~/Library/LaunchAgents`, started at login and again whenever it ends other than by
`daftard stop`. Each carries the PATH and `DAFTARD_STATE` it was installed with. With `routines: true`, daftard asks
the garden's `bin/routines.py tick` each minute; so on macOS, where a routine was a launchd job of its own, daftard is
now the one job launchd keeps, and the clock of every routine. A routine another scheduler still runs is that
scheduler's (`be … as: presence` on its walk), and the tick leaves it alone: its job is retired once daftard ticks it,
and never runs beside it.

A release's binaries are built by CI from the tagged commit (`.github/workflows/release.yml`) and attached to the tag's
GitHub release: `daftard-linux-amd64`, `daftard-linux-arm64`, `daftard-darwin-arm64`, `daftard-darwin-amd64` and
`daftard-windows-amd64.exe`, each with its SHA-256 beside it (`<binary>.sha256`), and `daftard-NOTICE.txt`, the notices
and licences of what a binary carries.

In `daftard.json`, beside each garden's `path`, `python`, `title` and `lang` (and `kind`: `dashboard`, the default, for
a garden that carries its own handplace; `board`, served by another tree's board; `core`, a garden of the core alone,
served Odoo's client, the served pages and forms, and kept in step by its own sync), `handplace` (`legacy`, the default:
daftard's own pages; `view`: the garden's page beans, drawn by the view of the release it runs): `writers` and `signed` (who sits here,
and whether every write is a person's signed commit), `machine` (the host bean this machine merges as), `channels`
(mail channels for leads and sign-in links, sent only where the flow law grants their party), `served` (offer the
garden on the served handplace), `routines` and `probe_seconds` (this machine's routines of the garden, and how often its
tools may be probed at the fastest); and at the top, `shared` (one account, several people) and `served: { listen,
names, cert, key }` (the TLS listener, bound before anything is served: if it cannot be, daftard does not start), and
`odoo_listen` (Odoo's origin, 127.0.0.1:8792 by default), and `places: { bundles: [<dir>, …] }` (this machine's place
bundles, place-bundle/1, later ones overlaying earlier ones by code). Beside a garden, `place_service: { url, party }`
names a place search beyond the machine (a Photon's address, where it answers `/api`) and the party a lookup sent there
is a `send` to, as the garden's own `sent-out` row grants it; or `place_service: { routes, party }`, reached as a
register is: its routes kept by `internal/register`, each route's health Photon's `/status`, a lookup by the first
healthy route and, failing at the connection, once more by the next (two attempts at most, through no proxy the
environment names); an ssh route to a Photon on a host's loopback — `{"via": "ssh", "host": …, "user": …, "to":
"127.0.0.1:2322"}` — goes with the garden's one ssh key and pinned host keys (`registers/<garden>.ssh`,
`.known_hosts`), the same its register's routes take, so one restricted account on that host may forward to both
(`permitopen` for each port). Plain HTTP only on this machine's loopback; a path is allowed (a Photon behind a proxy's
path). A lookup that says where a person will be is sealed before any route is asked. `listen` and `odoo_listen` must be on the loopback.
`daftard open` asks the running daftard for a one-time code with the machine's key in a header, and opens the page by
the code, so no command line or browser history holds the key. It opens a garden's front page by its name, a landing
(`daftar://go/<garden>/<kind>/<id>`, or `/go/…`), or a garden's Odoo screens (`daftar://odoo?g=<garden>&series=<series>`,
or `/odoo?g=<garden>&series=<series>`), each held to the one form the handplace takes and never passed on otherwise.
Odoo clients live in `<state>/odoo/<series>/`, taken there by `python3 importers/odoo/client.py … --out
<state>/odoo/<series> [--lang …]`.

State (settings, key, log, guided errors) lives in `%LOCALAPPDATA%\Daftar` or `~/.local/state/daftar`, never in git.

## Test

From the repository's root, `python3 test/daftard.py` runs what CI runs on Linux, macOS and Windows: `go build`,
`go vet` and `go test` of every package, the Go reader held to the same commit's `core/read.py` over a garden grown from
it, and the worker's and the importers' tests given that tree. The rest below needs an Odoo instance, a place bundle,
Node or a browser. From this folder, with `<daftar tree>` the repository's root (`..`):

    go test ./...                                 # sittings, keys, passkeys, sessions, the server and its pages
    DAFTARD_PLACE_BUNDLE=<a place bundle> go test ./internal/places/   # the place search ranked exactly as the Python
                                                  # it translates, over every place of the Iran bundle the reference was
                                                  # written from (place_ir's data/); without one, those tests say so and skip
    for f in test/worker/*_test.py test/importers/*_test.py; do python3 $f <daftar tree>; done   # forms, passkeys,
                                                  # records, odoo_grants, odoo_history and view_pages grow a garden
                                                  # from a daftar tree (the crosswalks, the view's pages), their argument
    ODOO_PASSWORD=… python3 test/odoo19/register.py --url … --db … --login admin --tree <daftar tree>   # a real 19
                                                  # instance read live as a garden's register, through daftard; nothing kept
    ODOO_PASSWORD=… node test/odoo-search/run.mjs --tree <daftar tree> --all   # Odoo's own search tests against daftard,
                                                  # and against it with each call removed (test/odoo-search/README.md)
    ODOO_PASSWORD=… node test/render/odoo_hr.mjs --tree <daftar tree>   # Odoo's own HR lists and forms, a garden of
                                                  # invented people through the law's hr.employee and hr.leave tables
    ODOO_PASSWORD=… python3 test/odoo19/conformance.py --url … --db … --login admin   # the answers to Odoo 19's
                                                  # client, held to a 19 instance's own for the same records
                                                  # (test/odoo19/README.md)
    ODOO_PASSWORD=… node test/render/odoo19.mjs --tree <daftar tree> --db …   # Odoo 19's own client through daftard
    node test/render/odoo_door.mjs --tree <daftar tree>   # the way into Odoo's origin, in headless Firefox (WebDriver
                                                  # BiDi, test/render/bidi.mjs) and Chromium: its Strict seat arrives
    node test/render/view_pages.mjs --tree <daftar tree>   # a garden's page beans as its pages, in Persian and English:
                                                  # drawn by the release, a Save through the view's write path
    node web/widgets/test_widgets.js              # the number and money widgets
    python3 test/bidi-lab/lab.py test/bidi-lab/widgets.json   # visual order in Chromium, right-to-left and left-to-right

## Licence

daftard is daftar's code, on daftar's terms: the GNU AGPL 3.0 or later with the garden exception (`REUSE.toml` gives
every path; `LICENSES/`). The Vazirmatn font is under the SIL Open Font License 1.1 (`web/widgets/Vazirmatn-OFL.txt`).
`vendor/golang.org/x/text` is The Go Authors', under the BSD 3-Clause licence, its `LICENSE` and its `PATENTS` grant
kept beside it. `internal/places` is place_responder's index, ported at that project's commit c7cb0fd
(`internal/places/doc.go` says what changed); the place names in its test keys are OpenStreetMap's, © OpenStreetMap
contributors, ODbL 1.0.

## Before pushing: nothing of a garden leaves

A repository of tools carries the language, never a garden. daftard is pushed as daftar is: the pre-push hook
`bin/install.sh` installs runs `bin/public.py` over the files and the commit messages being pushed, its forbidden words
derived from the gardens `git config daftar.garden` names (CONTRIBUTING.md, "This repository carries the language,
never a garden"). Who a page is for (its title, how the gardener is called) is each garden's setting in
`daftard.json` (`title`, `me`), never the code's.
