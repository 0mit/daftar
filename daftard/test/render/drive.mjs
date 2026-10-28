// drive — the handplace clicked through in headless Chromium, over the DevTools protocol (Node's own WebSocket, no
// packages): the landing page, a decision through its dialog, a label in admin mode, debug mode's logs. It WRITES to
// the garden it is pointed at (an answer, a label), so it is run against a scratch copy only:
//
//   DAFTAR_URL=http://127.0.0.1:8790 DAFTAR_KEY=<key> DAFTAR_GARDEN=<garden> node test/render/drive.mjs
//
// Any exception a page throws fails the run.
import assert from 'node:assert/strict';
import { browser } from './cdp.mjs';

const BASE = process.env.DAFTAR_URL, KEY = process.env.DAFTAR_KEY, GARDEN = process.env.DAFTAR_GARDEN;
if (!BASE || !KEY || !GARDEN) { console.error('DAFTAR_URL, DAFTAR_KEY and DAFTAR_GARDEN are needed'); process.exit(2); }

const b = await browser({base: BASE, key: KEY});
const {evaluate, until, ready, click, fill, textOf, open, exceptions, logs} = b;
const step = name => console.log('·', name);

try {
  step('the landing list');
  await open(`to=/go/${GARDEN}&static=1`);
  assert.equal(await evaluate('location.pathname'), `/go/${GARDEN}`);
  const rows = await evaluate(`document.querySelectorAll('[data-action="go-lead"][data-kind="pending"]').length`);
  assert.ok(rows > 0, 'no parked decision is listed');

  step('a parked decision, opened from the list');
  const slug = await evaluate(`document.querySelector('[data-action="go-lead"][data-kind="pending"]').dataset.id`);
  await click('[data-action="go-lead"][data-kind="pending"]');
  await until(`location.pathname === '/go/${GARDEN}/pending/${slug}' && document.querySelector('.lead h2')`, 'the decision page');
  await ready();

  step('an answer: refused empty, then saved');
  await click('[data-action="lead-decide"][data-decision="answered"]');
  await until(`document.querySelector('dialog[open] textarea[name="words"]')`, 'the answer dialog');
  await click('dialog[open] button[type="submit"]');
  await until(`document.querySelector('dialog[open] .w-invalid')`, 'the empty answer to be refused');
  await fill('dialog[open] textarea[name="words"]', 'پیش از تصمیم با همکارم صحبت می‌کنم.');
  await click('dialog[open] button[type="submit"]');
  await until(`!document.querySelector('dialog[open]') && location.pathname === '/go/${GARDEN}'`, 'the answer to be saved', 600000);
  await ready();
  assert.match(await textOf('#notice'), /پاسخ شما در دفتر ثبت شد/);

  step('a label changed in admin mode');
  await open('static=1&admin=1');
  await click('[data-action="edit-label"][data-key="nav.clients"]');
  await until(`document.querySelector('dialog[open] input[name="text"]')`, 'the label dialog');
  await fill('dialog[open] input[name="text"]', 'مراجعان');
  await click('dialog[open] button[type="submit"]');
  await until(`!document.querySelector('dialog[open]') && document.querySelector('[data-nav="clients"]')?.textContent.includes('مراجعان')`, 'the menu to read the label');

  step('the person\'s list of their labels');
  await click('[data-action="my-labels"]');
  await until(`document.querySelector('dialog[open] table')`, 'the list');
  const list = await textOf('dialog[open] table');
  assert.match(list, /nav\.clients[\s\S]*مراجعان[\s\S]*به‌روز/);
  await click('dialog[open] [data-close]');

  step('the label set back');
  await open('static=1&admin=1');
  await click('[data-action="my-labels"]');
  await until(`document.querySelector('dialog[open] [data-action="reset-label"][data-key="nav.clients"]')`, 'the reset button');
  await click('dialog[open] [data-action="reset-label"][data-key="nav.clients"]');
  await until(`!document.querySelector('[data-nav="clients"]')?.textContent.includes('مراجعان')`, 'the page word again');
  await click('dialog[open] [data-close]');

  step('debug mode logs');
  logs.length = 0;
  await open('static=1&debug=1');
  await until(`true`, 'logs');
  assert.ok(logs.some(l => /\[daftar \+/.test(l) && /GET \/api\/dashboard/.test(l)), 'no timed read in the console:\n' + logs.join('\n'));
  assert.ok(logs.some(l => /render home/.test(l)), 'no render logged');
  await open('static=1&debug=0');

  assert.deepEqual(exceptions, [], 'a page threw');
  console.log('PASS: drive — landing, decision, labels, debug');
} catch (e) {
  console.error('FAIL:', e.message);
  if (exceptions.length) console.error('page exceptions:', exceptions);
  process.exitCode = 1;
} finally {
  await b.close();
}
