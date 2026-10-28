// The gardener's books (accounting/book.py, read through /api/books): what the four books pages share. That covers
// the period they read, the names of accounts, centres, persons and beans, and every form that changes the books:
// - posting card lines and payments;
// - correcting, deleting, disputing and reversing a voucher;
// - a manual voucher;
// - a row of the chart.
// Every amount is shown by the money widget exactly as the books send it (n/d where it does not end in the
// currency's places) and summed exactly (toolbox/exact.js). Everything typed goes through its widget's take, so what
// is saved is the value's written form. The save kinds and their values are the garden model's (dashboard/model.py
// FORMS), unchanged.
import { h, mount } from '/toolbox/safe.js';
import * as money from '/toolbox/money.js';
import * as number from '/toolbox/number.js';
import * as moment from '/toolbox/moment.js';
import * as text from '/toolbox/text.js';
import * as choice from '/toolbox/choice.js';
import * as exact from '/toolbox/exact.js';
import * as api from '/toolbox/api.js';
import { form, collect, showErrors } from '/toolbox/form.js';
import { openDialog } from '/toolbox/dialog.js';
import { me, gardenerId } from '/toolbox/settings.js';
import { badge, fact, count } from './common.js';

// what the books pages remember while the handplace is open
export const state = {
  period: {from: '', to: '', unit: 'TRY'},
  posting: {statement: '', state: 'unposted', month: '', kind: '', search: ''},
  selected: new Set(),                 // card lines chosen for posting together: "<statement>|<line>"
  showReversed: false,
  vouchers: {search: '', kind: '', account: ''},
  open: new Set(),                     // vouchers shown whole
  focus: '',                           // a voucher another page sent the reader to
  histories: {},                       // ref → {history, whose, shown}
  report: 'trial',
  ledger: {code: '1301', person: ''},
  scheme: 'account',
};
export const KINDS = {purchase: 'خرید / قسط', refund: 'برگشت وجه', payment: 'واریز به کارت', discount: 'تخفیف بانکی', fee: 'کارمزد و سود'};
export const VOUCHER_KINDS = {pay: 'پرداخت', journal: 'سند دستی', reversal: 'سند معکوس'};
export const LEVELS = {group: 'گروه', general: 'کل', subsidiary: 'معین', plan: 'طرح', account: 'حساب تحلیلی'};
export const TYPES = {asset: 'دارایی', liability: 'بدهی', equity: 'سرمایه', income: 'درآمد', expense: 'هزینه'};
const SAVE_NOTE = 'ذخیره از دروازهٔ دفتر می‌گذرد؛ اگر همین پرونده در همین دقیقه ذخیره شده باشد، تا یک دقیقه طول می‌کشد.';

// THE BOOKS AS LAST READ, for the period chosen: pages render from it, forms opened from them read it
let B = null;
export const books = () => B;
export function query() {
  const q = new URLSearchParams({unit: state.period.unit});
  if (state.period.from) q.set('from', state.period.from);
  if (state.period.to) q.set('to', state.period.to);
  return q.toString();
}
export async function load(ctx) { B = await ctx.books(query()); return B; }

// names
export const account = code => B?.chart.accounts.find(a => a.code === code);
export const accountLabel = code => { const a = account(code); return a ? `${code} — ${a.name}` : code || '—'; };
export const centreLabel = code => B?.chart.analytic.find(a => a.code === code)?.name || code;
export const person = id => B?.persons.find(p => p.id === id)?.title || (id === 'unknown' ? 'نامعلوم' : id);
export const beanTitle = id => B?.beans.find(b => b.id === id)?.title || id;
// the agreement a payment is under: its bean, or the agreement its ledger is kept under (the garden's book.agreements);
// what the forms offer and pre-select, one per agreement, while the garden decides the bean a payment is written into
export const agreementOf = p => p?.agreement || p?.contract || '';
// an amount as the books send it, at its currency's places, with its code (or bare, in a table whose unit is said once)
export const amount = (v, unit, o = {}) => v === null || v === undefined || v === '' ? h`<span class="w-none">—</span>` : money.show(v, unit, o);
export const bare = (v, unit) => amount(v, unit, {label: 'none'});
export const day = d => d ? moment.show(d) : 'نامعلوم';
export const owes = v => { const s = exact.sign(exact.of(v) || exact.ZERO); return s > 0 ? 'به ' + me() + ' بدهکار است' : s < 0 ? me() + ' به او بدهکار است' : 'تسویه'; };
// the reader's month (Persian calendar) of a day, and its name
export const monthOf = d => { const p = moment.toPersian(String(d).slice(0, 10)); return p ? `${p.y}-${String(p.m).padStart(2, '0')}` : ''; };
export const monthName = key => { const [y, m] = key.split('-').map(Number); const d = moment.fromPersian(y, m, 1);
  return d ? new Intl.DateTimeFormat('fa-IR-u-ca-persian', {month: 'long', year: 'numeric', timeZone: 'UTC'}).format(new Date(d + 'T12:00:00Z')) : key; };

