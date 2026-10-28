// odoo_hr — Odoo 17's own hr.employee and hr.leave lists and forms, served by daftard over a garden of invented people
// (design §10.2, P5.4): the law's crosswalks of those models read the garden's beans, the reader's grants narrow them,
// a form's chatter is its bean's history, and the page read as of the garden's first save shows that save's garden.
//
//   ODOO_PASSWORD=… node test/render/odoo_hr.mjs --tree <daftar tree whose law crosses hr.employee and hr.leave>
//        [--odoo http://127.0.0.1:8269] [--db views17] [--login admin]
//
// Self-contained: it takes Odoo's client and the HR views from the Community instance named, with daftard's own
// importers (importers/odoo/client.py, views.py), grows the garden (odoo_hr_garden.py), builds daftard from this tree,
// serves the garden with it, and opens Odoo's page through daftard's door in headless Chromium. Fails on any page
// exception.
import assert from 'node:assert/strict';
import { spawn, spawnSync } from 'node:child_process';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import net from 'node:net';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { browser } from './cdp.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(HERE, '..', '..');
const opt = { odoo: 'http://127.0.0.1:8269', db: 'views17', login: 'admin' };
const argv = process.argv.slice(2);
for (let i = 0; i < argv.length; i += 2) opt[argv[i].replace(/^--/, '')] = argv[i + 1];
if (!opt.tree || !process.env.ODOO_PASSWORD) {
  console.error('ODOO_PASSWORD=… node test/render/odoo_hr.mjs --tree <daftar tree>');
  process.exit(2);
}
const T = mkdtempSync(join(process.env.TMPDIR || tmpdir(), 'odoo-hr-'));
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
  step('the garden of invented people, from the daftar tree');
  const { garden, first } = JSON.parse(sh(py, [join(HERE, 'odoo_hr_garden.py'), opt.tree, join(T, 'g')]).trim().split('\n').pop());
  step("Odoo's client and the HR views, taken from the Community instance by daftard's importers");
  const state = join(T, 'state');
  const odooArgs = ['--url', opt.odoo, '--db', opt.db, '--login', opt.login];
  sh(py, [join(REPO, 'importers/odoo/client.py'), ...odooArgs, '--out', join(state, 'odoo', '17.0')]);
  sh(py, [join(REPO, 'importers/odoo/views.py'), ...odooArgs, '--out', join(garden, 'captures', 'views', 'odoo-17.0'),
    '--model', 'hr.employee', '--model', 'hr.leave', '--model', 'hr.department', '--model', 'res.company']);
  step('daftard, built from this tree, serving it');
  const bin = join(T, 'daftard');
  sh('go', ['build', '-o', bin, './cmd/daftard'], { cwd: REPO });
  const port = await freePort(), odooPort = await freePort();
  writeFileSync(join(state, 'daftard.json'), JSON.stringify({ listen: `127.0.0.1:${port}`, odoo_listen: `127.0.0.1:${odooPort}`,
    gardens: [{ name: 'g', path: garden, python: py, title: 'Acme Tiles', kind: 'core', lang: 'en', gardener: 'sam' }] }));
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
  // the page through daftard's own door: a one-time code for the handplace, which sends it on to Odoo's origin
  const open = async (to) => {
    const door = await fetch(`${base}/door`, { method: 'POST', headers: { 'X-Daftard-Key': key } });
    const { once } = await door.json();
    await evaluate('window.__before = true');           // the page now showing, so the wait is for the next one
    await b.navigate(`${base}/?once=${once}&to=${encodeURIComponent(to)}`);
    try {
      await until(`!window.__before && location.host === 'localhost:${odooPort}' && document.querySelector('.o_main_navbar')`, "Odoo's page");
    } catch (e) {
      throw new Error(e.message + ' — at ' + await evaluate(`location.href + ' : ' + (document.body?.innerText || '').slice(0, 300)`));
    }
  };
  const rows = (cell) => evaluate(`[...document.querySelectorAll('.o_list_view .o_data_row')].map(r => r.querySelector(${JSON.stringify(cell)})?.textContent.trim())`);
  const action = async (id, title, what) => {         // the action's list, once its own title is the breadcrumb's
    await evaluate(`location.hash = 'action=${id}&view_type=list'`);
    await until(`(document.querySelector('.o_breadcrumb .active, .o_last_breadcrumb_item') || {}).textContent?.trim() === ${JSON.stringify(title)} && document.querySelector('.o_list_view') && !document.querySelector('.o_view_sample_data') && document.querySelectorAll('.o_list_view .o_data_row').length`, what);
    await sleep(300);
  };
  const field = (name) => evaluate(`(() => { const e = document.querySelector('.o_form_view [name=${JSON.stringify(name)}]'); if (!e) return null; const i = e.querySelector('input, textarea'); return (i ? i.value : e.textContent).trim(); })()`);
  // the client's apps are the garden's captured models, in order: hr.department, hr.employee, hr.leave, res.company
  const [EMPLOYEES, LEAVES] = [2, 3];

  await open('/odoo?g=g');
  step('hr.employee: the list, each employment a row');
  await action(EMPLOYEES, 'Employees', 'the employees');
  assert.deepEqual((await rows('[name=name]')).sort(), ['Lale Demir', 'Mo Karimi']);
  assert.deepEqual((await rows('[name=work_email]')).sort(), ['lale@acme.example', 'mo@acme.example']);
  assert.deepEqual((await rows('[name=department_id]')).sort(), ['Office', 'Workshop']);
  step("hr.employee: Lale's form, her job, department and company, her private tab held off git, her history");
  await evaluate(`[...document.querySelectorAll('.o_data_row')].find(r => r.textContent.includes('Lale Demir')).querySelector('td[name=name]').click()`);
  await until(`document.querySelector('.o_form_view [name=name]')`, "Lale's form");
  assert.equal(await field('name'), 'Lale Demir');
  assert.equal(await field('job_title'), 'Tiler');
  assert.equal(await field('work_email'), 'lale@acme.example');
  assert.match(await field('department_id'), /Workshop/);
  await evaluate(`[...document.querySelectorAll('.o_notebook .nav-link')].find(a => /Private/.test(a.textContent))?.click()`);
  await until(`document.querySelector('.o_form_view [name=identification_id]')`, 'the private tab');
  assert.equal(await field('identification_id'), '10000000146', 'the identity number, resolved from this host\'s store for the gardener');
  assert.equal(await field('private_email'), 'lale@home.example');
  await until(`document.querySelectorAll('.o-mail-Chatter .o-mail-Message').length >= 1`, "the chatter's history");
  assert.match(await evaluate(`document.querySelector('.o-mail-Chatter').textContent`), /Lale and Mo employed|employed/);

  step('hr.leave: the list, each absence under its employment, where its walk stands');
  await action(LEAVES, 'Time Off Requests', 'the leaves');
  assert.deepEqual((await rows('[name=name]')).sort(), ['Summer leave', 'Three days off']);
  const states = await evaluate(`Object.fromEntries([...document.querySelectorAll('.o_data_row')].map(r => [r.querySelector('[name=name]').textContent.trim(), r.querySelector('[name=state]').textContent.trim()]))`);
  assert.deepEqual(states, { 'Summer leave': 'Approved', 'Three days off': 'To Approve' });
  assert.match(await evaluate(`[...document.querySelectorAll('.o_data_row')].find(r => r.textContent.includes('Summer')).textContent`), /Lale Demir/);
  step("hr.leave: Lale's summer, its days and its employee");
  await evaluate(`[...document.querySelectorAll('.o_data_row')].find(r => r.textContent.includes('Summer')).querySelector('td[name=name]').click()`);
  await until(`document.querySelector('.o_form_view [name=request_date_from]')`, 'the leave form');
  // the form shows the days as one range on request_date_from, its end the range's second input
  const range = await evaluate(`[...document.querySelectorAll('.o_form_view [name=request_date_from]')].map(e => [e.textContent, ...[...e.querySelectorAll('input')].map(i => i.value)].join(' ')).join(' ')`);
  assert.match(range, /(07\/06\/2026|2026-07-06).*(07\/17\/2026|2026-07-17)/, range);
  assert.match(await field('number_of_days_display'), /^12(\.0+)?$/);
  assert.match(await evaluate(`document.querySelector('.o_form_view').textContent`), /Lale Demir/);
  if (process.env.ODOO_HR_DEBUG) console.log('  notifications:', await evaluate(`[...document.querySelectorAll('.o_notification')].map(n => n.innerText).join(' | ')`));

  step('as of the first save: the employees, and no leave yet');
  await open(`/odoo?g=g&asof=${first}`);
  assert.match(await evaluate(`document.querySelector('.o_daftar_asof')?.textContent || ''`), new RegExp(first.slice(0, 7)),
    'the page says the commit it reads as of');
  await action(EMPLOYEES, 'Employees', 'the employees as of the first save');
  assert.deepEqual((await rows('[name=name]')).sort(), ['Lale Demir', 'Mo Karimi']);
  await evaluate(`location.hash = 'action=${LEAVES}&view_type=list'`);
  await until(`(document.querySelector('.o_breadcrumb .active, .o_last_breadcrumb_item') || {}).textContent?.trim() === 'Time Off Requests' && document.querySelector('.o_list_view') && (document.querySelector('.o_view_nocontent') || document.querySelector('.o_view_sample_data'))`, 'no leave as of then');
  assert.equal(await evaluate(`document.querySelectorAll('.o_list_view .o_data_row:not(.o_sample_data_disabled)').length && !document.querySelector('.o_view_sample_data') ? 1 : 0`), 0);

  const errors = b.exceptions.filter((e) => !/serviceworker|service worker|bus|websocket/i.test(e));
  assert.deepEqual(errors, [], 'no page exception');
  console.log('PASS: odoo_hr — hr.employee and hr.leave, lists and forms, read from the garden through the law\'s crosswalks; ' +
    'the private tab resolved off git; the chatter its history; the page as of the first save');
} catch (e) {
  let where = '';
  if (b) {
    try {
      await b.evaluate(`[...document.querySelectorAll('.modal button, .o_dialog button')].find(x => /details/i.test(x.textContent))?.click()`).catch(() => {});
      await b.sleep(300);
      where = await b.evaluate(`location.href + ' :: ' + ((document.querySelector('.o_dialog, .modal') || {}).innerText || '').slice(0, 1500)`);
      if (process.env.ODOO_HR_SHOT) await b.shot(process.env.ODOO_HR_SHOT);
    } catch { /* the page is gone */ }
  }
  console.error('FAIL: odoo_hr —', e.message, '\n  at:', where, b ? '\n  exceptions: ' + JSON.stringify(b.exceptions.slice(0, 5)) : '');
  process.exitCode = 1;
} finally {
  if (b) await b.close();
  if (daftard) daftard.kill();
  if (process.env.ODOO_HR_LOG) {
    try { writeFileSync(process.env.ODOO_HR_LOG, readFileSync(join(T, 'state', 'daftard.log'))); } catch { /* none */ }
  }
  await new Promise((r) => setTimeout(r, 500));          // the browser and daftard let go of their files first
  try { rmSync(T, { recursive: true, force: true, maxRetries: 10, retryDelay: 300 }); } catch (e) { console.error('odoo_hr: scratch left at', T, e.code); }
}
