// The agreements: the balance in each currency (never added across currencies), what stands on each agreement (a
// balance, a periodic commitment, an offer, what needs completing), each agreement's transactions with their reversal
// marks, a payment or cost recorded, and a payment corrected. Positive is owed to the gardener, negative owed by them.
import { h, mount } from '/toolbox/safe.js';
import * as money from '/toolbox/money.js';
import * as moment from '/toolbox/moment.js';
import * as text from '/toolbox/text.js';
import * as choice from '/toolbox/choice.js';
import * as number from '/toolbox/number.js';
import { me } from '/toolbox/settings.js';
import { form, collect, showErrors } from '/toolbox/form.js';
import { openDialog } from '/toolbox/dialog.js';
import { table } from '/toolbox/table.js';
import { newRequest } from '/toolbox/api.js';
import { badge } from '../common.js';
import { currencyOptions } from './cases.js';

export const CATEGORIES = ['سوپرمارکت و خوراک', 'رستوران و کافه', 'حمل‌ونقل', 'پوشاک', 'خانه', 'سلامت', 'آموزش', 'تفریح', 'قبض و اشتراک', 'کارمزد و سود', 'سایر'];
// every purchase of the agreements and the card statements, each with where it is kept
export function purchases(d) {
  return [...d.agreements.flatMap(a => Object.entries(a.transactions || {}).map(([id, t]) => ({...t, id, bean: a.id, account: a.title, sources: a.sources?.[id] || {}}))),
    ...(d.statements || []).flatMap(s => Object.entries(s.entries || {}).map(([id, t]) => ({...t, id, bean: s.id, account: s.account, sources: {[s.id]: s.title}})))];
}
// the categories offered: the usual ones, and every one already written
export const categories = d => [...new Set([...CATEGORIES, ...purchases(d).map(t => t.category).filter(Boolean)])];

// AN AGREEMENT SHARED WITH ANOTHER GARDEN IS MORE THAN ONE BEAN: the agreement (made here, or taken from the garden
// that made it) and the ledgers kept under it, one per garden, each holding that garden's payments. The page shows
// each agreement once, its records grouped by the garden they were made in, and offers each agreement once; the garden
// decides which bean a payment recorded here goes into (the garden's books, book.agreements). A garden that reads with no
// such fields shows each bean as its own agreement, as before.
const agreementOf = a => a.agreement || a.id;
export const agreementsOnce = d => d.agreements.filter(a => !a.ledger);
const beansOf = (d, id) => d.agreements.filter(a => agreementOf(a) === id);
const day = v => v ? moment.show(v) : 'نامعلوم';
const partyName = (a, id) => a.parties?.[id] || id;
function txTable(a) {
  const rows = Object.values(a.transactions || {});
  return table({rows, empty: 'تراکنشی ثبت نشده است.', rowClass: t => t.reverses || t.reversedBy ? 'muted' : '', columns: [
    {title: 'شرح', cell: t => h`${text.show(t.what)}${t.reverses ? h` ${badge('سند معکوس', 'late')}` : t.reversedBy ? h` ${badge('برگشت‌خورده', 'late')}` : ''}${t.category ? h`<small>${text.show(t.category)}</small>` : ''}`},
    {title: 'روز', cell: t => day(t.day), sort: t => t.day || ''},
    {title: 'مبلغ', align: 'num', cell: t => t.amount?.count ? money.show(t.amount.count, t.amount.unit) : '—'},
    {title: 'پرداخت‌کننده', cell: t => (t.paid_by || []).map(p => partyName(a, p.party)).join('، ')},
    {title: 'سهم‌ها', cell: t => (t.borne_by || []).map(p => partyName(a, p.party) + ' ' + (number.plain(p.share) ?? p.share)).join('، ')},
    {title: '', cell: t => a.takenFrom ? h`<small>اصلاح در ${text.show(a.takenFromName || a.takenFrom)}</small>`
      : t.ref && !t.reverses && !t.reversedBy ? h`<button class="text-button" data-action="bk-correct" data-ref="${t.ref}">اصلاح</button>` : ''},
  ]});
}