// choices
export const accountRows = ({postableOnly = true, value = ''} = {}) => B.chart.accounts
  .filter(a => !postableOnly || (a.postable && a.active) || a.code === value)
  .map(a => ({value: a.code, label: ' '.repeat((a.path.length - 1) * 3) + a.code + ' — ' + a.name, disabled: !a.postable}));
export const centreRows = value => B.chart.analytic.filter(a => a.postable && (a.active || a.code === value)).map(a => ({value: a.code, label: a.name}));
const currencyRows = ctx => (ctx.data.currencies || []).map(c => ({value: c.code, label: c.code}));
const knownPersons = () => B.persons.filter(p => p.known).map(p => ({value: p.id, label: p.title}));

// THE PERIOD the books are read for, in the reader's calendar, and the currency
export function periodBar() {
  const p = state.period;
  return h`<div class="filters books-period"><label class="w-field"><span class="w-label">از</span>${moment.edit('period-from', p.from, {placeholder: 'آغاز'})}</label>
    <label class="w-field"><span class="w-label">تا</span>${moment.edit('period-to', p.to, {placeholder: 'امروز'})}</label>
    <label class="w-field"><span class="w-label">ارز</span>${choice.edit('period-unit', p.unit, B.units.map(u => ({value: u, label: u})), {required: true})}</label>
    <button class="secondary" data-action="bk-period">اعمال بازه</button>${p.from || p.to ? h`<button class="text-button" data-action="bk-period-clear">همهٔ دوره‌ها</button>` : ''}</div>`;
}

// what a posting says, in a line: accounts, centres, shares, the agreement and the voucher
export function postingSummary(p) {
  if (!p) return '';
  const shares = Object.entries(p.bears || {});
  return h`<small>${p.accounts.map(accountLabel).join('، ')}${p.analytic.length ? ' · ' + p.analytic.map(centreLabel).join('، ') : ''}${shares.length ? h` · سهم: ${shares.map(([w, s]) => h`${person(w)} ${number.show(s)}`).map((x, i) => i ? h`، ${x}` : x)}` : ''}${agreementOf(p) ? ' · ' + beanTitle(agreementOf(p)) : ''} · سند ${count(p.number)}</small>`;
}

// ---------------------------------------------------------------------------------------------- one form of the books
// The dialog, its fields' errors, the head it was opened at and its request id (a retry never saves twice). `read(f)`
// returns the values to save, or null when a field's error is shown; `wire(f)` binds what changes inside the form.
function bookForm(ctx, {kind, bean, title, note = SAVE_NOTE, body, read, wire, wide = false}) {
  if (ctx.stale) throw new Error('اطلاعات قدیمی است؛ ابتدا «به‌روزرسانی» را بزنید.');
  const head = ctx.data.head, request = api.newRequest();
  const d = openDialog({title, note, body, wide, onSubmit: async f => {
    const values = read(f);
    if (!values) return false;
    await ctx.save(kind, bean, values, {head, request});
    return true;
  }});
  if (wire) wire(d.querySelector('form'));
}
const field = (name, label, control, {wide = false, hint = '', required = false} = {}) =>
  h`<label class="w-field${wide ? ' wide' : ''}" data-field="${name}"><span class="w-label">${label}${required ? ' *' : ''}</span>${control}${hint ? h`<small class="w-hint">${hint}</small>` : ''}<small class="w-field-error" hidden></small></label>`;
const facts = (...pairs) => h`<div class="wide facts">${pairs.filter(Boolean).map(([l, v]) => fact(l, v))}</div>`;
const fieldsOf = (f, fields) => { const {values, errors} = collect(f, fields); return {values, errors}; };

// THE SHARES of an agreement's parties: a ratio each (1 and 1 is half and half)
function sharesEditor(contract, shares) {
  const c = B.contracts.find(x => x.id === contract);
  const parties = c ? c.parties : [B.me];
  return h`<div class="wide shares"><small>سهم هر نفر (نسبت؛ مثلاً ۱ و ۱ یعنی نصف‌نصف)</small>${parties.map(p =>
    field('share-' + p, person(p), number.edit('share:' + p, shares?.[p] ?? '1')))}</div>`;
}
function readShares(f, errors) {
  const out = {};
  for (const input of f.querySelectorAll('[name^="share:"]')) {
    const p = input.name.slice(6), r = number.take(input.value, {required: true});
    if (r.error) errors['share-' + p] = r.error; else out[p] = r.value;
  }
  return out;
}
// the agreement select redraws the shares under it
function wireShares(f, initial) {
  const slot = f.querySelector('.shares-slot'), sel = f.querySelector('[name="contract"]');
  if (!slot || !sel) return;
  sel.addEventListener('change', () => mount(slot, sel.value ? sharesEditor(sel.value, initial?.(sel.value)) : h``));
}

