// odoo19 — Odoo 19's own client served by daftard (P7.1), in Persian: taken by daftard's importers from a 19 Community
// instance with the owners' addons, it boots on Odoo's own origin, right to left, with the captured models as its apps
// named in the reader's language; each list opens with its own columns, its search box, its filters and its group-by
// (answered in 19's own shapes), a reload of one of its own addresses lands on the same action, and no page exception
// is raised. The garden holds none of the models' records (a register is read for them: P7.2): every list is empty.
//
//   ODOO_PASSWORD=… node test/render/odoo19.mjs --tree <daftar tree> [--odoo http://127.0.0.1:8369] [--db <db>]
//        [--login admin] [--model res.partner --model …] [--shots <dir>]
//
// Self-contained: it grows a garden of the core from the daftar tree, takes Odoo's client and the models' views from the
// instance with daftard's own importers (importers/odoo/client.py, views.py), builds daftard from this tree, serves the
// garden with it, and opens Odoo's page through daftard's door in headless Chromium.
import assert from 'node:assert/strict';
import { spawn, spawnSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import net from 'node:net';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { browser } from './cdp.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(HERE, '..', '..');
const opt = { odoo: 'http://127.0.0.1:8369', db: 'views19', login: 'admin', model: [] };
const argv = process.argv.slice(2);
for (let i = 0; i < argv.length; i += 2) {
  const k = argv[i].replace(/^--/, '');
  if (k === 'model') opt.model.push(argv[i + 1]); else opt[k] = argv[i + 1];
}
if (!opt.model.length) opt.model = ['res.country', 'res.partner', 'res.partner.category'];   // Odoo's own models
if (!opt.tree || !process.env.ODOO_PASSWORD) {
  console.error('ODOO_PASSWORD=… node test/render/odoo19.mjs --tree <daftar tree> [--odoo <url>] [--db <db>]');
  process.exit(2);
}
const T = mkdtempSync(join(process.env.TMPDIR || tmpdir(), 'odoo19-'));
const step = (name) => console.log('·', name);
const py = process.env.PYTHON || 'python3';
function sh(cmd, args, o = {}) {
  const r = spawnSync(cmd, args, { encoding: 'utf8', ...o });
  if (r.status !== 0) throw new Error(`${cmd} ${args.join(' ')}: ${(r.stderr || '') + (r.stdout || '')}`.slice(-1500));
  return r.stdout;
}
const freePort = () => new Promise((ok) => { const s = net.createServer(); s.listen(0, '127.0.0.1', () => { const p = s.address().port; s.close(() => ok(p)); }); });

let daftard, b;
try {
  step('a garden of the core, grown from the daftar tree');
  const garden = join(T, 'garden');
  sh(py, ['-c', `import sys; sys.path.insert(0, ${JSON.stringify(join(opt.tree, 'test'))}); import grow
rel = grow.release(${JSON.stringify(join(T, 'release'))}); grow.garden(rel, ${JSON.stringify(garden)}, 'sam', '--gardener-name', 'Sam')`]);
  step("Odoo 19's client and the models' views, taken from the Community instance by daftard's importers");
  const state = join(T, 'state');
  const odooArgs = ['--url', opt.odoo, '--db', opt.db, '--login', opt.login];
  sh(py, [join(REPO, 'importers/odoo/client.py'), ...odooArgs, '--out', join(state, 'odoo', '19.0'), '--lang', 'fa_IR']);
  sh(py, [join(REPO, 'importers/odoo/views.py'), ...odooArgs, '--out', join(garden, 'captures', 'views', 'odoo-19.0'),
    '--lang', 'fa_IR', ...opt.model.flatMap((m) => ['--model', m])]);
  step('daftard, built from this tree, serving it in Persian');
  const bin = join(T, 'daftard');
  sh('go', ['build', '-o', bin, './cmd/daftard'], { cwd: REPO });
  const port = await freePort(), odooPort = await freePort();
  writeFileSync(join(state, 'daftard.json'), JSON.stringify({ listen: `127.0.0.1:${port}`, odoo_listen: `127.0.0.1:${odooPort}`,
    gardens: [{ name: 'g', path: garden, python: py, title: 'دفتر آزمون', kind: 'core', lang: 'fa', gardener: 'sam' }] }));
  daftard = spawn(bin, ['serve'], { env: { ...process.env, DAFTARD_NOTIFY: 'off', DAFTARD_STATE: state }, stdio: 'ignore' });
  const base = `http://127.0.0.1:${port}`;
  for (let i = 0; ; i++) {
    try { if ((await fetch(`${base}/health`)).ok) break; } catch { /* not yet */ }
    if (i > 300) throw new Error('daftard did not start');
    await new Promise((r) => setTimeout(r, 100));
  }
  const key = readFileSync(join(state, 'key'), 'utf8').trim();
  b = await browser({ base, key });
  const { evaluate, until, sleep } = b;
  const shot = async (name) => { if (opt.shots) { mkdirSync(opt.shots, { recursive: true }); await b.shot(join(opt.shots, name), false); } };
  const open = async (to) => {
    const door = await fetch(`${base}/door`, { method: 'POST', headers: { 'X-Daftard-Key': key } });
    const { once } = await door.json();
    await evaluate('window.__before = true');
    await b.navigate(`${base}/?once=${once}&to=${encodeURIComponent(to)}`);
    try {
      await until(`!window.__before && location.host === 'localhost:${odooPort}' && document.querySelector('.o_main_navbar')`, "Odoo's page");
    } catch (e) {
      throw new Error(e.message + ' — at ' + await evaluate(`location.href + ' : ' + (document.body?.innerText || '').slice(0, 300)`));
    }
  };
  // the apps are the captured models, in their order: their actions are numbered so
  const models = [...opt.model].sort();
  const titles = Object.fromEntries(models.map((m) => [m, readFileSync(join(garden, 'captures', 'views', 'odoo-19.0', m, 'list.fa_IR.xml'), 'utf8').match(/string="([^"]+)"/)[1]]));
  const action = async (m) => {
    const id = models.indexOf(m) + 1;
    await evaluate(`odoo.__WOWL_DEBUG__.root.env.services.action.doAction(${id}, {clearBreadcrumbs: true}).then(() => 1)`);
    await until(`(document.querySelector('.o_breadcrumb .active, .o_last_breadcrumb_item') || {}).textContent?.trim() === ${JSON.stringify(titles[m])} && document.querySelector('.o_list_renderer thead th[data-name], .o_kanban_renderer')`, `the list of ${m}`);
    await sleep(400);
  };

  await open('/odoo?g=g&series=19.0');
  step('the page: right to left, the captured models as its apps, named in Persian');
  assert.equal(await evaluate(`document.documentElement.dir || getComputedStyle(document.body).direction`), 'rtl');
  const apps = await evaluate(`odoo.__WOWL_DEBUG__.root.env.services.menu.getApps().map(a => a.name)`);
  assert.deepEqual(apps, models.map((m) => titles[m]), 'an app per captured model, named by its list view in Persian');
  for (const m of models) {
    step(`${m}: its list, its own columns in Persian, empty`);
    await action(m);
    // each column is a field of the captured view, named as the capture names it in Persian (the view's own `string`,
    // else the field's): what the client shows is the capture, not a word of daftard's
    const cap = join(garden, 'captures', 'views', 'odoo-19.0', m);
    const arch = readFileSync(join(cap, 'list.fa_IR.xml'), 'utf8'), described = JSON.parse(readFileSync(join(cap, 'fields.fa_IR.json'), 'utf8'));
    const named = Object.fromEntries([...arch.matchAll(/<field ([^>]*?)\/?>/g)].map(([, at]) => [at.match(/name="([^"]+)"/)[1],
      (at.match(/string="([^"]+)"/) || [])[1] || (described[at.match(/name="([^"]+)"/)[1]] || {}).string]));
    const heads = await evaluate(`[...document.querySelectorAll('.o_list_renderer thead th[data-name]')].map(th => [th.dataset.name, th.textContent.trim()])`);
    assert.ok(heads.length >= 2, `the list has its columns: ${JSON.stringify(heads)}`);
    for (const [name, text] of heads) if (text) assert.equal(text, named[name], `the column ${name} is named as the capture names it`);   // an avatar's column shows none
    assert.ok(heads.filter(([, t]) => /[\u0600-\u06FF]/.test(t)).length >= heads.length / 2, `in Persian: ${JSON.stringify(heads)}`);
    assert.equal(await evaluate(`document.querySelectorAll('.o_list_view .o_data_row:not(.o_sample_data_disabled)').length && !document.querySelector('.o_view_sample_data') ? 1 : 0`), 0, 'no record: the garden holds none');
    await shot(`odoo19-${m}.png`);
  }
  const demand = models.includes('res.partner') ? 'res.partner' : models[0];
  step(`${demand}: the search box, a filter's menu, a group-by — each answered in 19's shapes`);
  await action(demand);
  await evaluate(`(() => { const i = document.querySelector('.o_searchview_input'); i.focus(); i.value = 'کافه'; i.dispatchEvent(new InputEvent('input', {bubbles: true, data: 'کافه', inputType: 'insertText'})); })()`);
  await until(`!!document.querySelector('.o_searchview_autocomplete .o-dropdown-item, .o_searchview_autocomplete li')`, 'the search box offers its fields');
  await evaluate(`document.querySelector('.o_searchview_input').dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', bubbles: true}))`);
  await until(`!!document.querySelector('.o_searchview_facet')`, 'a facet');
  await evaluate(`document.querySelector('.o_searchview_dropdown_toggler')?.click()`);
  await until(`!!document.querySelector('.o_group_by_menu, .o_searchview_dropdown .o_dropdown_container')`, "the filters' menu");
  // group by a field through "Add Custom Group", as a person picks one: 19's web_read_group
  await until(`!!document.querySelector('.o_group_by_menu')`, 'the group-by menu');
  const by = await evaluate(`(() => {
    const item = document.querySelector('.o_group_by_menu span.o-dropdown-item');   // a group-by the view offers
    if (item) { item.click(); return item.textContent.trim(); }
    const s = document.querySelector('.o_group_by_menu select.o_add_custom_group_menu');   // else one picked by its field
    const v = s && ['country_id', 'state', 'type'].find(x => [...s.options].some(o => o.value === x));
    if (v) { s.value = v; s.dispatchEvent(new Event('change', {bubbles: true})); }
    return v || '';
  })()`);
  assert.ok(by, 'a group-by to choose');
  await until(`[...document.querySelectorAll('.o_searchview_facet')].length >= 2 && !!document.querySelector('.o_list_renderer')`, 'the group-by facet');
  await sleep(800);
  assert.equal(await evaluate(`document.querySelector('.o_error_dialog, .o_dialog .modal-body .text-danger') ? 1 : 0`), 0, 'no error dialog');
  await shot('odoo19-search.png');
  step("a reload of one of the client's own addresses lands on the same action");
  const here = await evaluate('location.pathname');
  assert.match(here, /^\/odoo\/action-\d+/);
  await evaluate('window.__before = true; location.reload()');
  await until(`!window.__before && document.querySelector('.o_breadcrumb .active, .o_last_breadcrumb_item')`, 'the page again');
  assert.equal(await evaluate(`(document.querySelector('.o_breadcrumb .active, .o_last_breadcrumb_item') || {}).textContent.trim()`), titles[demand]);

  const errors = b.exceptions.filter((e) => !/serviceworker|service worker|bus|websocket/i.test(e));
  assert.deepEqual(errors, [], 'no page exception');
  console.log("PASS: odoo19 — Odoo 19's own client through daftard in Persian: its apps, each list's columns, the search box, " +
    "a filter's menu and a group-by in 19's shapes, a reload of its own address; no page exception");
} catch (e) {
  let where = '';
  if (b) {
    try {
      where = await b.evaluate(`location.href + ' :: ' + ((document.querySelector('.o_dialog, .modal, .o_error_dialog') || {}).innerText || '').slice(0, 1500)`);
      if (opt.shots) await b.shot(join(opt.shots, 'odoo19-fail.png'));
    } catch { /* the page is gone */ }
  }
  console.error('FAIL: odoo19 —', e.message, '\n  at:', where, b ? '\n  exceptions: ' + JSON.stringify(b.exceptions.slice(0, 5)) : '');
  process.exitCode = 1;
} finally {
  if (b) await b.close();
  if (daftard) daftard.kill();
  await new Promise((r) => setTimeout(r, 500));
  try { rmSync(T, { recursive: true, force: true, maxRetries: 10, retryDelay: 300 }); } catch (e) { console.error('odoo19: scratch left at', T, e.code); }
}
