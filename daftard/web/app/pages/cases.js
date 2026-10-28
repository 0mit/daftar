// The consultation cases: the list with its filters, a case's whole record in one dialog, and every form that changes
// one (a new case, the case itself, a contact, an offer, a follow-up and its result, the registration, a person's
// name and contacts, the case's private profile). Private fields are held off git by the garden's model; the forms
// show them only on the machine that holds them.
import { h, mount } from '/toolbox/safe.js';
import * as moment from '/toolbox/moment.js';
import * as text from '/toolbox/text.js';
import * as name from '/toolbox/name.js';
import * as money from '/toolbox/money.js';
import { form, collect, showErrors } from '/toolbox/form.js';
import { openDialog } from '/toolbox/dialog.js';
import { newRequest } from '/toolbox/api.js';
import { badge, fact, clientTable, taskRow, isOpenFollowup } from '../common.js';

const FA_DIGITS = '۰۱۲۳۴۵۶۷۸۹';
const ascii = s => String(s).replace(/[۰-۹]/g, d => FA_DIGITS.indexOf(d));
export const filters = {search: '', type: '', status: ''};
export const matches = c => (!filters.search || [c.name, c.phone, c.id].some(x => String(x || '').includes(filters.search) || String(x || '').includes(ascii(filters.search))))
  && (!filters.type || c.type === filters.type) && (!filters.status || c.status === filters.status);
export const filterBar = (d, extra = '') => h`<div class="filters"><input type="search" data-filter="search" aria-label="جستجوی کلاینت" placeholder="جستجوی نام یا تلفن…" value="${filters.search}">
  <select data-filter="type" aria-label="نوع مشاوره"><option value="">همهٔ مشاوره‌ها</option>${d.types.map(t => h`<option${t === filters.type ? h` selected` : ''}>${t}</option>`)}</select>
  <select data-filter="status" aria-label="وضعیت پرونده"><option value="">همهٔ وضعیت‌ها</option>${d.statuses.map(t => h`<option${t === filters.status ? h` selected` : ''}>${t}</option>`)}</select>${extra}</div>`;