// POSTING CARD LINES: one or several lines of one statement to an account, a centre and, if shared, an agreement
export function openPostCard(ctx, keys, {suggested = false} = {}) {
  const all = B.statements.flatMap(s => s.lines.map(l => ({...l, statement: s.id})));
  const lines = keys.map(([s, k]) => all.find(l => l.statement === s && l.line === k)).filter(Boolean);
  if (!lines.length) return;
  const statement = lines[0].statement, unit = lines[0].unit;
  if (lines.some(l => l.statement !== statement)) throw new Error('ردیف‌های یک صورتحساب را با هم ثبت کن.');
  const first = lines[0].posting, posted = lines.some(l => l.state === 'posted');
  const sugg = [...new Set(lines.map(l => l.suggested).filter(Boolean))];
  const total = exact.text(exact.sum(lines.map(l => l.amount)), money.places(unit) ?? 2);
  const shared = Boolean(first && Object.keys(first.bears || {}).length);
  const keysOut = lines.map(l => suggested ? {line: l.line, account: l.suggested} : l.line).filter(k => typeof k === 'string' || k.account);
  const same = lines.length === 1 ? B.pays.filter(p => p.kind === 'pay' && !p.reversedBy && p.by === B.me && p.unit === unit && exact.eq(exact.of(p.amount) || exact.ZERO, exact.of(lines[0].amount) || exact.ZERO)) : [];
  const fields = [
    ...(suggested ? [] : [{name: 'account', label: 'حساب معین', type: 'choice', required: true, placeholder: 'انتخاب حساب',
      options: accountRows({value: first?.accounts[0]}), value: first?.accounts[0] || (sugg.length === 1 ? sugg[0] : '')}]),
    {name: 'analytic', label: 'مرکز هزینه', type: 'choice', none: 'بدون مرکز هزینه', options: centreRows(first?.analytic[0]), value: first?.analytic[0] || ''},
    {name: 'contract', label: 'چه کسی هزینه را می‌دهد؟', type: 'choice', none: 'فقط ' + me(),
      options: B.contracts.map(c => ({value: c.id, label: 'تقسیم در توافق: ' + c.title})), value: shared ? agreementOf(first) : ''},
  ];
  const tail = [{name: 'note', label: 'توضیح', type: 'lines', max: 500},
    ...(lines.length === 1 ? [{name: 'replaces', label: 'این خرید قبلاً به‌صورت پرداخت ثبت شده؟', type: 'choice', none: 'نه، ثبت تازه است', wide: true,
      options: same.map(p => ({value: p.ref, label: `بله: ${p.date || 'بی‌تاریخ'} · ${p.memo} · ${p.beanTitle} (سند ${count(p.number)})`})),
      hint: same.length ? 'پرداخت قبلی با سند معکوس برمی‌گردد تا خرید دوبار شمرده نشود؛ توافق، سهم‌ها و حسابش اینجا پیش‌فرض می‌شوند.' : 'پرداختی با همین مبلغ پیدا نشد.'}] : [])];
  const body = h`${facts(['ردیف‌ها', count(lines.length)], ['جمع مبلغ', money.show(total, unit)], lines.length === 1 && ['شرح', lines[0].what], lines.length === 1 && ['تاریخ', day(lines[0].day)])}
    ${suggested ? h`<p class="wide report-note">هر ردیف با حساب پیشنهادی خودش ثبت می‌شود (${sugg.map(accountLabel).join('، ')}). ردیف‌های بدون پیشنهاد کنار گذاشته می‌شوند.</p>` : ''}
    ${form(fields)}<div class="wide shares-slot">${shared ? sharesEditor(agreementOf(first), first.bears) : ''}</div>${form(tail)}`;
  bookForm(ctx, {kind: 'post-card', bean: statement, title: posted ? 'تغییر ثبت ردیف‌ها' : 'ثبت ردیف‌های کارت در دفتر', body, wide: true,
    note: posted ? 'ثبت این ردیف در جای خودش اصلاح می‌شود: گفتهٔ قبلی برداشته و گفتهٔ تازه نوشته می‌شود؛ روزنامه تغییر را می‌نویسد و نسخهٔ قبلی در تاریخچه می‌ماند.' : SAVE_NOTE,
    read: f => {
      const {values, errors} = fieldsOf(f, [...fields, ...tail]);
      const shares = values.contract ? readShares(f, errors) : null;
      if (!showErrors(f, errors)) return null;
      return {lines: JSON.stringify(keysOut), account: suggested ? '' : values.account, analytic: values.analytic, contract: values.contract,
        shares: shares ? JSON.stringify(shares) : '', note: values.note, replaces: values.replaces || ''};
    },
    wire: f => {
      wireShares(f);
      // a purchase already written as a payment: its agreement, shares, account and centre become the defaults
      f.querySelector('[name="replaces"]')?.addEventListener('change', e => {
        const p = B.pays.find(x => x.ref === e.target.value);
        if (!p) return;
        if (p.accounts[0] && f.elements.account) f.elements.account.value = p.accounts[0];
        if (p.analytic[0]) f.elements.analytic.value = p.analytic[0];
        f.elements.contract.value = agreementOf(p);
        mount(f.querySelector('.shares-slot'), agreementOf(p) ? sharesEditor(agreementOf(p), Object.keys(p.bears).length ? p.bears : {[p.by]: '1'}) : h``);
      });
    }});
}

