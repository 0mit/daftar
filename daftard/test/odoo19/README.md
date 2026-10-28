# Odoo 19's client through daftard

daftard serves a series' own web client (design §10.2): the views and the client are taken from that series' own
Community instance by `importers/odoo/views.py` and `client.py`, and every call the client makes is answered by daftard.
Series 19 asks for a few things differently from 17, and its grouping was redesigned; this folder holds what proves the
19 answers against a real 19 instance. The suites that need no instance are `test/importers/odoo_views_test.py`,
`odoo_client_test.py`, `test/worker/odoo19_test.py` and `internal/web` `TestOdooClient19`.

    ODOO_PASSWORD=<the instance's> python3 test/odoo19/invented.py   --url http://127.0.0.1:<port> --db <db> --login admin
    ODOO_PASSWORD=<the instance's> python3 test/odoo19/conformance.py --url http://127.0.0.1:<port> --db <db> --login admin
    ODOO_PASSWORD=<the instance's> node test/render/odoo19.mjs --tree <daftar tree> --odoo http://127.0.0.1:<port> --db <db>

Needs: a throwaway Odoo 19 Community instance on the loopback (no Enterprise path, no production data), Python 3, and
for the render test Chromium, Go, Node 22+ and a daftar tree. `rtlcss` on the instance's PATH, or Odoo builds no
right-to-left sheet for a language written so.

## What each proves

- **`invented.py`** makes the records the others read: invented people and companies (`res.partner`: a country, a kind
  of address, tags, a parent company), three tags, and a currency's rates on days across a year (`res.currency.rate`).
  Odoo's own models, so any 19 Community instance has them; nobody real.
- **`conformance.py`**: daftard's answerer (`python/odoo_rpc.py`, series 19) is handed the instance's own records and
  must answer each call exactly as the instance answers it for the same records — a list's page and count, a domain
  through a relation, a form's read, the many2one's suggestions (`name_search`, `web_name_search`), and the groups 19
  redesigned (`web_read_group`, `formatted_read_group`): by a many2one, a many2many, a selection and a date at each
  granularity, summed and averaged, a group opened into its subgroups or its records, a limited level and its length,
  an order by count. Compared whole, JSON for JSON. It is asked in English: the answerer words a date's group in English
  only (19 words it in the reader's language through its locale tables); the only setting it makes on the instance is
  English made active.
- **`test/render/odoo19.mjs`**: the client itself, taken by daftard's importers and served by a daftard built from this
  tree over a scratch garden of the core, in headless Chromium, in Persian: it boots right to left on Odoo's own origin,
  the captured models are its apps named in Persian, each list opens with its columns named as the capture names them,
  the search box offers its fields and makes a facet, a group-by is answered, and a reload of one of the client's own
  addresses (`/odoo/action-<id>`) lands on the same action. The garden holds no record of those models, so every list is
  empty.

## What 19 asks differently, and what daftard does

- The page's own routes live under `/odoo/<path>`: daftard serves the page there too, but never at its own
  (`/odoo/session.js`, `/odoo/daftar.js`, `/odoo/asof`, `/odoo/enter`).
- Its menus and translations are asked with no path segment (`/web/webclient/load_menus`, `/web/webclient/translations
  ?lang=`); bundles a page needs are loaded by name (`/web/bundle/<name>`): the importer takes their definitions and
  files, and daftard serves exactly those.
- Its session carries what each kind of view is called, in the reader's language (`view_info`, taken per language), and
  starts mail as a Store (`/mail/data`). It never carries `browser_cache_secret`: given one, 19's client keeps the records
  it was shown and the search panel's values in the browser's own disk cache (IndexedDB); without it, in memory only.
- The data calls name their arguments; `web_read_group` takes aggregates and opens groups as the client asks; a week
  starts on its language's first day (`week_start`, from the language's translations).

## Not proved here

A date group's words in another language than English; a record's history in 19's chatter (its Store shape: the 17
chatter's is built); `fill_temporal` and a group by a number of a date (`date:year_number`), which daftard refuses as
not answered yet.
