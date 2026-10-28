// accounts — the agreements, categorising and exchange pages clicked through in headless Chromium. It WRITES to the
// garden it is pointed at (two transactions, one saved behind the page to see a stale save refused, a correction, a
// category, a consent turned off and on), so it is run against a SCRATCH copy only, whose daftard does not sync:
//
//   DAFTAR_URL=http://127.0.0.1:8793 DAFTAR_KEY=<key> DAFTAR_GARDEN=<garden> \
//   DAFTAR_AGREEMENT=<an agreement shared with another garden> DAFTAR_CORRECT_IN=<an agreement holding a payment> \
//   node test/render/accounts.mjs
//
// The agreements are the garden's own beans, so they are given here and never written in this file (the public gate).
// Any exception a page throws fails the run.
import assert from 'node:assert/strict';
import { browser } from './cdp.mjs';

const BASE = process.env.DAFTAR_URL, KEY = process.env.DAFTAR_KEY, GARDEN = process.env.DAFTAR_GARDEN;
// an agreement is chosen once, by itself; the garden writes the payment into its own ledger under it (book.agreements)
const AGREEMENT = process.env.DAFTAR_AGREEMENT;
// a payment in this agreement is corrected through the books' own form
const CORRECT_IN = process.env.DAFTAR_CORRECT_IN;
if (!BASE || !KEY || !GARDEN || !AGREEMENT || !CORRECT_IN) {
  console.error('DAFTAR_URL, DAFTAR_KEY, DAFTAR_GARDEN, DAFTAR_AGREEMENT and DAFTAR_CORRECT_IN are needed');
  process.exit(2);
}
const b = await browser({base: BASE, key: KEY});
const {evaluate, until, ready, click, fill, textOf} = b;
const step = name => console.log('·', name);
const stamp = Date.now().toString(36);
const WHAT = 'آزمون ثبت ' + stamp, FIXED = 'آزمون اصلاح ' + stamp, CATEGORY = 'دستهٔ آزمون ' + stamp;
const saved = (what, ms = 300000) => until(`!document.querySelector('dialog[open]') && document.getElementById('notice')?.textContent.includes('در دفتر ذخیره شد')`, what, ms);
// a save made behind the page, as another writer would: through daftard, at the garden's head now
async function saveBehind(bean, what) {
  const headers = {'X-Daftard-Key': KEY}, q = '?g=' + encodeURIComponent(GARDEN);   // the key in its header, never a cookie (audit 2.7)
  const d = await (await fetch(BASE + '/api/dashboard' + q, {headers})).json();
  const payer = Object.keys(d.agreements.find(a => a.id === bean).parties)[0];
  const r = await fetch(BASE + '/api/save' + q, {method: 'POST', headers: {...headers, Origin: BASE, 'X-CSRF-Token': d.csrf, 'Content-Type': 'application/json'},
    body: JSON.stringify({kind: 'transaction', bean, head: d.head, request: crypto.randomUUID().replace(/-/g, ''),
      values: {what, count: '1', unit: 'TRY', day: '', payer, allocation: 'equal', category: '', note: ''}})});
  assert.equal(r.status, 200, 'the save behind the page: ' + await r.text());
}
const shows = (words, ms = 60000) => until(`document.getElementById('content').textContent.includes(${JSON.stringify(words)})`, words, ms);