// THE ACCOUNT OF A PAYMENT outside the card
export function openPostPay(ctx, ref) {
  const p = B.pays.find(x => x.ref === ref);
  if (!p) return;
  const fields = [{name: 'account', label: 'حساب معین سهم ' + me(), type: 'choice', required: true, placeholder: 'انتخاب حساب',
      options: accountRows({value: p.accounts[0]}), value: p.accounts[0] || p.suggested || ''},
    {name: 'analytic', label: 'مرکز هزینه', type: 'choice', none: 'بدون مرکز هزینه', options: centreRows(p.analytic[0]), value: p.analytic[0] || ''},
    ...(p.by === B.me ? [{name: 'from_account', label: me() + ' از کجا پرداخت کرد؟', type: 'choice', none: 'نامعلوم (حساب ۱۹۰۱)',
      options: accountRows({value: p.fromAccount}), value: p.fromAccount || ''}] : [])];
  bookForm(ctx, {kind: 'post-pay', bean: p.bean, title: p.accounts.length ? 'تغییر حساب پرداخت' : 'تعیین حساب پرداخت',
    note: p.accounts.length ? 'تغییر، پرداخت قبلی را با سند معکوس برگشت می‌زند و پرداخت تازه با حساب جدید ثبت می‌کند.' : SAVE_NOTE,
    body: h`${facts(['توافق', p.beanTitle], ['شرح', p.memo], ['مبلغ', money.show(p.amount, p.unit)], ['پرداخت‌کننده', person(p.by)])}${form(fields)}`,
    read: f => {
      const {values, errors} = fieldsOf(f, fields);
      if (!showErrors(f, errors)) return null;
      return {pay: p.id, account: values.account, analytic: values.analytic, from_account: values.from_account || '', shares: ''};
    }});
}

// A voucher's history: each commit that changed it, with its journal entry and the lines it changed
export async function history(ref) {
  const known = state.histories[ref];
  if (known && known.head === B.head) return known;
  let got;
  try { got = await api.get('/api/history?ref=' + encodeURIComponent(ref)); } catch { got = {history: [], whose: null}; }
  return (state.histories[ref] = {...got, head: B.head, shown: known?.shown || false});
}
export function historyView(ref) {
  const hs = state.histories[ref];
  if (!hs) return h`<p class="muted">در حال خواندن تاریخچه…</p>`;
  return h`<div class="history"><b>تاریخچهٔ این سند</b>${hs.whose ? h`<small>${text.show(hs.whose.why)}</small>` : ''}${(hs.history || []).length ? hs.history.map(c =>
    h`<details><summary>${moment.show(String(c.when).slice(0, 16).replace('T', ' '))} · ${text.show(c.subject)} <small><bdi dir="ltr">${c.commit}</bdi></small></summary>
      ${c.journal.length ? h`<ul>${c.journal.map(l => h`<li>${text.show(l)}</li>`)}</ul>` : ''}${c.changes.length ? h`<pre dir="ltr">${c.changes.join('\n')}</pre>` : ''}</details>`)
    : h`<p class="muted">تاریخچه‌ای پیدا نشد.</p>`}</div>`;
}

