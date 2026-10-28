// A board's garden (`kind: board`): its agreements, the payments under them, what each person owes the gardener and is
// owed, and the exchange — what the board (board/model.py of the tools' tree) reads and writes. A payment is written
// as daftar writes one, through the garden's own tools; one in an agreement taken from another garden is read here
// and corrected there. Its forms send the board's own shape: {kind, values, head}.
import { h } from '/toolbox/safe.js';
import * as api from '/toolbox/api.js';
import * as money from '/toolbox/money.js';
import * as moment from '/toolbox/moment.js';
import * as text from '/toolbox/text.js';
import { me } from '/toolbox/settings.js';
import { form, collect, showErrors } from '/toolbox/form.js';
import { openDialog } from '/toolbox/dialog.js';
import { table } from '/toolbox/table.js';
import { badge } from '../../common.js';
import { CATEGORIES } from '../accounts.js';

// the categories offered: the usual ones, and every one this garden's gardener has written
export const categories = d => [...new Set([...CATEGORIES, ...allPays(d).map(p => p.category).filter(Boolean)])];

export const who = (d, p) => d.people?.[p] || (p === d.me ? (d.meTitle || me()) : p);
// every payment, each with its agreement, the latest first
export const allPays = d => d.agreements.flatMap(a => a.pays.map(p => ({...p, agreement: a})))
  .sort((x, y) => (y.day || '').localeCompare(x.day || ''));
const bearers = (d, p) => p.bears.length === 1 && p.bears[0].by === p.by ? 'فقط خودش'
  : p.bears.map(b => who(d, b.by) + (b.share !== '1' ? ' ×' + b.share : '')).join('، ');

export function payTable(d, rows, {actions = true} = {}) {
  return table({rows, empty: 'پرداختی ثبت نشده است.', columns: [
    {title: 'روز', cell: p => p.day ? moment.show(p.day) : '—', sort: p => p.day || ''},
    {title: 'شرح', cell: p => h`${text.show(p.note)}<small>${text.show(p.agreement.title)}${p.agreement.from ? h` · از ${text.show(p.agreement.fromTitle)}` : ''}</small>`},
    {title: 'دسته', cell: p => h`${p.category ? badge(p.category) : h`<small class="muted">بدون دسته</small>`} <button class="text-button" data-action="board-categorize" data-a="${p.agreement.id}" data-p="${p.id}">${p.category ? 'تغییر' : 'دسته‌بندی'}</button>`},
    {title: 'مبلغ', align: 'num', cell: p => money.show(p.count, p.unit)},
    {title: 'پرداخت‌کننده', cell: p => text.show(who(d, p.by))},
    {title: 'سهم‌برها', cell: p => text.show(bearers(d, p))},
    {title: '', cell: p => actions && p.agreement.writable ? h`<button class="text-button" data-action="board-edit" data-a="${p.agreement.id}" data-p="${p.id}">اصلاح</button>
      <button class="text-button" data-action="board-delete" data-a="${p.agreement.id}" data-p="${p.id}">حذف</button>`
      : !p.agreement.writable ? h`<small>اصلاح در ${text.show(p.agreement.fromTitle || p.agreement.from)}</small>` : ''},
  ]});
}

// the payment form: what, how much, which day, who paid, who carries a share (one check each)
function payFields(d, a) {
  const units = (d.units || ['TRY']).map(u => ({value: u, label: u}));
  return [
    {name: 'what', label: 'شرح پرداخت', required: true, max: 500, wide: true},
    {name: 'count', label: 'مبلغ', type: 'number', required: true},
    {name: 'unit', label: 'ارز', type: 'choice', required: true, options: units},
    {name: 'day', label: 'روز پرداخت', type: 'date'},
    {name: 'payer', label: 'چه کسی پرداخت کرد؟', type: 'choice', required: true, options: a.parties.map(p => ({value: p, label: who(d, p)}))},
    ...a.parties.flatMap(p => [{name: 'bear-' + p, label: 'سهم دارد: ' + who(d, p), type: 'check'},
      {name: 'share-' + p, label: 'نسبت سهم ' + who(d, p), type: 'number', hint: '۱ و ۱ یعنی نصف‌نصف؛ ۲ و ۱ یعنی دو سوم و یک سوم'}]),
  ];
}
function read(f, d, a, fields, extra = []) {
  const {values: v, errors} = collect(f, [...fields, ...extra]);
  if (v.unit && !errors.count) { const m = money.take(f.elements.count.value, v.unit, {required: true, positive: true}); if (m.error) errors.count = m.error; else v.count = m.value; }
  const bears = a.parties.filter(p => v['bear-' + p]);
  if (!bears.length) errors['bear-' + a.parties[0]] = 'دست‌کم یک نفر سهم دارد.';
  for (const p of bears) if (v['share-' + p] !== undefined && v['share-' + p] !== '' && !(Number(v['share-' + p]) > 0)) errors['share-' + p] = 'نسبت سهم عددی مثبت است.';
  if (!showErrors(f, errors)) return null;
  const ratio = p => { const s = String(v['share-' + p] ?? '').trim(); return s && s !== '1' ? p + ':' + s : p; };
  const out = {agreement: a.id, what: v.what, count: String(v.count), unit: v.unit, day: v.day || '', payer: v.payer, bearers: bears.map(ratio).join(',')};
  for (const e of extra) out[e.name] = v[e.name] || '';
  return out;
}
const save = async (ctx, kind, values) => {
  await api.post('/api/save', {kind, values, head: ctx.data.head});
  ctx.notice('در دفتر ذخیره شد.');
  await ctx.reload();
};
const find = (d, el) => {
  const a = d.agreements.find(x => x.id === el.dataset.a);
  return {a, p: a?.pays.find(x => x.id === el.dataset.p)};
};

