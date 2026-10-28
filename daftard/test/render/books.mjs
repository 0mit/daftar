// books — the four books pages clicked through in headless Chromium: every view, and every form saved once, on a
// SCRATCH copy of a garden (it writes: postings, a correction, a dispute, a reversal, a manual voucher corrected and
// deleted, a chart row added and renamed), and a refusal shown as a guided error. Fails on any page exception.
//
//   DAFTAR_URL=http://127.0.0.1:8791 DAFTAR_KEY=<key> DAFTAR_GARDEN=<garden> node test/render/books.mjs
import assert from 'node:assert/strict';
import { browser } from './cdp.mjs';

const BASE = process.env.DAFTAR_URL, KEY = process.env.DAFTAR_KEY, GARDEN = process.env.DAFTAR_GARDEN;
if (!BASE || !KEY || !GARDEN) { console.error('DAFTAR_URL, DAFTAR_KEY and DAFTAR_GARDEN are needed'); process.exit(2); }
const b = await browser({base: BASE, key: KEY});
const {evaluate, until, click, fill, textOf} = b;
const step = name => console.log('·', name);
const count = sel => evaluate(`document.querySelectorAll(${JSON.stringify(sel)}).length`);
// the first choice a select offers that can be taken
const firstOption = sel => evaluate(`[...document.querySelector(${JSON.stringify(sel)}).options].find(o => o.value && !o.disabled)?.value || ''`);
const dialog = what => until(`document.querySelector('dialog[open] form')`, what);
// submit the open dialog: saved (it closes and the page is read again) or refused (a guided error in it)
async function submit(expect = 'saved') {
  await click('dialog[open] button[type="submit"]');
  const got = await until(`!document.querySelector('dialog[open]') ? 'saved' : document.querySelector('dialog[open] .w-dialog-error .w-guided, dialog[open] .w-invalid, dialog[open] .jl-error:not(:empty)') ? 'refused' : ''`, 'the save', 300000);
  if (got !== expect) throw new Error(`expected ${expect}, got ${got}: ` + await textOf('dialog[open] .w-dialog-error') + await textOf('dialog[open] .w-invalid'));
  if (got === 'saved') await b.ready();
  return got;
}