// CORRECTING a voucher: a card line's posting, a manual voucher's lines, or a payment whole
export async function openEdit(ctx, ref) {
  const v = B.vouchers.find(x => x.ref === ref);
  if (v && v.source) return openPostCard(ctx, [[v.source.bean, v.source.line]]);
  if (v && v.kind === 'journal') return openJournal(ctx, {voucher: v});
  const p = B.pays.find(x => x.ref === ref);
  if (!p) throw new Error('این سند از این صفحه ویرایش نمی‌شود.');
  if (p.reversedBy) throw new Error('این پرداخت در یک برگشت رسمی آمده است؛ سند برگشت را حذف کنید، نه خود پرداخت را.');
  const whose = (await history(ref)).whose;
  const fields = [
    {name: 'what', label: 'شرح', max: 500, wide: true, value: p.note || ''},
    {name: 'day', label: 'تاریخ واقعی پرداخت', type: 'date', value: p.date || ''},
    {name: 'count', label: 'مبلغ کل', type: 'number', required: true, value: p.amount},
    {name: 'unit', label: 'ارز', type: 'choice', required: true, options: currencyRows(ctx), value: p.unit},
    {name: 'payer', label: 'چه کسی پرداخت کرد؟', type: 'choice', required: true, options: knownPersons(), value: p.by},
    {name: 'contract', label: 'در کدام توافق و چه کسی هزینه را می‌دهد؟', type: 'choice', wide: true, none: `فقط ${me()} — بیرون از توافق‌ها (دفتر روزنامهٔ ${me()})`,
      options: B.contracts.map(c => ({value: c.id, label: 'در توافق: ' + c.title})), value: agreementOf(p)},
  ];
  const tail = [
    {name: 'account', label: 'حساب معین سهم ' + me(), type: 'choice', none: 'بعداً (حساب ۱۹۰۲)', options: accountRows({value: p.accounts[0]}), value: p.accounts[0] || p.suggested || ''},
    {name: 'analytic', label: 'مرکز هزینه', type: 'choice', none: 'بدون مرکز هزینه', options: centreRows(p.analytic[0]), value: p.analytic[0] || ''},
    {name: 'from_account', label: me() + ' از کجا پرداخت کرد؟', type: 'choice', none: 'نامعلوم یا دیگری پرداخته (۱۹۰۱)', options: accountRows({value: p.fromAccount}), value: p.fromAccount || ''},
    {name: 'reason', label: 'علت اصلاح', type: 'lines', required: true, max: 500, hint: 'مثلاً: به‌اشتباه در توافق دیگری ثبت شده بود'},
  ];
  const bears = Object.keys(p.bears).length ? p.bears : {[p.by]: '1'};
  const body = h`${facts(['سند', count(p.number)], ['ثبت فعلی', p.beanTitle], ['مبلغ', money.show(p.amount, p.unit)], ['پرداخت‌کننده', person(p.by)])}
    ${whose && !whose.mine ? h`<p class="wide warn">این سند ${text.show(whose.why)} است. اگر اصلاحش کنی، نسخهٔ تازه گفتهٔ خود توست و نسخهٔ قبلی به نام گوینده‌اش در تاریخچه می‌ماند. اگر فقط با آن مخالفی، به‌جای اصلاح «اعتراض» بزن.</p>` : ''}
    ${form(fields)}<div class="wide shares-slot">${agreementOf(p) ? sharesEditor(agreementOf(p), bears) : ''}</div>${form(tail)}`;
  bookForm(ctx, {kind: 'edit-pay', bean: p.bean, title: 'اصلاح سند ' + count(p.number), body, wide: true,
    note: 'روش دفتر: گفتهٔ قبلی برداشته و گفتهٔ درست نوشته می‌شود؛ روزنامه هر تغییر و علتش را می‌نویسد و نسخهٔ قبلی در تاریخچه (گیت) می‌ماند. مانده‌ها، تراز و گزارش تحلیلی همه از همین گفته‌ها خوانده می‌شوند.',
    read: f => {
      const {values, errors} = fieldsOf(f, [...fields, ...tail]);
      if (!errors.count && values.unit) {           // the amount at the places of the currency chosen
        const r = money.take(f.elements.count.value, values.unit, {required: true});
        if (r.error) errors.count = r.error; else values.count = r.value;
      }
      const shares = values.contract ? readShares(f, errors) : null;
      if (!showErrors(f, errors)) return null;
      return {pay: p.id, what: values.what, day: values.day, count: values.count, unit: values.unit, payer: values.payer, contract: values.contract,
        shares: shares ? JSON.stringify(shares) : '', account: values.account, analytic: values.analytic, from_account: values.from_account, reason: values.reason};
    },
    wire: f => wireShares(f, c => (c === agreementOf(p) ? bears : null))});
}

