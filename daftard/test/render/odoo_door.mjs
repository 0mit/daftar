// odoo_door — the way from the handplace into Odoo's own origin (odoo.go), walked in headless Firefox and in headless
// Chromium: a one-time code at the handplace's door, its redirect to the page's door (/odoo?g=…), that door's redirect
// to Odoo's origin with a token (/odoo/enter?t=…), and the seat the token becomes there — a SameSite=Strict cookie of
// Odoo's origin alone. Each browser must end on Odoo's client page with its seat, the token gone from the address bar.
//
// Firefox holds SameSite to the whole of a redirect chain: one that began on another site (here the handplace's
// 127.0.0.1, then localhost) sends no Strict cookie on any later hop of it, where Chromium sends it. When /odoo/enter
// redirected to /odoo, Firefox arrived without the seat it had just been given, and the page said «اودو را از دفتر باز
// کنید.» (2026-10-12); /odoo/enter now ends the chain on a page of Odoo's own origin, which moves on to /odoo itself.
//
//   node test/render/odoo_door.mjs --tree <daftar tree>
//
// Self-contained: daftard built from this tree, its state and ports this run's own, a garden of the core grown from the
// daftar tree (core_front_garden.py's bare one: the door and the session read it, nothing writes it), and a stand-in for
// a series' client — CLIENT.json, and its two assets, the script no more than the module loader daftard's own page
// script registers with: the client's page is daftard's own, and tells by itself whether the seat came with it. Each
// browser in a profile of its own, made and removed by the run. A browser that is not on the machine is said and
// skipped; a page exception fails.
import assert from 'node:assert/strict';
import { spawn, spawnSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import net from 'node:net';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { browser } from './cdp.mjs';
import { firefox } from './bidi.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(HERE, '..', '..');
const opt = {};
const argv = process.argv.slice(2);
for (let i = 0; i < argv.length; i += 2) opt[argv[i].replace(/^--/, '')] = argv[i + 1];
if (!opt.tree) { console.error('node test/render/odoo_door.mjs --tree <daftar tree>'); process.exit(2); }
const py = process.env.PYTHON || 'python3';
const T = mkdtempSync(join(process.env.TMPDIR || tmpdir(), 'odoo-door-'));
const step = (name) => console.log('·', name);
const freePort = () => new Promise((ok) => { const s = net.createServer(); s.listen(0, '127.0.0.1', () => { const p = s.address().port; s.close(() => ok(p)); }); });
const has = (cmd) => spawnSync('sh', ['-c', `command -v ${cmd}`]).status === 0;
const ASK_FROM_HANDPLACE = 'اودو را از دفتر باز کنید';

let daftard;
const walked = [], failed = [];
try {
  step('a garden of the core, from the daftar tree; daftard, built from this tree, serving it with a series 19 client');
  const grown = spawnSync(py, [join(HERE, 'core_front_garden.py'), opt.tree, join(T, 'grown')], { encoding: 'utf8' });
  if (grown.status !== 0) throw new Error('core_front_garden.py: ' + (grown.stderr + grown.stdout).slice(-800));
  const garden = JSON.parse(grown.stdout.trim().split('\n').pop()).bare;
  const state = join(T, 'state');
  const assets = join(state, 'odoo', '19.0', 'web', 'assets', 'debug');
  mkdirSync(assets, { recursive: true });
  writeFileSync(join(state, 'odoo', '19.0', 'CLIENT.json'), '{}');
  writeFileSync(join(assets, 'web.assets_web.js'), "// a stand-in for the series' client: its module loader, no more\nodoo.define = function () {};\n");
  writeFileSync(join(assets, 'web.assets_web.css'), '/* a stand-in for the client\'s style */\n');
  const bin = join(T, 'daftard');
  const built = spawnSync('go', ['build', '-o', bin, './cmd/daftard'], { cwd: REPO, encoding: 'utf8' });
  if (built.status !== 0) throw new Error('go build: ' + built.stderr);
  const [port, oport] = [await freePort(), await freePort()];
  writeFileSync(join(state, 'daftard.json'), JSON.stringify({ listen: `127.0.0.1:${port}`, odoo_listen: `127.0.0.1:${oport}`,
    gardens: [{ name: 'g', path: garden, python: py, title: 'The garden', kind: 'core', gardener: 'sam' }] }));
  daftard = spawn(bin, ['serve'], { env: { ...process.env, DAFTARD_NOTIFY: 'off', DAFTARD_STATE: state, PYTHONDONTWRITEBYTECODE: '1' }, stdio: 'ignore' });
  const base = `http://127.0.0.1:${port}`, origin = `localhost:${oport}`;
  for (let i = 0; ; i++) {
    try { if ((await fetch(`${base}/health`)).ok) break; } catch { /* not yet */ }
    if (i > 300) throw new Error('daftard did not start');
    await new Promise((r) => setTimeout(r, 100));
  }
  const key = readFileSync(join(state, 'key'), 'utf8').trim();
  const to = 'to=' + encodeURIComponent('/odoo?g=g&series=19.0');

  // where a browser stands once the way is walked: Odoo's client page with its seat, or what it was told
  const arrived = (b) => b.evaluate(`({host: location.host, path: location.pathname, search: location.search,
    client: !!document.querySelector('script[src="/odoo/session.js"]') && document.body.classList.contains('o_web_client'),
    says: document.body.innerText.slice(0, 120)})`);

  for (const [name, cmd] of [['Firefox', 'firefox'], ['Chromium', 'chromium']]) {
    if (!has(cmd)) {
      console.log(`SKIP: odoo_door — no ${cmd} on this machine`);
      continue;
    }
    step(`${name}: the handplace's door, then Odoo's origin by its one-time token`);
    const b = name === 'Firefox' ? await firefox({ base, key }) : await browser({ base, key });
    try {
      if (name === 'Firefox') {
        await b.open(to);
      } else {                                   // cdp.mjs's open waits for the handplace's own page, which this is not
        const { once } = await (await fetch(`${base}/door`, { method: 'POST', headers: { 'X-Daftard-Key': key } })).json();
        await b.navigate(`${base}/?once=${encodeURIComponent(once)}&${to}`);
      }
      // the page settles on Odoo's origin: its client, or the sentence that sends the reader back to the handplace
      await b.until(`location.host === ${JSON.stringify(origin)} && location.pathname === '/odoo' && document.readyState === 'complete'
        && (!!document.querySelector('script[src="/odoo/session.js"]') || document.body.innerText.includes(${JSON.stringify(ASK_FROM_HANDPLACE)}))`,
      "Odoo's origin", 20000);
      const at = await arrived(b);
      assert.ok(!at.says.includes(ASK_FROM_HANDPLACE), `${name} arrived without its seat: «${at.says}»`);
      assert.ok(at.client, `${name}: Odoo's client page — ${JSON.stringify(at)}`);
      assert.equal(at.search, '', `${name}: the token is gone from the address bar`);
      if (name === 'Firefox') {
        const seat = (await b.cookies()).find((c) => c.name === 'daftard-odoo');
        assert.ok(seat && seat.sameSite === 'strict' && seat.httpOnly && seat.domain === 'localhost',
          `the seat is Odoo's origin's own, HttpOnly and Strict: ${JSON.stringify(seat)}`);
        const page = b.requests.filter((r) => r.url === `http://${origin}/odoo`);
        assert.ok(page.length && page.every((r) => r.cookies.includes('daftard-odoo')) && page.every((r) => !r.cookies.includes('daftard')),
          `the page was asked with its seat, and with nothing of the handplace's: ${JSON.stringify(page)}`);
      }
      assert.deepEqual(b.exceptions, [], `${name}: no page exception`);
      walked.push(name);
      console.log(`  ${name}: Odoo's client page, with its seat`);
    } catch (e) {                                 // said, and the next browser walks the way all the same
      failed.push(name);
      console.log(`  ${name}: FAILED — ${e.message.split('\n')[0]}`);
    } finally {
      await b.close();
    }
  }
  if (failed.length) throw new Error(`the way into Odoo's origin fails in ${failed.join(' and ')}`);
  if (!walked.length) throw new Error('no browser to walk the way in');
  console.log(`PASS: odoo_door — the way into Odoo's origin ends on its client page with its Strict seat in ${walked.join(' and ')}`);
} catch (e) {
  console.error('FAIL: odoo_door —', e.message);
  process.exitCode = 1;
} finally {
  if (daftard) daftard.kill();
  rmSync(T, { recursive: true, force: true });
}
