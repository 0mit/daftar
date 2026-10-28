// core_front — the front page of a garden of the core alone (`kind: core`), which carries no handplace of its own,
// served by daftard and opened in headless Chromium: it says what the garden offers on this machine — its register's
// Odoo screens, read live, opened by Odoo's own client through the handplace's door — and a garden that offers nothing
// yet says so; neither is left «در حال خواندن دفتر…» (2026-10-12: the page asked the dashboard's payload, which a garden
// of the core does not have, and said it was reading for ever). A garden whose worker cannot read it at all says that,
// in the place it said it was reading. (A dashboard's and a board's pages are their own: internal/web/odoo_test.go,
// TestCoreFrontOffers.)
//
//   node test/render/core_front.mjs --tree <daftar tree> [--shots <dir>]
//
// Self-contained: it grows two scratch gardens of the core (core_front_garden.py), builds daftard from this tree and
// serves them, the register named at a loopback port nothing listens on — the front page asks it nothing. It writes
// only to its scratch. Fails on any exception of the handplace's page.
import assert from 'node:assert/strict';
import { spawn, spawnSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import net from 'node:net';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { browser } from './cdp.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(HERE, '..', '..');
const opt = {};
const argv = process.argv.slice(2);
for (let i = 0; i < argv.length; i += 2) opt[argv[i].replace(/^--/, '')] = argv[i + 1];
if (!opt.tree) { console.error('node test/render/core_front.mjs --tree <daftar tree>'); process.exit(2); }
const T = mkdtempSync(join(process.env.TMPDIR || tmpdir(), 'core-front-'));
const step = (name) => console.log('·', name);
const py = process.env.PYTHON || 'python3';
function sh(cmd, args, o = {}) {
  const r = spawnSync(cmd, args, { encoding: 'utf8', ...o });
  if (r.status !== 0) throw new Error(`${cmd} ${args.join(' ')}: ${(r.stderr || '') + (r.stdout || '')}`.slice(-1500));
  return r.stdout;
}
const freePort = () => new Promise((ok) => { const s = net.createServer(); s.listen(0, '127.0.0.1', () => { const p = s.address().port; s.close(() => ok(p)); }); });
const READING = 'در حال خواندن دفتر';

let daftard, b;
try {
  step('two scratch gardens of the core, from the daftar tree: one with a register and its captured views, one bare');
  const grown = JSON.parse(sh(py, [join(HERE, 'core_front_garden.py'), opt.tree, T]).trim().split('\n').pop());
  mkdirSync(join(T, 'broken'));                     // a dashboard's folder with no dashboard: its worker cannot start

  step('daftard, built from this tree, serving them; the register named at a port nothing listens on');
  const state = join(T, 'state');
  mkdirSync(join(state, 'odoo', '19.0'), { recursive: true });
  writeFileSync(join(state, 'odoo', '19.0', 'CLIENT.json'), '{}');      // 19's client taken on this machine
  const bin = join(T, 'daftard');
  sh('go', ['build', '-o', bin, './cmd/daftard'], { cwd: REPO });
  const [port, oport, nowhere] = [await freePort(), await freePort(), await freePort()];
  const garden = (name, path, extra = {}) => ({ name, path, python: py, title: name, kind: 'core', lang: 'fa', gardener: 'sam', ...extra });
  writeFileSync(join(state, 'daftard.json'), JSON.stringify({ listen: `127.0.0.1:${port}`, odoo_listen: `127.0.0.1:${oport}`,
    gardens: [garden('g-reg', grown.register, { register: { series: '19.0', url: `http://127.0.0.1:${nowhere}`, db: 'none', bean: 'register' } }),
      garden('g-bare', grown.bare), garden('g-broken', join(T, 'broken'), { kind: 'dashboard' })] }));
  daftard = spawn(bin, ['serve'], { env: { ...process.env, DAFTARD_NOTIFY: 'off', DAFTARD_STATE: state, PYTHONDONTWRITEBYTECODE: '1' }, stdio: 'ignore' });
  const base = `http://127.0.0.1:${port}`;
  for (let i = 0; ; i++) {
    try { if ((await fetch(`${base}/health`)).ok) break; } catch { /* not yet */ }
    if (i > 600) throw new Error('daftard did not start');
    await new Promise((r) => setTimeout(r, 100));
  }
  const key = readFileSync(join(state, 'key'), 'utf8').trim();
  b = await browser({ base, key });
  const { evaluate, until } = b;
  const content = () => b.textOf('#content');

  step("a garden with a register: its front page offers the register's Odoo screens, and reads nothing for ever");
  await b.open('g=g-reg&static=1');                  // waits for the page to render: on a garden of the core, it never did
  const screens = await evaluate(`[...document.querySelectorAll('#content .core-screen')].map(x => ({series: x.dataset.series,
    register: x.dataset.register || '', href: x.querySelector('a.primary')?.getAttribute('href') || '', text: x.textContent}))`);
  assert.equal(screens.length, 1, JSON.stringify(screens));
  assert.equal(screens[0].href, '/odoo?g=g-reg&series=19.0');
  assert.equal(screens[0].register, '1');
  assert.match(screens[0].text, /The register/);
  assert.ok(!(await content()).includes(READING), await content());
  assert.ok(!(await b.textOf('#sync')).includes(READING), await b.textOf('#sync'));
  assert.deepEqual(await evaluate(`[...document.querySelectorAll('#nav [data-nav]')].map(x => x.dataset.nav)`), ['core']);
  assert.deepEqual(b.exceptions, []);
  if (opt.shots) await b.shot(join(opt.shots, 'core-front-register.png'));

  step("...and its link opens Odoo's screens on Odoo's own origin, through the handplace's door");
  await b.click('#content .core-screen a.primary');
  await until(`location.host === 'localhost:${oport}' && location.pathname === '/odoo'`, "Odoo's page on its own origin", 20000);

  step('a garden that offers nothing yet says so');
  b.exceptions.length = 0;
  await b.open('g=g-bare&static=1');
  assert.match(await content(), /این دفتر هنوز صفحه‌ای ندارد که اینجا باز شود/);
  assert.ok(!(await content()).includes(READING));
  assert.equal(await evaluate(`document.querySelectorAll('#content .core-screen').length`), 0);
  assert.deepEqual(b.exceptions, []);
  if (opt.shots) await b.shot(join(opt.shots, 'core-front-bare.png'));

  step('a garden its worker cannot read: the page says so where it said it was reading');
  await b.open('g=g-broken&static=1');
  assert.ok(!(await content()).includes(READING), await content());
  assert.ok(await evaluate(`!!document.querySelector('#content .panel')`), await content());
  assert.ok(!(await b.textOf('#sync')).includes(READING), await b.textOf('#sync'));
  assert.deepEqual(b.exceptions, []);
  if (opt.shots) await b.shot(join(opt.shots, 'core-front-broken.png'));
  console.log('PASS: core_front — a garden of the core says what it offers here (its register\'s Odoo screens, opened through the door), or that it offers nothing yet; none reads for ever');
} catch (e) {
  console.error('FAIL: core_front —', e.message);
  process.exitCode = 1;
} finally {
  if (b) await b.close();
  if (daftard) daftard.kill();
  rmSync(T, { recursive: true, force: true });
}