// DELETING, DISPUTING, REVERSING: a voucher and the reason
const voucherBean = v => v.kind === 'journal' ? gardenerId() : v.bean;
const reasonOnly = (label, hint) => [{name: 'reason', label, type: 'lines', required: true, max: 500, hint}];
function voucherForm(ctx, ref, {kind, title, bean, note, label, hint, date = false}) {
  const v = B.vouchers.find(x => x.ref === ref);
  if (!v) return;
  const fields = [...(date ? [{name: 'date', label: 'تاریخ سند معکوس', type: 'date', value: ctx.data.asOf}] : []), ...reasonOnly(label, hint)];
  bookForm(ctx, {kind, bean: bean(v), title: title(v), note,
    body: h`${facts(date && ['سند', count(v.number)], ['تاریخ', day(v.date)], ['شرح', v.memo], ['مبلغ', money.show(v.total, v.unit)], !date && ['در', v.beanTitle])}${form(fields)}`,
    read: f => {
      const {values, errors} = fieldsOf(f, fields);
      if (!showErrors(f, errors)) return null;
      return {voucher: v.ref, ...values};
    }});
}
export const openDelete = (ctx, ref) => voucherForm(ctx, ref, {kind: 'delete-doc', bean: voucherBean, title: v => 'حذف سند ' + count(v.number),
  label: 'علت حذف', hint: 'مثلاً: تکراری ثبت شده بود',
  note: 'فقط برای سندی که اصلاً نباید ثبت می‌شد. سند و همهٔ ردیف‌هایش برداشته می‌شوند؛ روزنامه آن را با علتش نام می‌برد و نسخه‌اش در تاریخچه (گیت) می‌ماند. اگر از ردیف کارت آمده باشد، آن ردیف دوباره ثبت‌نشده می‌شود.'});
export const openDispute = (ctx, ref) => voucherForm(ctx, ref, {kind: 'dispute-pay', bean: v => v.bean, title: v => 'اعتراض به سند ' + count(v.number),
  label: 'علت اعتراض',
  note: 'وقتی سند گفتهٔ کس دیگری است (مثلاً طرف دیگر یک توافق) و نمی‌خواهی جای او حرف بزنی: نظر تو کنار گفتهٔ او ثبت می‌شود و هر دو می‌مانند تا با هم روشنش کنید.'});
export function openReverse(ctx, ref) {
  const v = B.vouchers.find(x => x.ref === ref);
  if (v?.reversedBy) throw new Error('این سند پیش‌تر برگشت خورده است.');
  voucherForm(ctx, ref, {kind: 'reverse', bean: voucherBean, title: () => 'سند معکوس', label: 'علت برگشت', date: true,
    note: 'سند اصلی در دفتر می‌ماند و سند معکوس اثر آن را خنثی می‌کند. اگر سند از ردیف کارت آمده باشد، ردیف دوباره ثبت‌نشده می‌شود.'});
}