try {
  step('posting: a card line to its account');
  await b.page('posting');
  const before = await count('[data-action="bk-post-one"]');
  await click('[data-action="bk-post-one"]');
  await dialog('the posting form');
  if (!await evaluate(`document.querySelector('dialog[open] [name="account"]').value`)) await fill('dialog[open] [name="account"]', await firstOption('dialog[open] [name="account"]'));
  await fill('dialog[open] [name="note"]', 'آزمون ثبت ردیف');
  await submit();
  assert.ok(await count('[data-action="bk-post-one"]') < before, 'the posted line still waits among the unposted');

  step('posting: lines chosen together, each with its suggested account');
  const suggested = await evaluate(`[...document.querySelectorAll('#posting-lines tbody tr')].filter(tr => tr.textContent.includes('پیشنهاد')).slice(0, 2).map(tr => tr.querySelector('[data-line]').dataset.line)`);
  for (const k of suggested) { await click(`[data-line="${k}"]`); await b.sleep(100); }
  assert.match(await textOf('.batch'), /۲ ردیف انتخاب شده/);
  await click('[data-action="bk-accept-suggested"]');
  await dialog('the suggested posting');
  assert.match(await textOf('dialog[open]'), /حساب پیشنهادی خودش/);
  await submit();
  await click('[data-action="bk-clear-selection"]').catch(() => {});

  step('posting: a line shared in an agreement, with its shares');
  await click('[data-action="bk-post-one"]');
  await dialog('the posting form');
  if (!await evaluate(`document.querySelector('dialog[open] [name="account"]').value`)) await fill('dialog[open] [name="account"]', await firstOption('dialog[open] [name="account"]'));
  await fill('dialog[open] [name="contract"]', await firstOption('dialog[open] [name="contract"]'));
  await until(`document.querySelector('dialog[open] [name^="share:"]')`, 'the shares');
  await fill('dialog[open] [name^="share:"]', 'x');
  await submit('refused');                                   // a share that is no number is said at its field
  await fill('dialog[open] [name^="share:"]', '۲');
  await submit();

  step('posting: a payment given its account');
  await click('[data-action="bk-post-pay"]');
  await dialog('the payment form');
  if (!await evaluate(`document.querySelector('dialog[open] [name="account"]').value`)) await fill('dialog[open] [name="account"]', await firstOption('dialog[open] [name="account"]'));
  await submit();

  step('posting: a payment corrected');
  // one with no account yet (correcting one just given its account is refused by the garden's model: see the report)
  await evaluate(`[...document.querySelectorAll('[data-action="bk-correct"]')].find(x => x.closest('tr').textContent.includes('بدون حساب')).dataset.pick = '1'`);
  await click('[data-action="bk-correct"][data-pick="1"]');
  await dialog('the correction');
  await fill('dialog[open] [name="what"]', 'شرح اصلاح‌شده در آزمون');
  await submit('refused');                                   // no reason: refused at its field
  await fill('dialog[open] [name="reason"]', 'آزمون اصلاح');
  await submit();

  step('vouchers: open one, its history, a dispute and a reversal');
  await b.page('vouchers');
  const pay = await evaluate(`[...document.querySelectorAll('.voucher-head')].find(x => x.textContent.includes('پرداخت') && !x.closest('.reversed'))?.dataset.ref`);
  assert.ok(pay, 'no payment voucher');
  await click(`.voucher-head[data-ref="${pay}"]`);
  await until(`document.querySelector('.voucher-body')`, 'the voucher body');
  await click(`.voucher-body [data-action="bk-history"]`);
  await until(`document.querySelector('.history')`, 'the history');
  await click(`.voucher-body [data-action="bk-dispute"]`);
  await dialog('the dispute');
  await fill('dialog[open] [name="reason"]', 'آزمون اعتراض');
  await submit();
  await b.page('vouchers');
  await click(`.voucher-head[data-ref="${pay}"]`);
  await until(`document.querySelector('.voucher-body [data-action="bk-reverse"]')`, 'the reverse button');
  await click(`.voucher-body [data-action="bk-reverse"]`);
  await dialog('the reversal');
  await fill('dialog[open] [name="reason"]', 'آزمون برگشت');
  await submit();

  step('vouchers: a manual voucher — unbalanced refused, then saved, corrected and deleted');
  await b.page('vouchers');
  const vouchersBefore = await count('.voucher');
  await click('[data-action="bk-journal"]');
  await dialog('the manual voucher');
  await fill('dialog[open] [name="memo"]', 'سند آزمون');
  const acct = await firstOption('dialog[open] tr[data-jl="0"] [name="jl-account"]');
  await fill('dialog[open] tr[data-jl="0"] [name="jl-account"]', acct);
  await fill('dialog[open] tr[data-jl="1"] [name="jl-account"]', acct);
  await fill('dialog[open] tr[data-jl="0"] [name="jl-debit"]', '۱۰۰٫۵۰');
  await fill('dialog[open] tr[data-jl="1"] [name="jl-credit"]', '1.234');   // three places in a two-place currency
  await submit('refused');
  await fill('dialog[open] tr[data-jl="1"] [name="jl-credit"]', '100.50');
  await until(`document.querySelector('dialog[open] .jl-totals').textContent.includes('تراز') && !document.querySelector('dialog[open] .jl-totals').textContent.includes('نیست')`, 'the voucher to balance');
  await click('dialog[open] [data-jl-add]');
  assert.equal(await count('dialog[open] tr[data-jl]'), 3);
  await click('dialog[open] [data-jl-remove="2"]');
  assert.equal(await count('dialog[open] tr[data-jl]'), 2);
  await submit();
  assert.equal(await count('.voucher'), vouchersBefore + 1);
  const mine = await evaluate(`[...document.querySelectorAll('.voucher-head')].find(x => x.textContent.includes('سند آزمون'))?.dataset.ref`);
  await click(`.voucher-head[data-ref="${mine}"]`);
  await until(`document.querySelector('.voucher-body')`, 'its body');
  await click(`.voucher-body [data-action="bk-correct"]`);
  await dialog('the correction of a manual voucher');
  assert.equal(await count('dialog[open] tr[data-jl]'), 2);
  await fill('dialog[open] [name="memo"]', 'سند آزمون اصلاح‌شده');
  await fill('dialog[open] [name="reason"]', 'آزمون اصلاح سند');
  await submit();
  await b.page('vouchers');
  const fixed = await evaluate(`[...document.querySelectorAll('.voucher-head')].find(x => x.textContent.includes('سند آزمون اصلاح‌شده'))?.dataset.ref`);
  assert.ok(fixed, 'the corrected voucher is not listed');
  await click(`.voucher-head[data-ref="${fixed}"]`);
  await until(`document.querySelector('.voucher-body')`, 'its body');
  await click(`.voucher-body [data-action="bk-delete"]`);
  await dialog('the deletion');
  await fill('dialog[open] [name="reason"]', 'آزمون حذف');
  await submit();
  assert.ok(!(await textOf('#voucher-list')).includes('سند آزمون اصلاح‌شده'), 'the deleted voucher is still listed');

  step('vouchers: the filters');
  await fill('[data-vf="search"]', 'zzzz-no-such');
  await until(`document.querySelector('#voucher-list .empty')`, 'nothing to match');
  await fill('[data-vf="search"]', '');

  step('chart: an account added, then renamed; a code taken twice refused');
  await b.page('chart');
  const parent = await evaluate(`[...document.querySelectorAll('[data-action="bk-chart-add"]')].find(x => x.dataset.parent && x.closest('tr').classList.contains('level-general'))?.dataset.parent`);
  await click(`[data-action="bk-chart-add"][data-parent="${parent}"]`);
  await dialog('the new account');
  await fill('dialog[open] [name="code"]', parent + '97');
  await fill('dialog[open] [name="name"]', 'حساب آزمون');
  await submit();
  assert.match(await textOf('#content'), /حساب آزمون/);
  await click(`[data-action="bk-chart-edit"][data-code="${parent}97"]`);
  await dialog('the account edited');
  await fill('dialog[open] [name="name"]', 'حساب آزمون تازه');
  await submit();
  assert.match(await textOf('#content'), /حساب آزمون تازه/);
  await click(`[data-action="bk-chart-add"][data-parent="${parent}"]`);
  await dialog('another new account');
  await fill('dialog[open] [name="code"]', parent + '97');
  await fill('dialog[open] [name="name"]', 'تکراری');
  await submit('refused');
  assert.ok(await count('dialog[open] .w-guided'), 'the refusal is not a guided error');
  await click('dialog[open] [data-close]');
  for (const s of ['analytic', 'details']) {
    await click(`[data-action="bk-scheme"][data-scheme="${s}"]`);
    await b.ready();
  }
  assert.match(await textOf('#content'), /اشخاص — حساب‌های تفصیلی/);

  step('finance: each report, a ledger from the trial, a person\'s ledger from the chart');
  await b.page('finance');
  for (const r of ['trial', 'ledger', 'people', 'analytic', 'card', 'checks']) {
    await click(`[data-action="bk-report"][data-report="${r}"]`);
    await until(`document.querySelector('[data-report="${r}"][aria-selected="true"]')`, r);
  }
  await click('[data-action="bk-report"][data-report="trial"]');
  await until(`document.querySelector('[data-action="bk-ledger"]')`, 'the trial');
  await click('[data-action="bk-ledger"]');
  await until(`document.querySelector('[name="lg-code"]')`, 'the ledger');
  await b.page('chart');
  await click('[data-action="bk-scheme"][data-scheme="details"]');
  await until(`document.querySelector('[data-action="bk-person-ledger"]')`, 'the persons');
  await click('[data-action="bk-person-ledger"]');
  // the finance report is a part of the books' page now (pages/seven.js): the chart's link opens that part
  await until(`document.querySelector('section[data-part="finance"] [name="lg-person"]')?.value`, 'the person\'s ledger');

  step('finance: a period applied, and a wrong day refused');
  await click('[data-action="bk-report"][data-report="trial"]');
  await until(`document.querySelector('[name="period-from"]')`, 'the period bar');
  await fill('[name="period-from"]', '۱۴۰۵/۰۷/۰۱');
  await click('[data-action="bk-period"]');
  await until(`document.querySelector('.print-heading')?.textContent.includes('۱۴۰۵')`, 'the period applied');
  await fill('[name="period-from"]', '۱۴۰۵/۱۳/۰۱');
  await click('[data-action="bk-period"]');
  await until(`document.getElementById('notice').textContent.trim()`, 'the wrong day said');
  await click('[data-action="bk-period-clear"]');

  assert.deepEqual(b.exceptions, [], 'a page threw');
  console.log('PASS: books — posting, vouchers, finance, chart: every form saved once, refusals shown');
} catch (e) {
  console.error('FAIL:', e.message);
  if (b.exceptions.length) console.error('page exceptions:', b.exceptions);
  process.exitCode = 1;
} finally {
  await b.close();
}
