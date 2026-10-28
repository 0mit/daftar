# Odoo's own search tests against daftard (design §10.2, P5.5)

The design's acceptance: *"accepted when Odoo's own search tests (`web/static/tests/search/`) pass against daftard,
and fail against a daftard with one call removed."* This folder makes that claim checkable, and says where it is true
and where it is not.

    ODOO_PASSWORD=<the instance's> node test/odoo-search/run.mjs --tree <daftar tree> --all [--out report.json]
    node test/odoo-search/run.mjs --tree <tree> [--without <call>] [--filter "<QUnit filter>"]     # one run

Needs: an Odoo 17 Community instance on the loopback (the kit's throwaway one, `--odoo http://127.0.0.1:8269 --db
views17 --login admin`), Chromium, Go, Node 22+, Python 3, and a daftar tree whose law has `core/law/crosswalks.yaml`.

## What the tests are

Odoo 17's search tests are 250 QUnit tests in 11 files. They run in the browser, in Odoo's own test page, against
`MockServer`, an in-page imitation of Odoo's server fed with each test's `serverData`. Measured (hook.js logs every
call that reaches the mock): 216 tests make server calls and 34 make none (the search model, its utilities, the
group-by class); the calls are `get_views` (210 tests), the two `search_panel_*` calls (115), `fields_get` (22),
`web_search_read` (13), `name_search` (12), `read_group` (4), `web_read` (2), `read` (1), and, from the 12 tests that
mount Odoo's whole web client, its menus and actions (`/web/webclient/load_menus`, `/web/action/load`) and three
writes (`onchange`, `web_save`).

## What the harness does

- **Odoo's test files are Odoo's, fetched at run time**: the page and its bundles (`/web/tests`, the instance's own
  compiled `web.qunit_suite_tests`) come from the Community instance named. Nothing of Odoo (LGPL-3) is kept here.
  Every module of the suite loads, as in Odoo's own run; only the files of `web/static/tests/search/` register tests.
- **Each read call goes to a real daftard**, built from this tree, serving a scratch garden of the core grown from the
  daftar tree, opened through daftard's own door: the seat on its Odoo origin, its worker, its answerer
  (`python/odoo_rpc.py`). For each call, the runner first lays the test's own data where daftard reads a garden's:
  its views (the arch the mock would have chosen for each `[id, type]` asked) and fields as the garden's captures, its
  favourites on the reader's own ref, and its records as the **register** the worker reads them from
  (`register_worker.py`). What daftard answers is what the test gets; a refusal is the test's server error.
- **The register is the one stand-in, and it stands in for the crosswalks only.** Odoo's test models (`partner`,
  `foo`, `company`…) are no facts of any garden and the law crosses none of them; carrying them through invented
  statements would test the invention. So the worker's records come, for these tests, from the mock's own data, and
  everything else is daftard's. That the crosswalks read a garden's beans as Odoo's models, and that the reader's
  grants narrow every answer, is proved where it is real: `test/worker/records_test.py`, `odoo_grants_test.py`,
  `odoo_history_test.py`, and `test/render/odoo_hr.mjs` over the law's own tables.
- **The bridge is synchronous.** The tests were written against an in-page server: many click, then assert after one
  tick. A call carried over HTTP arrives later than a tick, so a test would fail for its transport, not its answer.
  The page asks the runner's bridge with a blocking request, which asks daftard while the page waits; the answer
  then resolves the client's promise in the same turn as the mock's own would. What is answered is daftard's; when,
  the mock's.
- **What daftard does not answer stays with the mock, and is named**: the web client's menus and actions (daftard's
  are the garden's captured models, not a test's actions) and the writes (daftard's Odoo client is read-only). The
  report lists, test by test, every call that went to daftard and every call that did not.
- **A daftard with one call removed** (`--without <call>`, and each in turn with `--all`) is built from a copy of this
  tree whose answerer never takes that call's branch, so the call is refused as one daftard does not answer.

## What it shows (2026-10-11, Odoo 17.0-20240429)

Whole: 250 tests, **247 pass, 2 fail, 1 skipped by Odoo itself**; every one of the 216 tests that make a server call
asked daftard, 484 calls in all, and 12 also asked the mock what daftard does not answer.

The two that fail are `SearchPanel` "many2one: select one, expand, hierarchize, counters" and "…no expand…". They
assert the MOCK's own error, not Odoo's: its `mockSearchPanelGlobalCounters` reads each value's count from an array by
the record's id (`localCounters[id]`, `web/static/tests/helpers/mock_server.js`), so a parent never gains its children's
counts. Odoo's server (`_search_panel_global_counters`, `addons/web/models/models.py`) reads them by id and adds them,
and Odoo's own server test of it (`odoo/addons/test_search_panel/tests/test_search_panel_select_range.py`, its first
case: "Folder 1" counts 2, its own record and its child's) asserts so; `test/worker/odoo_rpc_test.py` holds daftard to
that case. Here daftard answers as Odoo's server does, and these two tests fail. (That they would fail against Odoo's
own server too is read from its code and its own test, not measured: the tests' models exist only in the mock.)

With each call removed, every test that asks it fails:

| call removed | tests that ask it | of them failing | all failing |
|---|---|---|---|
| `get_views` | 210 | 210 | 210 |
| `search_panel_select_multi_range` | 58 | 58 | 60 |
| `search_panel_select_range` | 57 | 57 | 57 |
| `fields_get` | 22 | 22 | 24 |
| `web_search_read` | 13 | 13 | 15 |
| `name_search` | 12 | 12 | 14 |
| `read_group` | 4 | 4 | 6 |
| `web_read` | 2 | 2 | 4 |
| `read` | 1 | 1 | 3 |
| `web_read_group`, `search_count` | 0 | — | 2 |

("All failing" counts the two that assert the mock's error.) Before this harness's change, against daftard as it was
(origin/main 2026-10-11, its worker given only the kind of a garden of the core, so it could start): every one of the
216 tests that make a server call failed, its worker refusing every model the tests name (a model name without a dot);
with that name check alone relaxed, 69 failed (`fields_get`, `read`, `read_group` unanswered; the panel, groups and
reads answered otherwise than Odoo's server).
