# The toolbox: what every page is built from

The handplace's pages are made only of these modules (`web/toolbox/`, ES modules, no build step). They carry daftar's
design rules: values exact, every value isolated, HTML built only from safe templates (daftar `design/TEXT.md`), one
widget per value of the types tree (`design/TYPES.md`, `design/WIDGETS.md`). A page that needs something the toolbox
lacks adds it here, with tests, rather than building it inline.

## The one rule: HTML only from `h`

```js
import { h, mount } from '/toolbox/safe.js';
mount(el, h`<p>${person.name}</p>`);   // every ${} is escaped, unless it is itself Safe (a widget's output)
```

- `h` is a tagged template. It returns `Safe`; every interpolation is escaped (`& < > " '`) unless it is a `Safe`. An
  array of Safe values is joined. `null` and `undefined` print nothing.
- `mount(el, safe)` is the only way to put HTML into the page. `test/toolbox/lint.mjs` fails on any `innerHTML`,
  `outerHTML`, `insertAdjacentHTML` or `document.write` in `web/` outside `safe.js`.
- Text from data always goes through a widget or `${}`; never string concatenation into markup.

## Value widgets (one per value of the types tree)

Each exports `implements` (the value of `core/law/values.yaml`), `show(value, options) → Safe`,
`text(value, options) → string` (plain text: CSV, a notification, isolated with FSI/LRI … PDI), and, where a person
types the value in, `edit(name, value, options) → Safe` and `take(input, options) → {value} | {error}`.

| Module | Value | Shows |
|---|---|---|
| `number.js` | number, count, fraction | Persian digits, grouping, the fraction stacked or inline, never a float |
| `money.js` | money | `number` at the currency's places, plus its label outside the number's isolate; an uneven amount flagged |
| `moment.js` | day, time-of-day | in the reader's calendar (Persian or Gregorian), written as the law writes a position (`2026-10-01`) |
| `text.js` | text | isolated, its direction from its language or its first strong character; an inspect mode shows hidden controls |
| `name.js` | name (phone, email, id) | left to right, grouped as its namespace shows it |
| `choice.js` | choice, choices, code | a table row by its label; `edit` is a select, or a searchable list for long tables |
| `exact.js` | number (sums) | not shown: amounts as written (decimals or n/d) added exactly as BigInt fractions, and written back (`text(q, places)`), for running balances, totals and a voucher's two sides |
| `being.js` | being | a bean by its title; a link opens it |

## Parts pages are made of

| Module | What |
|---|---|
| `table.js` | `table({columns, rows, empty, key})`: each column `{title, cell: row => Safe, sort?, align?}`; sorting in the page, no reload |
| `form.js` | `form(fields, values)` renders, `collect(formEl, fields)` takes each field back through its widget's `take`, with errors per field; a choice field takes `none`, `placeholder` (asks even when required) and rows `{disabled}` (headings never taken) |
| `dialog.js` | `openDialog({title, body, actions})` on a `<dialog>`; closing returns focus |
| `guided.js` | `guidedError(err)`: the message, the reference (copyable), whom to follow up with, and a link to the detail the reader may see |
| `api.js` | `get(path)`, `save(body)` (CSRF, the form's head, a request id), `post(path, body)`, `events(onChanged)` (server-sent events: refresh only when the garden changed, never while hidden); the garden from a landing address or `?g=` |
| `settings.js` | who the page is for (`me`, `gardenerId`), the garden's title, language, calendar and currencies, from the payload |
| `labels.js` | `L(key, default)` / `Lt(key, default)`: every interface word; the reader's own labels in place of the default |
| `log.js` | `log`, `warn`, `timed`, `expose`: debug mode's console, silent otherwise |

## Labels: a person's own words for the interface

Every word a page shows that is not data (a menu entry, a heading, a button) is `L(key, default)`. A **label** is
one reader's customisation of such a word, made in admin mode. It is never the garden's:

- **A garden's names and data are its beans'.** They are shown by the value widgets and changed as data, with their
  journal entry. Nothing that names something in the garden (a bean's title, a law term, a currency) goes through
  `L`, so no label can rename it.
- **One person's labels are theirs alone, and the same on each machine they read on.** daftard keeps them in the
  garden's repository on `refs/daftar/custom/<person>`, outside its tree. That is not a bean, not in the journal, not
  judged by the gate, and not exchanged. daftard carries the ref through the hub it syncs with, after each sync step
  (`internal/custom`).
- **Merged word by word.** For the same word, the later change stands; a word set back is kept as an empty text.
- **Checked against the page.** Each label keeps the default it replaced (`was`). Admin mode marks one whose default
  has changed since, and "my labels" lists each label as current, to look at again, or no longer on any page.

Keys are `area.id` (`nav.clients`, `title.clients`, `garden.title`). A page offers the defaults of its keys before
they are shown (`offer`), so the list can say which ones changed.

## The page's switches

| Switch | What it does |
|---|---|
| `?debug=1` | logs every read and save (path, status, time), change event, render and action, with the error references, to the console; `window.daftar.ctx` is the page's state. Remembered in this browser until `?debug=0` |
| `?admin=1` | edit marks on every label, and "my labels" (this tab only) |
| `?static=1` | no change events: a screenshot or a test waits for the page to go quiet, and a live stream never does |

The one-time code's redirect (`/?once=…`, the code asked of `POST /door` by `daftard open` or a render test) carries
these three on, and nothing else. The cookie it sets carries a value the running daftard made when it started, never
the machine's key (a cookie reaches every port of 127.0.0.1), so a page left open while daftard starts again is opened
again from the desktop icon; a script or the command line sends the key in the `X-Daftard-Key` header instead.

## Landing addresses

`/go/<garden>[/<kind>[/<id>]]` (and `daftar://go/…`, through `daftard open`) opens the handplace on what a
notification or any platform's lead names. The kinds are `pending`, `proposal`, `sync`, `error` and `case`; the page
is `app/pages/lead.js`. The address only names the case: the page reads it from the garden, and the decision is made
on the page. The server accepts only addresses of that shape (`web.GoRe`), and the client's router reads the same
shape (`main.js` `GO`). `ctx.go(kind, id)` moves between them without reloading.

## Pages

`web/app/pages/<name>.js` exports `{id, nav, title, render(ctx) → Safe, actions?, input?, change?, headerActions?}`.
`ctx` holds the data (`ctx.data`, `ctx.books()`, `ctx.calendar()`), `ctx.reload()`, `ctx.save()`, `ctx.notice()`,
`ctx.open(page, params)` and `ctx.go(kind, id)`. Pages act through `data-action` attributes: the shell delegates
each click to the page's `actions`, then the shared ones. There are no inline handlers (the CSP forbids them) and no
globals.

## Tests

- `node test/toolbox/*.test.mjs`: each widget, exact, isolated, escaped.
- `node test/toolbox/lint.mjs`: no HTML built outside `h`.
- `python3 test/bidi-lab/lab.py test/bidi-lab/*.json`: visual order in Chromium, right to left and left to right.
- `go test ./...`: landing addresses and redirects, label text, the labels' merge across two machines and a hub.
- `node test/render/drive.mjs` (`DAFTAR_URL`, `DAFTAR_KEY`, `DAFTAR_GARDEN`): the handplace clicked through in headless
  Chromium against a SCRATCH copy of a garden. It covers the landing list, a decision through its dialog, a label in
  admin mode, "my labels" and debug mode's logs, and fails on any page exception.
