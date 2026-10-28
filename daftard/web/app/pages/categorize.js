// Categorising purchases, one at a time: every purchase of the agreements and the card statements, filtered by account,
// statement, month (in the reader's calendar), whether it has a category, and words; each category saved on its own.
// A category left empty puts the purchase back among the uncategorised.
import { h, mount } from '/toolbox/safe.js';
import * as money from '/toolbox/money.js';
import * as moment from '/toolbox/moment.js';
import * as text from '/toolbox/text.js';
import * as number from '/toolbox/number.js';
import { settings } from '/toolbox/settings.js';
import { form, collect, showErrors } from '/toolbox/form.js';
import { openDialog } from '/toolbox/dialog.js';
import { table } from '/toolbox/table.js';
import { newRequest } from '/toolbox/api.js';
import { badge, fact } from '../common.js';
import { purchases, categories } from './accounts.js';

const filters = {account: '', statement: '', month: '', search: '', state: 'pending'};
const KINDS = {purchase: 'خرید / قسط', refund: 'برگشت وجه', payment: 'واریز به کارت', discount: 'تخفیف بانکی', fee: 'کارمزد و سود'};
const notPurchase = t => ['payment', 'discount'].includes(t.kind);
const needsCategory = t => !notPurchase(t) && !String(t.category || '').trim();
const hasCategory = t => Boolean(String(t.category || '').trim());
// a day's month in the reader's calendar, and its name
const monthOf = day => { if (!day) return ''; if (settings.calendar !== 'persian') return day.slice(0, 7); const p = moment.toPersian(day); return `${p.y}-${String(p.m).padStart(2, '0')}`; };
function monthLabel(key) {
  const [y, m] = key.split('-').map(Number);
  const day = settings.calendar === 'persian' ? moment.fromPersian(y, m, 1) : `${key}-01`;
  return new Intl.DateTimeFormat(`${settings.lang}-u-ca-${settings.calendar}`, {month: 'long', year: 'numeric', timeZone: 'UTC'}).format(new Date(day + 'T12:00:00Z'));
}
const accounts = d => [...d.agreements.map(a => ({value: a.id, label: a.title})), ...(d.statements || []).map(s => ({value: s.id, label: s.account + ' — ' + s.title}))];
function scope(d) {
  const f = filters, words = f.search.toLocaleLowerCase();
  return purchases(d).filter(t => (!f.account || t.bean === f.account) && (!f.statement || Object.hasOwn(t.sources, f.statement))
    && (!f.month || monthOf(t.day) === f.month) && (!words || [t.what, t.category, t.note, t.account].some(v => String(v || '').toLocaleLowerCase().includes(words))));
}
function purchaseTable(d) {
  const all = scope(d), pending = all.filter(needsCategory).length;
  const rows = all.filter(t => filters.state === 'all' || (filters.state === 'pending' ? needsCategory(t) : hasCategory(t)));
  const empty = !purchases(d).length ? 'هنوز خریدی وارد نشده است. پس از ورود صورت‌حساب، موارد اینجا نمایش داده می‌شوند.'
    : filters.state === 'pending' ? 'در این فیلتر خرید بدون دسته‌بندی ندارید.' : 'خریدی با این فیلتر پیدا نشد.';
  return h`<p role="status">${number.plain(String(pending))} مورد بدون دسته‌بندی از ${number.plain(String(all.length))} خرید در این فیلتر</p>${table({rows, empty, columns: [
    {title: 'تاریخ', cell: t => t.day ? moment.show(t.day) : 'نامعلوم', sort: t => t.day || ''},
    {title: 'شرح خرید', cell: t => h`${text.show(t.what)}${t.kind ? h`<small>${KINDS[t.kind] || t.kind}</small>` : ''}${t.note ? h`<small>${text.show(t.note)}</small>` : ''}`},
    {title: 'حساب / صورت‌حساب', cell: t => h`${text.show(t.account)}<small>${Object.values(t.sources).join('، ')}</small>`},
    {title: 'مبلغ', align: 'num', cell: t => h`${t.amount?.count ? money.show(t.amount.count, t.amount.unit) : '—'}${t.charged ? h`<small>مبلغ برداشت: ${money.show(t.charged.count, t.charged.unit)}</small>` : ''}`},
    {title: 'دسته‌بندی', cell: t => notPurchase(t) ? 'خرید نیست' : hasCategory(t) ? h`${text.show(t.category)}${t.category_inferred ? h` ${badge('پیشنهادی')}` : ''}` : badge('بدون دسته‌بندی', 'late')},
    {title: 'بررسی', cell: t => notPurchase(t) ? '—' : h`<button class="secondary" data-action="categorize" data-bean="${t.bean}" data-entry="${t.id}">${hasCategory(t) ? 'اصلاح دسته' : 'تعیین دسته'}</button>`},
  ]})}`;
}
function statementSummary(d) {
  const shown = (d.statements || []).filter(s => (!filters.statement || s.id === filters.statement) && (!filters.account || s.id === filters.account));
  return h`${shown.map(s => h`<div class="report-note"><b>${text.show(s.title)}</b><div class="facts">
    ${fact('بدهی اعلام‌شدهٔ بانک', s.closing_debt ? money.show(s.closing_debt.count, s.closing_debt.unit) : null)}${fact('حداقل پرداخت اعلام‌شده', s.minimum_payment ? money.show(s.minimum_payment.count, s.minimum_payment.unit) : null)}
    ${fact('سررسید', s.due_on ? moment.show(s.due_on) : null)}${fact('تطبیق ردیف‌ها با مانده', s.reconciliation?.matches ? 'تطبیق کامل' : 'نیازمند بررسی')}</div>
    <small>ارقام مربوط به همین صورت‌حساب‌اند. منفی در ردیف‌ها یعنی بستانکاری کارت. دسته‌های «پیشنهادی» بر اساس نام پذیرنده‌اند و قابل اصلاح هستند. ردیف‌های این سند به حساب مشترک افراد اضافه نشده‌اند.</small></div>`)}`;
}
function remount(ctx) {
  const d = ctx.data;
  mount(document.getElementById('purchase-table'), purchaseTable(d));
  mount(document.getElementById('statement-summary'), statementSummary(d));
}