// the currencies the law's table lists, by their names in the reader's language (CLDR), the common ones first
export function currencyOptions(d) {
  const first = ['TRY', 'USD', 'EUR', 'IRR', 'GBP', 'AED'];
  let names; try { names = new Intl.DisplayNames(['fa'], {type: 'currency'}); } catch { names = null; }
  return (d.currencies || []).map(c => ({value: c.code, label: (names ? names.of(c.code) : c.name) + ' — ' + c.code}))
    .sort((a, b) => ((first.indexOf(a.value) + 1) || 99) - ((first.indexOf(b.value) + 1) || 99));
}
const area = (n, l, extra = {}) => ({name: n, label: l, type: 'lines', ...extra});
export const FORMS = {
  'new-case': {title: 'پروندهٔ جدید', fields: d => [{name: 'name', label: 'نام کلاینت جدید (در مخزن خصوصی)'},
    {name: 'phone', label: 'تلفن (در مخزن خصوصی)', type: 'phone'}, {name: 'person', label: 'یا شناسهٔ شخص موجود', type: 'id'},
    {name: 'consultation_on', label: 'تاریخ اولین مشاوره', type: 'date'}, {name: 'consultation_type', label: 'نوع مشاوره', type: 'choice', options: d.types},
    {name: 'case_status', label: 'وضعیت پرونده', type: 'choice', options: d.statuses}, area('advice', 'شرح مشاوره انجام‌شده')]},
  'case': {title: 'ویرایش پرونده', fields: d => [{name: 'consultation_on', label: 'تاریخ اولین مشاوره', type: 'date'},
    {name: 'consultation_type', label: 'نوع مشاوره', type: 'choice', options: d.types}, {name: 'case_status', label: 'وضعیت پرونده', type: 'choice', options: d.statuses}]},
  'offer': {title: 'پیشنهاد دانشگاه', fields: d => [{name: 'university', label: 'دانشگاه', required: true}, {name: 'offered_on', label: 'تاریخ پیشنهاد', type: 'date'},
    {name: 'count', label: 'شهریهٔ پیشنهادی', type: 'number'}, {name: 'unit', label: 'ارز', type: 'choice', options: currencyOptions(d)},
    area('client_response', 'پاسخ کلاینت'), area('funds', 'آمادگی مبلغ'), area('payment_terms', 'شرایط پرداخت')]},
  'contact': {title: 'تماس', fields: () => [{name: 'date', label: 'تاریخ تماس', type: 'date'}, area('goal', 'هدف کلاینت'), area('request', 'درخواست'),
    area('advice', 'شرح مشاوره'), area('actions', 'اقدام انجام‌شده'), area('outcome', 'نتیجهٔ تماس'), area('notes', 'یادداشت')]},
  'followup': {title: 'پیگیری', fields: () => [area('topic', 'موضوع پیگیری', {required: true}),
    {name: 'responsible', label: 'مسئول', type: 'choice', options: ['مشاور', 'کلاینت'], required: true}, {name: 'due', label: 'موعد', type: 'date'}]},
  'complete': {title: 'ثبت نتیجهٔ پیگیری', fields: () => [{name: 'completed_on', label: 'تاریخ انجام', type: 'date'}, area('outcome', 'نتیجهٔ پیگیری', {required: true})]},
  'registration': {title: 'وضعیت ثبت‌نام', fields: () => [area('state', 'مرحلهٔ ثبت‌نام'), area('student_payment', 'وضعیت پرداخت دانشجو'), area('final_registration', 'نتیجهٔ ثبت‌نام نهایی')]},
  'person-contact': {title: 'مشخصات تماس', fields: () => [{name: 'name', label: 'نام', required: true}, {name: 'phone', label: 'تلفن', type: 'phone'},
    {name: 'email', label: 'ایمیل', type: 'email'}, area('address', 'نشانی'), area('notes', 'یادداشت')]},
  'case-profile': {title: 'سن و مشخصات کلاینت', fields: () => [{name: 'age', label: 'سن'}, {name: 'education', label: 'تحصیلات'}, {name: 'current_area', label: 'محل سکونت'},
    {name: 'turkey_stay', label: 'وضعیت حضور در ترکیه'}, {name: 'original-diploma', label: 'اصل مدرک'}, {name: 'transcript', label: 'ریزنمرات'},
    {name: 'diploma-photo', label: 'عکس مدرک'}, {name: 'diploma-translation', label: 'ترجمهٔ مدرک'}, area('notes', 'یادداشت')]},
};
const SECTIONS = {offer: 'offers', contact: 'contacts', followup: 'followups'};

// open one form; on save, the case it belongs to opens again with what was saved
export function openForm(ctx, kind, bean = '', {entry = '', values = {}, note = '', title = '', reopen = ''} = {}) {
  const spec = FORMS[kind], fields = spec.fields(ctx.data), request = newRequest(), head = ctx.data.head;
  const editing = Boolean(entry) && SECTIONS[kind];
  const extra = editing ? h`<label class="wide w-check remove-item"><input type="checkbox" name="remove" value="true"> این مورد را از پرونده بردار (اشتباه ثبت شده بود)</label>` : '';
  openDialog({title: title || spec.title, note, body: h`${form(fields, values)}${extra}`, onSubmit: async f => {
    const {values: v, errors} = collect(f, fields);
    if (!showErrors(f, errors)) return false;
    if (entry) v.entry = entry;
    if (editing && f.elements.remove?.checked) v.remove = '1';
    await ctx.save(kind, bean, v, {head, request});
    if (reopen) setTimeout(() => openCase(ctx, reopen));
    return true;
  }});
}