try {
  step('the agreements page');
  await b.page('accounts');
  assert.ok(await evaluate(`document.querySelectorAll('.stat').length >= 1`), 'no balance per currency');
  assert.ok(await evaluate(`document.querySelectorAll('[data-action="new-transaction"][data-agreement]').length >= 1`), 'no agreement panel');

  step('a transaction: refused empty, its payer following the agreement, then saved');
  await click('[data-action="new-transaction"]:not([data-agreement])');
  await until(`document.querySelector('dialog[open] select[name="agreement"]')`, 'the transaction form');
  await click('dialog[open] button[type="submit"]');
  await until(`document.querySelectorAll('dialog[open] .w-invalid').length >= 4`, 'the empty form to be refused');
  await fill('dialog[open] select[name="agreement"]', AGREEMENT);
  await until(`document.querySelectorAll('dialog[open] select[name="payer"] option').length >= 2 && document.querySelectorAll('dialog[open] select[name="allocation"] option').length >= 3`, 'the parties of the agreement');
  await fill('dialog[open] textarea[name="what"]', WHAT);
  await fill('dialog[open] input[name="count"]', '۱۲٫۵');
  await fill('dialog[open] select[name="unit"]', 'TRY');
  await fill('dialog[open] select[name="payer"]', await evaluate(`document.querySelector('dialog[open] select[name="payer"] option').value`));
  await fill('dialog[open] select[name="allocation"]', 'equal');
  await fill('dialog[open] input[name="category"]', 'خانه');
  assert.ok(await evaluate(`document.querySelectorAll('dialog[open] datalist option').length >= 10`), 'no category suggestions');
  await fill('dialog[open] input[name="count"]', '12.555');
  await click('dialog[open] button[type="submit"]');
  await until(`document.querySelector('dialog[open] [data-field="count"].w-invalid')`, 'three decimals of a lira to be refused');
  await fill('dialog[open] input[name="count"]', '۱۲٫۵');
  await click('dialog[open] button[type="submit"]');
  await saved('the transaction to be saved');
  await shows(WHAT);

  step('a save the garden refuses: the page is older than a change behind it');
  await click(`[data-action="new-transaction"][data-agreement="${AGREEMENT}"]`);
  await until(`document.querySelector('dialog[open] textarea[name="what"]')`, 'the form');
  await saveBehind(AGREEMENT, 'آزمون پشت صفحه ' + stamp);
  await fill('dialog[open] textarea[name="what"]', 'نباید ذخیره شود ' + stamp);
  await fill('dialog[open] input[name="count"]', '1');
  await fill('dialog[open] select[name="payer"]', await evaluate(`document.querySelector('dialog[open] select[name="payer"] option').value`));
  await fill('dialog[open] select[name="allocation"]', 'equal');
  await click('dialog[open] button[type="submit"]');
  await until(`document.querySelector('dialog[open] .w-dialog-error .w-guided')`, 'the refusal as a guided error', 300000);
  assert.match(await textOf('dialog[open] .w-dialog-error'), /E-[0-9A-Z]{4}-[0-9A-Z]{4}/, 'the refusal has no reference');
  await click('dialog[open] [data-close]');
  await click('[data-action="refresh"]');
  await ready();

  step('a payment corrected');
  await b.page('accounts');
  await shows(WHAT);
  const ref = await evaluate(`document.querySelector('[data-action="new-transaction"][data-agreement="${CORRECT_IN}"]').closest('section').querySelector('[data-action="bk-correct"]').dataset.ref`);
  await click(`[data-action="bk-correct"][data-ref="${ref}"]`);
  await until(`document.querySelector('dialog[open] input[name="what"]')`, 'the correction form', 120000);
  await fill('dialog[open] input[name="what"]', FIXED);
  await click('dialog[open] button[type="submit"]');
  await until(`document.querySelector('dialog[open] [data-field="reason"].w-invalid')`, 'a correction without its reason to be refused');
  await fill('dialog[open] textarea[name="reason"]', 'آزمون: شرح اشتباه بود');
  await click('dialog[open] button[type="submit"]');
  await saved('the correction to be saved');
  await shows(FIXED);

  step('the purchase categorised, then put back among the uncategorised');
  await b.page('categorize');
  await fill('[data-purchase="state"]', 'all');
  await fill('[data-purchase="search"]', FIXED);
  await until(`document.querySelectorAll('#purchase-table [data-action="categorize"]').length === 1`, 'the purchase alone');
  await click('#purchase-table [data-action="categorize"]');
  await until(`document.querySelector('dialog[open] input[name="category"]')`, 'the category form');
  await fill('dialog[open] input[name="category"]', CATEGORY);
  await click('dialog[open] button[type="submit"]');
  await saved('the category to be saved');
  await b.page('categorize');
  await fill('[data-purchase="state"]', 'done');
  await fill('[data-purchase="search"]', CATEGORY);
  await until(`document.getElementById('purchase-table').textContent.includes(${JSON.stringify(CATEGORY)})`, 'the category on the purchase');
  await click('#purchase-table [data-action="categorize"]');
  await until(`document.querySelector('dialog[open] input[name="category"]')`, 'the category form again');
  await fill('dialog[open] input[name="category"]', '');
  await click('dialog[open] button[type="submit"]');
  await saved('the empty category to be saved');
  await b.page('categorize');
  await fill('[data-purchase="state"]', 'pending');
  await fill('[data-purchase="search"]', FIXED);
  await until(`document.querySelectorAll('#purchase-table [data-action="categorize"]').length === 1`, 'the purchase among the uncategorised');

  step('the exchange: a consent turned off and on again, and a round asked for');
  await b.page('exchange');
  const row = await evaluate(`(() => { const x = document.querySelector('[data-action="exchange-consent"][data-on="0"]'); return x && {agreement: x.dataset.agreement, peer: x.dataset.peer}; })()`);
  assert.ok(row, 'no consent that is on');
  await click(`[data-action="exchange-consent"][data-agreement="${row.agreement}"][data-peer="${row.peer}"]`);
  await until(`document.querySelector('dialog[open] .report-note')`, 'the consent form');
  await click('dialog[open] button[type="submit"]');
  await saved('the consent to be taken back');
  await until(`document.querySelector('[data-action="exchange-consent"][data-agreement="${row.agreement}"][data-on="1"]')`, 'the consent off');
  await click(`[data-action="exchange-consent"][data-agreement="${row.agreement}"][data-peer="${row.peer}"]`);
  await until(`document.querySelector('dialog[open] .report-note')`, 'the consent form again');
  await click('dialog[open] button[type="submit"]');
  await saved('the consent to be given again');
  await until(`document.querySelector('[data-action="exchange-consent"][data-agreement="${row.agreement}"][data-on="0"]')`, 'the consent on');
  await click('[data-action="exchange-now"]');
  await until(`document.getElementById('notice').textContent.includes('تبادل و همگام‌سازی آغاز شد')`, 'the round asked for');

  assert.deepEqual(b.exceptions, [], 'a page threw');
  console.log('PASS: accounts — agreements, transaction, refusal, correction, categorising, exchange consent');
} catch (e) {
  console.error('FAIL:', e.message);
  if (b.exceptions.length) console.error('page exceptions:', b.exceptions);
  process.exitCode = 1;
} finally {
  await b.close();
}
