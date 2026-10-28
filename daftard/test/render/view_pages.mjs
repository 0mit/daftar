// view_pages — a garden whose handplace is its page beans (daftard.json `handplace: "view"`), served by daftard and
// clicked through in headless Chromium, once in Persian and once in English: the navigation is the garden's page
// beans in the order it places them; each page is drawn in the chrome by the release's own runtime, renderers and
// widgets (loaded from /release/<garden>/ under the handplace's policy), in the garden's language and direction; a
// sheet's Save goes to the view's one write path and is one commit; the view's own page of a page bean (/view?page=)
// runs only its asset's scripts; where the release keeps a reader's way of reading, the Gregorian calendar and Latin
// digits chosen in the chrome draw the Persian page again in place, and the chrome's own days (today, the last read)
// with it, kept for a second browser, with no commit. (A legacy
// garden keeps daftard's own pages: internal/web/viewpages_test.go.)
//
//   node test/render/view_pages.mjs --tree <daftar tree whose view draws pages of readings>
//
// Self-contained: it grows two scratch gardens of invented beings (view_pages_garden.py), builds daftard from this
// tree, serves them, and opens each through daftard's door. It WRITES only to those scratch gardens. Fails on any page
// exception.
import assert from 'node:assert/strict';
import { spawn, spawnSync } from 'node:child_process';
import { mkdtempSync, readFileSync, rmSync, writeFileSync, mkdirSync } from 'node:fs';
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
if (!opt.tree) { console.error('node test/render/view_pages.mjs --tree <daftar tree>'); process.exit(2); }
const T = mkdtempSync(join(process.env.TMPDIR || tmpdir(), 'view-pages-'));
const step = (name) => console.log('·', name);
const py = process.env.PYTHON || 'python3';
function sh(cmd, args, o = {}) {
  const r = spawnSync(cmd, args, { encoding: 'utf8', ...o });
  if (r.status !== 0) throw new Error(`${cmd} ${args.join(' ')}: ${(r.stderr || '') + (r.stdout || '')}`.slice(-1500));
  return r.stdout;
}
const freePort = () => new Promise((ok) => { const s = net.createServer(); s.listen(0, '127.0.0.1', () => { const p = s.address().port; s.close(() => ok(p)); }); });
const PERSIAN_DIGIT = /[۰-۹]/;

