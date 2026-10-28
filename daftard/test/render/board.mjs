// board — a board's garden (`kind: board`) clicked through in headless Chromium: its summary, payments, agreements,
// exchange and «منتظر شما»; a payment recorded, refused without a share-holder, corrected and taken out. It WRITES to
// the garden it is pointed at, so it is run against a SCRATCH copy only, whose daftard serves it as `kind: board`:
//
//   DAFTAR_URL=… DAFTAR_KEY=… DAFTAR_GARDEN=<garden> DAFTAR_AGREEMENT=<an agreement this garden made> \
//   [DAFTAR_READONLY=<an agreement taken from another garden>] node test/render/board.mjs
//
// The agreements are the garden's own beans, so they are given here and never written in this file. Any exception a
// page throws fails the run.
import assert from 'node:assert/strict';
import { browser } from './cdp.mjs';

const BASE = process.env.DAFTAR_URL, KEY = process.env.DAFTAR_KEY, GARDEN = process.env.DAFTAR_GARDEN;
const AGREEMENT = process.env.DAFTAR_AGREEMENT, READONLY = process.env.DAFTAR_READONLY;
if (!BASE || !KEY || !GARDEN || !AGREEMENT) { console.error('DAFTAR_URL, DAFTAR_KEY, DAFTAR_GARDEN and DAFTAR_AGREEMENT are needed'); process.exit(2); }
const b = await browser({base: BASE, key: KEY});
const {evaluate, until, ready, click, fill, textOf, exceptions} = b;
const step = name => console.log('·', name);
const stamp = Date.now().toString(36), WHAT = 'آزمون تابلو ' + stamp, FIXED = 'آزمون اصلاح تابلو ' + stamp;
const shows = (words, ms = 120000) => until(`document.getElementById('content').textContent.includes(${JSON.stringify(words)})`, words, ms);
const page = async id => { await click(`[data-nav="${id}"]`); await ready(); };
const saved = what => until(`!document.querySelector('dialog[open]') && document.getElementById('notice').textContent.includes('ذخیره شد')`, what, 600000);

try {
  step('the summary, as a board shows it');
  await b.open(`g=${GARDEN}&static=1`);
  assert.deepEqual(await evaluate(`[...document.querySelectorAll('#nav [data-nav]')].map(x => x.dataset.nav)`), ['home', 'lead', 'pays', 'agreements', 'exchange']);
  assert.ok(await evaluate(`document.querySelectorAll('.stat').length >= 1`), 'no balance');

  step('each page renders');
  for (const id of ['pays', 'agreements', 'exchange', 'lead']) await page(id);
  if (READONLY) {
    await page('agreements');
    const ro = await evaluate(`(() => { const s = [...document.querySelectorAll('section.panel')].find(x => x.querySelector('h2')?.textContent && !x.querySelector('[data-action="board-add"]') && x.textContent.includes('فقط خواندنی')); return !!s; })()`);
    assert.ok(ro, 'an agreement from another garden is read only');
  }

  step('a payment: refused without a share-holder, then recorded');
  await page('agreements');
  await click(`[data-action="board-add"][data-a="${AGREEMENT}"]`);
  await until(`document.querySelector('dialog[open] input[name="what"]')`, 'the payment form');
  await fill('dialog[open] input[name="what"]', WHAT);
  await fill('dialog[open] input[name="count"]', '۱۲۳٫۵');
  await evaluate(`document.querySelectorAll('dialog[open] input[type="checkbox"]').forEach(c => c.checked = false)`);
  await click('dialog[open] button[type="submit"]');
  await until(`document.querySelector('dialog[open] .w-invalid')`, 'no share-holder to be refused');
  await evaluate(`document.querySelectorAll('dialog[open] input[type="checkbox"]').forEach(c => c.checked = true)`);
  await evaluate(`document.querySelector('dialog[open] input[name^="share-"]').value = '2'`);   // two shares to one
  await click('dialog[open] button[type="submit"]');
  await saved('the payment to be saved');
  await page('pays');
  await shows(WHAT);
  assert.ok(await evaluate(`[...document.querySelectorAll('#content tr')].find(r => r.textContent.includes(${JSON.stringify(WHAT)}))?.textContent.includes('×')`), 'the 2:1 share is not shown');

  step('the payment categorised, in the gardener\'s own books');
  await evaluate(`[...document.querySelectorAll('[data-action="board-categorize"]')].find(x => x.closest('tr').textContent.includes(${JSON.stringify(WHAT)})).dataset.cat = '1'`);
  await click('[data-action="board-categorize"][data-cat="1"]');
  await until(`document.querySelector('dialog[open] input[name="category"]')`, 'the category form');
  await fill('dialog[open] input[name="category"]', 'خانه');
  await click('dialog[open] button[type="submit"]');
  await saved('the category to be saved');
  await page('pays');
  assert.ok(await evaluate(`[...document.querySelectorAll('#content tr')].find(r => r.textContent.includes(${JSON.stringify(WHAT)}))?.textContent.includes('خانه')`), 'the category is not shown');
  if (READONLY) {
    step('a payment another garden recorded, categorised all the same');
    const other = await evaluate(`(() => { const r = [...document.querySelectorAll('#content tr')].find(r => r.textContent.includes('اصلاح در') && r.querySelector('[data-action="board-categorize"]')); if (!r) return ''; const b = r.querySelector('[data-action="board-categorize"]'); b.dataset.cat = '2'; return b.dataset.p; })()`);
    if (other) {
      await click('[data-action="board-categorize"][data-cat="2"]');
      await until(`document.querySelector('dialog[open] input[name="category"]')`, 'the category form');
      await fill('dialog[open] input[name="category"]', 'قبض و اشتراک ' + stamp);
      await click('dialog[open] button[type="submit"]');
      await saved('the category of another garden\'s payment to be saved');
    }
  }

  step('the payment corrected: a reason asked, then saved');
  const editing = await evaluate(`(() => { const e = [...document.querySelectorAll('[data-action="board-edit"]')].find(x => x.closest('tr').textContent.includes(${JSON.stringify(WHAT)})); e.dataset.pick = '1'; return e.dataset.p; })()`);
  await click(`[data-action="board-edit"][data-pick="1"]`);
  await until(`document.querySelector('dialog[open] input[name="what"]')?.value === ${JSON.stringify(WHAT)}`, 'the correction form, filled');
  await fill('dialog[open] input[name="what"]', FIXED);
  await click('dialog[open] button[type="submit"]');
  await until(`document.querySelector('dialog[open] [data-field="reason"].w-invalid')`, 'a correction without its reason to be refused');
  await fill('dialog[open] textarea[name="reason"]', 'آزمون: شرح اشتباه بود');
  await click('dialog[open] button[type="submit"]');
  await saved('the correction to be saved');
  await page('pays');
  await shows(FIXED);

  step('the payment taken out');
  await click(`[data-action="board-delete"][data-p="${editing}"]`);
  await until(`document.querySelector('dialog[open] textarea[name="reason"]')`, 'the removal form');
  await fill('dialog[open] textarea[name="reason"]', 'آزمون: پاک شود');
  await click('dialog[open] button[type="submit"]');
  await saved('the removal to be saved');
  await page('pays');
  assert.ok(!(await textOf('#content')).includes(FIXED), 'still there');

  assert.deepEqual(exceptions, [], 'a page threw');
  console.log('PASS: board — summary, pages, a payment recorded, refused, corrected and taken out');
} catch (e) {
  console.error('FAIL:', e.message);
  if (exceptions.length) console.error('page exceptions:', exceptions);
  process.exitCode = 1;
} finally {
  await b.close();
}