// A MANUAL VOUCHER (or a manual voucher corrected): its lines, each a debit or a credit, balanced before it is saved
function journalRow(l, n) {
  const a = account(l.account);
  return h`<tr data-jl="${n}"><td>${choice.edit('jl-account', l.account || '', accountRows({value: l.account}), {placeholder: 'حساب'})}</td>
    <td>${a?.detail === 'person' ? choice.edit('jl-person', l.person || '', knownPersons(), {none: '—'}) : h`<select class="w-input" name="jl-person" disabled><option value="">—</option></select>`}</td>
    <td>${choice.edit('jl-analytic', l.analytic || '', centreRows(l.analytic), {none: '—'})}</td>
    <td>${number.edit('jl-debit', l.debit || '')}</td><td>${number.edit('jl-credit', l.credit || '')}</td>
    <td><input class="w-input" name="jl-memo" maxlength="500" value="${l.memo || ''}" aria-label="شرح ردیف"></td>
    <td><button type="button" class="text-button" data-jl-remove="${n}" aria-label="حذف ردیف">×</button></td></tr>`;
}
function readRows(f) {
  return [...f.querySelectorAll('tr[data-jl]')].map(tr => {
    const get = n => tr.querySelector(`[name="${n}"]`)?.value || '';
    return {account: get('jl-account'), person: get('jl-person'), analytic: get('jl-analytic'), debit: get('jl-debit'), credit: get('jl-credit'), memo: get('jl-memo')};
  });
}
function totals(f) {
  const unit = f.elements.unit.value, places = money.places(unit) ?? 2;
  const side = k => exact.sum(readRows(f).map(r => number.take(r[k]).value || '0'));
  const d = side('debit'), c = side('credit');
  return h`جمع بدهکار ${money.show(exact.text(d, places), unit)} · جمع بستانکار ${money.show(exact.text(c, places), unit)} ${exact.eq(d, c) && exact.sign(d) ? badge('تراز', 'done') : badge('تراز نیست', 'late')}`;
}
export function openJournal(ctx, {voucher = null, prefill = null} = {}) {
  const v = voucher;
  const rows = v ? v.lines.map(l => ({account: l.account, person: l.person || '', analytic: l.analytic[0] || '', memo: l.memo || '',
      debit: exact.sign(exact.of(l.dr) || exact.ZERO) ? l.dr : '', credit: exact.sign(exact.of(l.cr) || exact.ZERO) ? l.cr : ''}))
    : prefill?.lines || [{}, {}];
  const fields = [{name: 'date', label: 'تاریخ سند', type: 'date', required: true, value: v?.date || prefill?.date || ctx.data.asOf},
    {name: 'unit', label: 'ارز', type: 'choice', required: true, options: currencyRows(ctx), value: v?.unit || prefill?.unit || 'TRY'},
    {name: 'memo', label: 'شرح سند', required: true, max: 500, wide: true, value: v?.memo || prefill?.memo || ''}];
  const tail = v ? [{name: 'reason', label: 'علت اصلاح', type: 'lines', required: true, max: 500}] : [];
  const body = h`${form(fields)}<div class="wide table-scroll"><table class="journal-lines"><thead><tr><th>حساب</th><th>شخص</th><th>مرکز هزینه</th><th>بدهکار</th><th>بستانکار</th><th>شرح</th><th></th></tr></thead>
    <tbody class="jl-body">${rows.map(journalRow)}</tbody></table></div><p class="wide jl-totals"></p><p class="wide w-field-error jl-error"></p><p class="wide"><button type="button" class="secondary" data-jl-add>＋ ردیف</button></p>${form(tail)}`;
  bookForm(ctx, {kind: v ? 'edit-entry' : 'journal', bean: gardenerId(), title: v ? 'اصلاح سند ' + count(v.number) : 'سند دستی تازه', body, wide: true,
    note: v ? 'روش دفتر: ردیف‌های قبلی برداشته و ردیف‌های درست نوشته می‌شوند؛ نسخهٔ قبلی در تاریخچه می‌ماند.'
      : `برای مانده‌های افتتاحیه، جابه‌جایی بین حساب‌های خود ${me()} یا اصلاحی که هیچ پرداختی نمی‌گوید. هر ردیف یا بدهکار است یا بستانکار.`,
    read: f => {
      const {values, errors} = fieldsOf(f, [...fields, ...tail]);
      const lines = [];
      readRows(f).forEach((r, i) => {
        if (!r.account && !r.debit && !r.credit) return;
        const dr = money.take(r.debit, values.unit || 'TRY'), cr = money.take(r.credit, values.unit || 'TRY');
        if (dr.error || cr.error) errors['jl'] = `ردیف ${count(i + 1)}: ${dr.error || cr.error}`;
        lines.push({...r, debit: dr.value || '', credit: cr.value || ''});
      });
      mount(f.querySelector('.jl-error'), errors.jl ? h`${errors.jl}` : h``);
      const ok = showErrors(f, errors) && !errors.jl;
      if (!ok) return null;
      if (!lines.length) throw new Error('دست‌کم دو ردیف بنویسید.');
      return {...(v ? {voucher: v.ref, reason: values.reason} : {}), date: values.date, memo: values.memo, unit: values.unit, lines: JSON.stringify(lines)};
    },
    wire: f => {
      mount(f.querySelector('.jl-totals'), totals(f));
      const redraw = rs => { mount(f.querySelector('.jl-body'), h`${rs.map(journalRow)}`); mount(f.querySelector('.jl-totals'), totals(f)); };
      f.addEventListener('click', e => {
        if (e.target.closest('[data-jl-add]')) redraw([...readRows(f), {}]);
        const rm = e.target.closest('[data-jl-remove]');
        if (rm) { const rs = readRows(f); rs.splice(Number(rm.dataset.jlRemove), 1); redraw(rs); }
      });
      f.addEventListener('change', e => { if (e.target.name === 'jl-account' || e.target.name === 'unit') redraw(readRows(f)); });
      f.addEventListener('input', e => { if (/^jl-(debit|credit)$/.test(e.target.name)) mount(f.querySelector('.jl-totals'), totals(f)); });
    }});
}