function openCategory(ctx, bean, entry) {
  const d = ctx.data, row = purchases(d).find(t => t.bean === bean && t.id === entry);
  if (!row) return;
  const head = d.head, request = newRequest();
  const fields = [{name: 'category', label: 'دسته‌بندی خرید', suggest: categories(d), max: 120, placeholder: 'انتخاب از فهرست یا نوشتن دستهٔ دلخواه', wide: true}];
  openDialog({title: 'دسته‌بندی خرید',
    body: h`<div class="wide facts">${fact('شرح خرید', row.what)}${fact('تاریخ', row.day ? moment.show(row.day) : null)}${fact('مبلغ', row.amount?.count ? money.show(row.amount.count, row.amount.unit) : null)}${fact('حساب', row.account)}</div>
      ${form(fields, {category: row.category || ''})}<p class="wide muted">خالی گذاشتن دسته، خرید را دوباره به فهرست بدون دسته‌بندی برمی‌گرداند.</p>`,
    onSubmit: async f => {
      const {values, errors} = collect(f, fields);
      if (!showErrors(f, errors)) return false;
      await ctx.save('categorize', bean, {entry, category: values.category}, {head, request});
      return true;
    }});
}

export const actions = {categorize: (el, ctx) => openCategory(ctx, el.dataset.bean, el.dataset.entry)};

export default {
  id: 'categorize', title: 'دسته‌بندی خریدها', actions,
  headerActions: () => h`<button class="secondary" data-nav="accounts">← توافق‌ها</button>`,
  render(ctx) {
    const d = ctx.data, all = purchases(d);
    const sources = Object.assign({}, ...all.map(t => t.sources));
    const months = [...new Set(all.map(t => monthOf(t.day)).filter(Boolean))].sort().reverse();
    const opt = (v, label, cur) => h`<option value="${v}"${v === cur ? h` selected` : ''}>${label}</option>`;
    return h`<section class="panel"><div class="panel-head"><div><h2>خریدها را یکی‌یکی بررسی کن</h2><p>دسته را از فهرست انتخاب کن یا نام دلخواهت را بنویس. هر انتخاب جداگانه ذخیره می‌شود.</p></div></div>
      <div id="statement-summary">${statementSummary(d)}</div>
      ${Object.keys(sources).length ? '' : h`<p class="report-note">هنوز صورت‌حساب کارتی وارد نشده است. پس از فرستادن فایل و ورود آن به دفتر، خریدهایش در همین بخش قابل دسته‌بندی‌اند. ردیف‌های فعلی مربوط به حساب‌های موجود هستند.</p>`}
      <div class="filters">
        <select data-purchase="account" aria-label="حساب خرید">${opt('', 'همهٔ حساب‌ها', filters.account)}${accounts(d).map(a => opt(a.value, a.label, filters.account))}</select>
        <select data-purchase="statement" aria-label="صورت‌حساب">${opt('', 'همهٔ صورت‌حساب‌ها', filters.statement)}${Object.entries(sources).map(([id, title]) => opt(id, title, filters.statement))}</select>
        <select data-purchase="month" aria-label="ماه انجام خرید">${opt('', 'همهٔ ماه‌ها', filters.month)}${months.map(m => opt(m, monthLabel(m), filters.month))}</select>
        <select data-purchase="state" aria-label="وضعیت دسته‌بندی">${[['pending', 'بدون دسته‌بندی'], ['done', 'دسته‌بندی‌شده'], ['all', 'همهٔ خریدها']].map(([v, l]) => opt(v, l, filters.state))}</select>
        <input type="search" data-purchase="search" aria-label="جستجوی خرید" placeholder="جستجوی شرح خرید یا دسته…" value="${filters.search}"></div>
      <p class="muted">برای مرور کل دوره، صورت‌حساب را انتخاب کن؛ فیلتر ماه بر اساس تاریخ انجام خرید است.</p>
      <div id="purchase-table">${purchaseTable(d)}</div></section>`;
  },
  input(e, ctx) {
    const key = e.target.dataset?.purchase;
    if (!key || !Object.hasOwn(filters, key)) return;
    filters[key] = e.target.value;
    remount(ctx);
  },
};