// the transaction form: its payer and allocation follow the agreement chosen
const parties = (d, id) => Object.entries(d.agreements.find(a => a.id === id)?.parties || {}).map(([value, label]) => ({value, label}));
const allocations = (d, id) => [{value: 'equal', label: 'هزینهٔ مشترک با سهم برابر'}, ...parties(d, id).map(p => ({value: p.value, label: 'تمام مبلغ برای ' + p.label}))];
function txFields(d, agreement) {
  return [
    {name: 'agreement', label: 'توافق', type: 'choice', required: true, none: 'انتخاب کنید', options: agreementsOnce(d).map(a => ({value: a.id, label: a.title})), wide: true},
    {name: 'what', label: 'شرح پرداخت یا هزینه', type: 'lines', required: true},
    {name: 'day', label: 'تاریخ واقعی پرداخت', type: 'date'},
    {name: 'count', label: 'مبلغ کل', type: 'number', required: true},
    {name: 'unit', label: 'واحد ارز', type: 'choice', required: true, options: currencyOptions(d)},
    {name: 'payer', label: 'چه کسی پرداخت کرده؟', type: 'choice', required: true, options: parties(d, agreement)},
    {name: 'allocation', label: 'مبلغ به حساب چه کسی است؟', type: 'choice', required: true, options: allocations(d, agreement)},
    {name: 'category', label: 'دسته‌بندی', suggest: categories(d), max: 120, placeholder: 'انتخاب از فهرست یا نوشتن دستهٔ دلخواه'},
    {name: 'note', label: 'توضیح', type: 'lines'},
  ];
}
export function openTransaction(ctx, agreement = '') {
  if (ctx.stale) throw new Error('اطلاعات قدیمی است؛ ابتدا «به‌روزرسانی» را بزنید.');
  const d = ctx.data, head = d.head, request = newRequest();
  let fields = txFields(d, agreement);
  const dlg = openDialog({title: 'ثبت پرداخت یا هزینه', wide: true,
    body: h`${form(fields, {agreement, unit: 'TRY'})}<p class="wide report-note">مبلغ کل تراکنش را وارد کنید. برای بازپرداخت، پرداخت‌کننده کسی است که وجه را می‌دهد و «تمام مبلغ برای» دریافت‌کننده است. پیشنهاد شهریه و بدهیِ پرداخت‌نشده را اینجا ثبت نکنید.</p>`,
    onSubmit: async f => {
      const {values: v, errors} = collect(f, fields);
      if (v.unit && !errors.count) { const m = money.take(f.elements.count.value, v.unit, {required: true, positive: true}); if (m.error) errors.count = m.error; else v.count = m.value; }
      if (!showErrors(f, errors)) return false;
      const bean = v.agreement;
      delete v.agreement;
      await ctx.save('transaction', bean, v, {head, request});
      return true;
    }});
  // a required choice offers no empty row: what the person has not chosen yet is shown unchosen, and refused if left so
  const unchoose = (...names) => { for (const n of names) { const s = dlg.querySelector(`select[name="${n}"]`); if (s) s.selectedIndex = -1; } };
  unchoose(...(agreement ? [] : ['agreement']), 'payer', 'allocation');
  dlg.querySelector('select[name="agreement"]').addEventListener('change', e => {
    fields = txFields(d, e.target.value);
    for (const n of ['payer', 'allocation']) {
      const f = fields.find(x => x.name === n);
      mount(dlg.querySelector(`[data-field="${n}"]`), h`<span class="w-label">${f.label} *</span>${choice.edit(n, '', f.options, {required: true})}<small class="w-field-error" hidden></small>`);
    }
    unchoose('payer', 'allocation');
  });
}

export const actions = {
  'new-transaction': (el, ctx) => openTransaction(ctx, el.dataset.agreement || ''),
};

export default {
  id: 'accounts', nav: 'توافق‌ها', title: 'حساب‌ها', actions,
  headerActions: () => h`<button class="secondary" data-nav="categorize">دسته‌بندی خریدها</button>`,
  render(ctx) {
    const d = ctx.data, acc = d.accounting || {totals: {}, rows: []};
    const totals = Object.entries(acc.totals || {});
    return h`<section class="panel"><div class="panel-head"><div><h2>ماندهٔ حساب‌ها</h2><p>مثبت: طلب ${me()} · منفی: بدهی ${me()} · ارزهای مختلف با هم جمع نمی‌شوند.</p></div>
        <button class="primary" data-action="new-transaction">＋ ثبت پرداخت یا هزینه</button></div>
      <div class="stats">${totals.map(([u, n]) => h`<div class="stat"><span>${u}</span><b class="amount">${money.show(n, u, {label: 'none'})}</b><small>ماندهٔ همهٔ سوابق${money.uneven(n, u) ? h` — ${money.UNEVEN}` : ''}</small></div>`)}</div>
      ${table({rows: acc.rows || [], empty: 'سابقه‌ای ثبت نشده است.', columns: [
        {title: 'شرح', cell: r => text.show(r.title)},
        {title: 'نوع', cell: r => badge(r.kind, r.kind === 'نیازمند تکمیل' ? 'late' : '')},
        {title: 'مبلغ', align: 'num', cell: r => r.amount === null || r.amount === undefined ? '—' : money.show(r.amount, r.currency)},
        {title: 'توضیح', cell: r => text.show(r.note, {empty: ''})},
      ]})}</section>
      ${agreementsOnce(d).map(a => { const beans = beansOf(d, a.id); return h`<section class="panel"><div class="panel-head"><h2>${text.show(a.title)}</h2><button class="secondary" data-action="new-transaction" data-agreement="${a.id}">ثبت تراکنش</button></div>
        ${beans.length === 1 ? txTable(a) : beans.map(b => h`<div class="detail-section"><h3>${b.takenFrom ? h`ثبت‌های ${text.show(b.takenFromName || b.takenFrom)}` : 'ثبت‌های این دفتر'}${b.ledger ? '' : h` <small>(خود توافق)</small>`}</h3>${txTable(b)}</div>`)}</section>`; })}`;
  },
};