export function openCase(ctx, id) {
  const c = ctx.data.cases.find(x => x.id === id);
  if (!c) return;
  const person = (ctx.data.people || []).find(p => p.id === c.person && p.state === 'here');
  const btn = (action, label, extra = {}) => h`<button class="secondary" data-action="${action}" data-case="${c.id}"${Object.entries(extra).map(([k, v]) => h` data-${k}="${v}"`)}>${label}</button>`;
  const editItem = (kind, key) => h`<button class="text-button" data-action="edit-item" data-kind="${kind}" data-case="${c.id}" data-entry="${key}">ویرایش</button>`;
  const body = h`<div class="facts wide">${fact('تلفن', name.show(c.phone, {kind: 'phone', link: true}))}${fact('نوع مشاوره', c.type)}${fact('وضعیت پرونده', c.status)}
    ${fact('تاریخ مشاوره', c.date ? moment.show(c.date) : null)}${fact('سن', c.age)}${fact('تحصیلات', c.education)}${fact('محل سکونت', c.area)}${fact('حضور در ترکیه', c.stay)}</div>
    ${c.privateNote ? h`<p class="muted wide">${text.show(c.privateNote, {lines: true})}</p>` : ''}
    <div class="actions wide">${btn('case-form', 'ویرایش پرونده', {kind: 'case'})}${btn('case-form', '＋ ثبت تماس', {kind: 'contact'})}${btn('case-form', '＋ پیشنهاد دانشگاه', {kind: 'offer'})}
      ${btn('case-form', '＋ پیگیری', {kind: 'followup'})}${btn('case-form', 'وضعیت ثبت‌نام', {kind: 'registration'})}
      ${person ? h`<button class="secondary" data-action="edit-person" data-person="${person.id}" data-case="${c.id}">ویرایش نام و تماس</button>` : ''}
      ${c.profileFields ? btn('edit-profile', 'ویرایش سن و مشخصات') : ''}</div>
    <div class="detail-section wide"><h3>ثبت‌نام و پرداخت</h3><div class="facts">${fact('مرحله', c.registration)}${fact('پرداخت دانشجو', c.payment)}${fact('ثبت‌نام نهایی', c.finalRegistration)}</div></div>
    <div class="detail-section wide"><h3>پیشنهادها</h3>${Object.entries(c.record.offers || {}).map(([k, o]) => h`<div class="panel"><b>${text.show(o.university)}</b> ${editItem('offer', k)}
      <div class="facts">${fact('شهریه', o.tuition?.count ? money.show(o.tuition.count, o.tuition.unit) : null)}${fact('تاریخ پیشنهاد', o.offered_on ? moment.show(o.offered_on) : null)}
      ${fact('پاسخ کلاینت', o.client_response)}${fact('آمادگی مبلغ', o.funds)}${fact('شرایط پرداخت', o.payment_terms)}</div></div>`)}${Object.keys(c.record.offers || {}).length ? '' : h`<p class="muted">پیشنهادی ثبت نشده.</p>`}</div>
    <div class="detail-section wide"><h3>تماس‌ها</h3>${Object.entries(c.record.contacts || {}).map(([k, o]) => h`<div class="panel">${editItem('contact', k)}<div class="facts">
      ${fact('تاریخ', o.date ? moment.show(o.date) : null)}${[['goal', 'هدف'], ['request', 'درخواست'], ['advice', 'مشاوره'], ['actions', 'اقدام'], ['outcome', 'نتیجه'], ['notes', 'یادداشت']].map(([key, l]) => fact(l, o[key]))}</div></div>`)}
      ${Object.keys(c.record.contacts || {}).length ? '' : h`<p class="muted">تماس جداگانه‌ای ثبت نشده.</p>`}</div>
    <div class="detail-section wide"><h3>همهٔ پیگیری‌ها</h3>${Object.entries(c.record.followups || {}).map(([id, f]) => h`${isOpenFollowup(f) ? taskRow({...f, id, case: c}, ctx.data.asOf)
      : h`<div class="row"><div><b>${text.show(f.topic)}</b><small>${text.show(f.outcome)}</small><small>${f.completed_on ? moment.show(f.completed_on) : 'تاریخ انجام نامعلوم'}</small></div>${badge('انجام‌شده', 'done')}</div>`}${editItem('followup', id)}`)}
      ${Object.keys(c.record.followups || {}).length ? '' : h`<p class="muted">پیگیری ثبت نشده.</p>`}</div>
    <div class="detail-section wide"><h3>مدارک و اطلاعات تکمیلی</h3><div class="facts">${(c.documents || []).map(d => fact(d.label, d.status))}${(c.privateExtras || []).map(d => fact(d.label, d.value))}</div></div>`;
  openDialog({title: c.name, body, wide: true});
}