let daftard, b;
try {
  step('two scratch gardens of invented beings, from the daftar tree');
  const grown = {};
  for (const name of ['g-fa', 'g-en']) {
    mkdirSync(join(T, name));
    grown[name] = JSON.parse(sh(py, [join(HERE, 'view_pages_garden.py'), opt.tree, join(T, name)]).trim().split('\n').pop()).garden;
  }
  step('daftard, built from this tree, serving them');
  const state = join(T, 'state');
  mkdirSync(state);
  const bin = join(T, 'daftard');
  sh('go', ['build', '-o', bin, './cmd/daftard'], { cwd: REPO });
  const port = await freePort();
  const garden = (name, lang, handplace) => ({ name, path: grown[name], python: py, title: name, kind: 'core', lang, gardener: 'sam', handplace });
  writeFileSync(join(state, 'daftard.json'), JSON.stringify({ listen: `127.0.0.1:${port}`,
    gardens: [garden('g-fa', 'fa', 'view'), garden('g-en', 'en', 'view')] }));
  daftard = spawn(bin, ['serve'], { env: { ...process.env, DAFTARD_NOTIFY: 'off', DAFTARD_STATE: state }, stdio: 'ignore' });
  const base = `http://127.0.0.1:${port}`;
  for (let i = 0; ; i++) {
    try { if ((await fetch(`${base}/health`)).ok) break; } catch { /* not yet */ }
    if (i > 300) throw new Error('daftard did not start');
    await new Promise((r) => setTimeout(r, 100));
  }
  const key = readFileSync(join(state, 'key'), 'utf8').trim();
  b = await browser({ base, key });
  const { evaluate, until, ready, click, exceptions } = b;
  const nav = () => evaluate(`[...document.querySelectorAll('#nav [data-nav]')].map(x => x.dataset.nav)`);
  const go = async (id) => { await click(`[data-nav="${id}"]`); await ready(); };
  const drawn = (sel, what) => until(`document.querySelector('#content .vp ${sel}')`, what, 120000);
  const head = (name) => sh('git', ['rev-parse', 'HEAD'], { cwd: grown[name] }).trim();

  for (const [name, lang, dir] of [['g-fa', 'fa', 'rtl'], ['g-en', 'en', 'ltr']]) {
    step(`${lang}: the navigation is the garden's page beans, in the order it places them`);
    await b.open(`g=${name}&static=1`);
    await ready();
    assert.deepEqual(await nav(), ['page-now', 'page-repair', 'page-time']);
    assert.deepEqual(await evaluate(`[...document.querySelectorAll('#nav [data-nav]')].map(x => x.firstChild.textContent.trim())`), ['Now', 'Repair', 'Time']);

    step(`${lang}: what waits, drawn by the release's queue, ${dir}`);
    await go('page-now');
    await drawn('.eg-lead[data-kind="case"]', 'the case waiting at its step');
    assert.equal(await evaluate('document.documentElement.dir'), dir);
    assert.equal(await evaluate('document.documentElement.lang'), lang);
    assert.ok(await evaluate(`!!window.viewMount && !!window.daftarWidgets && !!window.daftarArchetypes`), 'the release was not loaded');

    step(`${lang}: the time, drawn by the release's timeline, in the reader's digits`);
    await go('page-time');
    await drawn('.eg-event', 'the class on the timeline');
    const time = await evaluate(`document.querySelector('#content .vp').innerText`);
    assert.equal(PERSIAN_DIGIT.test(time), lang === 'fa', `digits of ${lang}: ${time.slice(0, 200)}`);

    step(`${lang}: daftard's own chrome in the reader's language — its buttons, greeting, footer and sync`);
    const chrome = await evaluate(`[...document.querySelectorAll('aside, header, #sync')].map(x => x.innerText).join(' | ')`);
    const page = await evaluate('document.body.innerText');
    if (lang === 'en') {
      assert.ok(!/[\u0600-\u06FF]/.test(page), `no Persian anywhere on an English garden's page: ${page.slice(0, 400)}`);
      for (const w of ['Refresh', 'Welcome', 'Last read', 'Your private garden']) assert.ok(chrome.includes(w), `the chrome says ${w}: ${chrome}`);
    } else {
      for (const w of ['به‌روزرسانی', 'خوش آمدی', 'آخرین خواندن', 'دفتر خصوصی شما']) assert.ok(chrome.includes(w), `the chrome says ${w}: ${chrome}`);
    }

    step(`${lang}: the repair's sheet; its summary changed in the one Edit, saved through the view's write path`);
    await go('page-repair');
    await drawn('[data-do="edit"]', "the sheet's Edit");
    const before = head(name), said = `mended in ${lang} ${Date.now().toString(36)}`;
    await click('#content .vp [data-do="edit"]');
    await until(`document.querySelector('#content .vp [name="header.summary"]')`, 'the summary to edit');
    await evaluate(`(() => { const f = document.querySelector('#content .vp [name="header.summary"]'); f.value = ${JSON.stringify(said)}; f.dispatchEvent(new Event('input', {bubbles: true})); })()`);
    await click('#content .vp [data-do="save"]');
    await until(`document.querySelector('#content .vp')?.innerText.includes(${JSON.stringify(said)}) && !document.querySelector('#content .vp [data-do="save"]')`, 'the page to show the saved summary', 120000);
    const after = head(name);
    assert.notEqual(after, before, 'no commit was made');
    assert.equal(sh('git', ['rev-list', '--count', `${before}..${after}`], { cwd: grown[name] }).trim(), '1', 'one Save is one commit');
    assert.ok(readFileSync(join(grown[name], 'beans', 'repair-1.md'), 'utf8').includes(said), 'the bean holds the new summary');

    if (lang === 'fa' && await evaluate(`!!(window.daftarWidgets && window.daftarWidgets.prefs)`)) {
      step("fa: the reader's own way of reading — the Gregorian calendar and Latin digits, chosen in the chrome, the page and the chrome's own days drawn again in place; kept for a second browser; no commit");
      const before2 = head(name);
      await b.open(`g=${name}&static=1`); await ready();
      await go('page-time');
      await drawn('.eg-event', 'the class on the timeline');
      assert.ok(PERSIAN_DIGIT.test(await evaluate(`document.querySelector('#content .vp').innerText`)), "unset: the language's own digits");
      const chrome = () => evaluate(`document.getElementById('today').innerText + ' | ' + document.getElementById('sync').innerText`);
      assert.ok(PERSIAN_DIGIT.test(await chrome()), "unset: the chrome's own days in the language's own digits");
      // drawn as days, never as the markup a widget made of them (the release's widgets make their own Safe HTML)
      const markup = /<\/?time|w-moment|datetime=/;
      assert.ok(!markup.test(await chrome()), `unset: the chrome's own days drawn, not their markup: ${await chrome()}`);
      await click('aside [data-action="view-prefs"]');
      await until(`document.querySelector('#prefsdlg[open] [name="pref.ca"]')`, 'the panel');
      await evaluate(`(() => { const d = document.getElementById('prefsdlg'), set = (n, v) => { const x = d.querySelector('[name="pref.' + n + '"]'); x.value = v; x.dispatchEvent(new Event('change', {bubbles: true})); };
        set('ca', 'gregory'); set('nu', 'latn'); })()`);
      assert.ok(!PERSIAN_DIGIT.test(await evaluate(`document.querySelector('#prefsdlg .w-prefs-sample').innerText`)), 'the sample shows the choice');
      await evaluate(`window.__same = true`);
      await click('#prefsdlg [data-prefs="save"]');
      await until(`!document.querySelector('#prefsdlg[open]') && document.querySelector('#content .vp .eg-event') && !/[۰-۹]/.test(document.querySelector('#content .vp').innerText)`, 'the page in Latin digits', 120000);
      assert.equal(await evaluate('window.__same'), true, 'drawn again in place, not reloaded');
      await until(`!/[۰-۹]/.test(document.getElementById('today').innerText + document.getElementById('sync').innerText)`, "the chrome's own days in Latin digits", 60000);
      const days = await chrome();
      assert.ok(/\d/.test(days) && /(ژانویه|فوریه|مارس|آوریل|مه|ژوئن|ژوئیه|اوت|سپتامبر|اکتبر|نوامبر|دسامبر)/.test(days), `the chrome's own days in the Gregorian calendar: ${days}`);
      assert.ok(!markup.test(days), `the chrome's own days drawn, not their markup: ${days}`);
      const b2 = await browser({ base, key });
      try {
        await b2.open(`g=${name}&static=1`); await b2.ready();
        await b2.evaluate(`location.hash = 'page-time'`); await b2.sleep(300); await b2.ready();
        await b2.until(`document.querySelector('#content .vp .eg-event')`, 'the timeline in a second browser', 120000);
        assert.ok(!PERSIAN_DIGIT.test(await b2.evaluate(`document.querySelector('#content .vp').innerText`)), 'kept for a second browser');
      } finally { await b2.close(); }
      assert.equal(head(name), before2, 'a preference makes no commit');
      assert.equal(sh('git', ['status', '--porcelain'], { cwd: grown[name] }).trim(), '', 'nor any change in the garden');
    }

    step(`${lang}: the view's own page of a page bean runs only its asset's scripts`);
    await b.navigate(`${base}/view?g=${name}&page=page-now`);
    await until(`document.querySelector('#view')?.children.length > 0 && !!window.daftarWidgets && !!window.daftarArchetypes`,
      "the view's own page, its scripts run by their hashes", 120000);
  }

  assert.deepEqual(exceptions, [], 'a page threw');
  console.log('PASS: view_pages — the page beans as the navigation, drawn by the release in Persian and English, a Save through the view\'s write path');
} catch (e) {
  console.error('FAIL:', e.message);
  if (b?.exceptions?.length) console.error('page exceptions:', b.exceptions);
  process.exitCode = 1;
} finally {
  if (b) await b.close();
  if (daftard) daftard.kill();
  rmSync(T, { recursive: true, force: true });
}