// A ROW OF THE CHART: an account (group, general, subsidiary) or a centre (plan, account), and what it links to
export function openChartRow(ctx, scheme, code = '', parent = '') {
  const rows = scheme === 'account' ? B.chart.accounts : B.chart.analytic;
  const r = rows.find(x => x.code === code);
  const levels = scheme === 'account' ? ['group', 'general', 'subsidiary'] : ['plan', 'account'];
  const p = rows.find(x => x.code === (r ? r.parent : parent));
  const level = r ? r.level : p ? levels[levels.indexOf(p.level) + 1] : levels[0];
  const linkable = B.beans.filter(b => b.kind !== 'document' || b.id.startsWith('card'));
  const fields = [
    ...(code ? [] : [{name: 'code', label: 'کد', required: true, max: 40}]),
    {name: 'name', label: 'نام', required: true, max: 120, value: r?.name || ''},
    ...(scheme === 'account' && level === 'group' ? [{name: 'type', label: 'نوع', type: 'choice', required: true, options: TYPES, value: r?.type || ''}] : []),
    ...(scheme === 'account' ? [{name: 'detail', label: 'حساب تفصیلی', type: 'choice', none: 'ندارد', options: {person: 'شخص لازم است'}, value: r?.detail || ''}] : []),
    {name: 'status', label: 'وضعیت', type: 'choice', none: 'فعال', options: {closed: 'بسته'}, value: r?.status || ''},
  ];
  const body = h`${facts(['سطح', LEVELS[level]], ['زیرِ', p ? p.code + ' — ' + p.name : 'بالاترین سطح'], code && ['کد', h`<bdi dir="ltr">${code}</bdi>`])}${form(fields)}
    <fieldset class="wide links"><legend>پیوند به توافق‌ها، کارت‌ها و اشخاص</legend>${linkable.map(b => h`<label><input type="checkbox" data-link="${b.id}"${r?.links?.includes(b.id) ? h` checked` : ''}> ${text.show(b.title)}</label>`)}</fieldset>`;
  bookForm(ctx, {kind: 'chart-account', bean: gardenerId(), title: code ? 'ویرایش حساب' : 'حساب تازه', body,
    note: code && r?.used ? 'این حساب در اسناد به کار رفته است: نامش را می‌توان عوض کرد یا بست، ولی جابه‌جا نمی‌شود.' : SAVE_NOTE,
    read: f => {
      const {values, errors} = fieldsOf(f, fields);
      if (!code && values.code && !/^[A-Za-z0-9][A-Za-z0-9-]*$/.test(values.code)) errors.code = 'کد فقط رقم، حرف لاتین و خط تیره.';
      if (!showErrors(f, errors)) return null;
      return {scheme, original: code, level, parent: r ? r.parent || '' : parent, code: code || values.code, name: values.name,
        type: values.type || '', detail: values.detail || '', status: values.status || '',
        links: [...f.querySelectorAll('[data-link]:checked')].map(i => i.dataset.link).join(' ')};
    }});
}

// THE ACTIONS any books page offers (registered with the shared ones: a payment is corrected from the agreements page
// too, and a voucher opens from a ledger or a check)
export const actions = {
  'bk-period': (el, ctx) => {
    const val = n => document.querySelector(`[name="${n}"]`)?.value || '';
    const from = moment.take(val('period-from')), to = moment.take(val('period-to'));
    if (from.error || to.error) throw new Error(from.error || to.error);
    if (from.value && to.value && from.value > to.value) throw new Error('آغاز بازه پس از پایان آن است.');
    Object.assign(state.period, {from: from.value, to: to.value, unit: val('period-unit') || state.period.unit});
    return ctx.rerender();
  },
  'bk-period-clear': (el, ctx) => { state.period.from = state.period.to = ''; return ctx.rerender(); },
  'bk-correct': async (el, ctx) => { await load(ctx); return openEdit(ctx, el.dataset.ref); },
  'bk-delete': (el, ctx) => openDelete(ctx, el.dataset.ref),
  'bk-dispute': (el, ctx) => openDispute(ctx, el.dataset.ref),
  'bk-reverse': async (el, ctx) => { await load(ctx); return openReverse(ctx, el.dataset.ref); },
  'bk-journal': (el, ctx) => openJournal(ctx),
  'bk-goto-voucher': (el, ctx) => {
    state.open.add(el.dataset.ref); state.focus = el.dataset.ref; state.vouchers.search = '';
    return show(ctx, 'vouchers');
  },
  'bk-ledger': (el, ctx) => { state.report = 'ledger'; state.ledger = {code: el.dataset.code, person: ''}; return show(ctx, 'finance'); },
  'bk-person-ledger': (el, ctx) => { state.report = 'ledger'; state.ledger = {code: '1301', person: el.dataset.person}; return show(ctx, 'finance'); },
};
// a books page, drawn again when it is the one open
// a page of the books, or the page made of it: drawn again where it stands, else opened
const show = (ctx, id) => ctx.page?.id === id || ctx.part === id ? ctx.rerender() : ctx.open(id);