export const actions = {
  'open-case': (el, ctx) => openCase(ctx, el.dataset.id),
  'new-case': (el, ctx) => openForm(ctx, 'new-case'),
  'case-form': (el, ctx) => {
    const c = ctx.data.cases.find(x => x.id === el.dataset.case), kind = el.dataset.kind;
    const values = kind === 'case' ? {...c.record, consultation_on: c.record.consultation_on} : kind === 'registration' ? (c.record.registration || {}) : {};
    openForm(ctx, kind, c.id, {values, title: FORMS[kind].title + ' · ' + c.name, reopen: c.id});
  },
  'complete-followup': (el, ctx) => openForm(ctx, 'complete', el.dataset.case, {entry: el.dataset.entry, reopen: ''}),
  'edit-item': (el, ctx) => {
    const c = ctx.data.cases.find(x => x.id === el.dataset.case), kind = el.dataset.kind, key = el.dataset.entry;
    const item = c?.record[SECTIONS[kind]]?.[key];
    if (!item) return;
    const values = {...item, ...(kind === 'offer' ? {count: item.tuition?.count || '', unit: item.tuition?.unit || ''} : {})};
    openForm(ctx, kind, c.id, {entry: key, values, title: 'ویرایش · ' + c.name, reopen: c.id, note: 'تغییر در همین مورد ثبت می‌شود و نسخهٔ قبلی در تاریخچهٔ دفتر می‌ماند.'});
  },
  'edit-person': (el, ctx) => {
    const p = (ctx.data.people || []).find(x => x.id === el.dataset.person);
    if (!p || p.state !== 'here') throw new Error(p?.state === 'erased' ? 'اطلاعات خصوصی این شخص به درخواست خودش حذف شده است.' : 'اطلاعات تماس این شخص روی این دستگاه نیست.');
    openForm(ctx, 'person-contact', p.id, {values: p, title: 'مشخصات تماس · ' + p.name, reopen: el.dataset.case || '',
      note: 'نام و راه‌های تماس فقط در مخزن خصوصی همین رایانه نگه داشته می‌شوند، نه در گیت؛ دفتر فقط ثبت می‌کند که تغییر کردند.'});
  },
  'edit-profile': (el, ctx) => {
    const c = ctx.data.cases.find(x => x.id === el.dataset.case);
    if (!c?.profileFields) throw new Error('مشخصات خصوصی این پرونده روی این دستگاه در دسترس نیست.');
    openForm(ctx, 'case-profile', c.id, {values: c.profileFields, title: 'سن و مشخصات · ' + c.name, reopen: c.id,
      note: (c.profileFields.held ? '' : 'این پرونده هنوز مشخصات خصوصی ندارد؛ با ذخیره، در مخزن خصوصی ساخته می‌شود. ') + 'خالی کردن یک فیلد آن را پاک می‌کند.'});
  },
};

export default {
  id: 'clients', nav: 'پرونده‌ها', title: 'پرونده‌های مشاوره',
  headerActions: () => h`<button class="primary" data-action="new-case">＋ پروندهٔ جدید</button>`,
  render: ctx => h`<section class="panel">${filterBar(ctx.data)}<div id="client-table">${clientTable(ctx.data.cases.filter(matches), ctx.data.asOf)}</div></section>`,
  input(e, ctx) {          // only the table is drawn again: the search box keeps its focus and caret
    const k = e.target.dataset.filter;
    if (!k || !(k in filters)) return;
    filters[k] = e.target.value;
    mount(document.getElementById('client-table'), clientTable(ctx.data.cases.filter(matches), ctx.data.asOf));
  },
};