export const actions = {
  'board-add': (el, ctx) => {
    const d = ctx.data, a = d.agreements.find(x => x.id === el.dataset.a);
    if (!a) return;
    const fields = payFields(d, a);
    const values = {unit: d.units?.[0] || 'TRY', payer: d.me, ...Object.fromEntries(a.parties.flatMap(p => [['bear-' + p, true], ['share-' + p, '1']]))};
    openDialog({title: 'پرداخت در ' + a.title, wide: true, body: form(fields, values),
      onSubmit: async f => { const v = read(f, d, a, fields); if (!v) return false; await save(ctx, 'add-pay', v); return true; }});
  },
  'board-edit': (el, ctx) => {
    const d = ctx.data, {a, p} = find(d, el);
    if (!p) return;
    const fields = payFields(d, a), reason = [{name: 'reason', label: 'علت اصلاح', type: 'lines', required: true, max: 500, wide: true}];
    const values = {what: p.note, count: p.count, unit: p.unit, day: p.day, payer: p.by,
      ...Object.fromEntries(a.parties.map(x => ['share-' + x, '1'])), ...Object.fromEntries(p.bears.flatMap(b => [['bear-' + b.by, true], ['share-' + b.by, b.share]]))};
    openDialog({title: 'اصلاح پرداخت', wide: true, body: form([...fields, ...reason], values),
      note: 'پرداخت از دفتر برداشته و درست نوشته می‌شود؛ روزنامه علتش را می‌نویسد و نسخهٔ قبلی در تاریخچه می‌ماند.',
      onSubmit: async f => { const v = read(f, d, a, fields, reason); if (!v) return false; await save(ctx, 'edit-pay', {...v, pay: p.id}); return true; }});
  },
  'board-delete': (el, ctx) => {
    const d = ctx.data, {a, p} = find(d, el);
    if (!p) return;
    const fields = [{name: 'reason', label: 'علت حذف', type: 'lines', required: true, max: 500, wide: true}];
    openDialog({title: 'حذف پرداخت', submit: 'حذف', body: h`<p class="wide">${text.show(p.note)} · ${money.show(p.count, p.unit)}</p>${form(fields)}`,
      onSubmit: async f => {
        const {values: v, errors} = collect(f, fields);
        if (!showErrors(f, errors)) return false;
        await save(ctx, 'delete-pay', {agreement: a.id, pay: p.id, reason: v.reason});
        return true;
      }});
  },
  'board-categorize': (el, ctx) => {
    const d = ctx.data, {a, p} = find(d, el);
    if (!p) return;
    const fields = [{name: 'category', label: 'دسته', suggest: categories(d), max: 120, placeholder: 'انتخاب از فهرست یا نوشتن دستهٔ دلخواه', wide: true}];
    openDialog({title: 'دسته‌بندی پرداخت', note: 'دسته، ثبت خود شماست و در دفتر حساب خودتان می‌ماند؛ خود پرداخت و توافق تغییر نمی‌کنند. خالی گذاشتن، آن را به بدون دسته برمی‌گرداند.',
      body: h`<p class="wide">${text.show(p.note)} · ${money.show(p.count, p.unit)}</p>${form(fields, {category: p.category || ''})}`,
      onSubmit: async f => {
        const {values: v, errors} = collect(f, fields);
        if (!showErrors(f, errors)) return false;
        await save(ctx, 'categorize', {agreement: a.id, pay: p.id, category: v.category || ''});
        return true;
      }});
  },
  'board-exchange-now': async (el, ctx) => { await api.post('/api/sync'); ctx.notice('یک دور تبادل آغاز شد؛ نتیجه‌اش به‌زودی اینجا می‌آید.'); },
};

export const owesText = b => b.owes ? 'به تو بدهکار است' : 'از تو طلبکار است';
export { badge };
