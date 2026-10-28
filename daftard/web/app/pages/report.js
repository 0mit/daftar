// The company report: the cases with activity in a month (in the reader's calendar), ready to review, print or send
// as CSV. It names clients: the page says so before anything leaves.
import { h, mount } from '/toolbox/safe.js';
import * as moment from '/toolbox/moment.js';
import * as text from '/toolbox/text.js';
import { me } from '/toolbox/settings.js';
import { table } from '/toolbox/table.js';
import { filters, matches, filterBar } from './cases.js';
const state = {month: '', unknown: false};
const ym = day => { const p = moment.toPersian(day); return `${p.y}-${String(p.m).padStart(2, '0')}`; };
const monthLabel = key => { if (!key) return 'همهٔ دوره‌ها'; const [y, m] = key.split('-').map(Number); const day = moment.fromPersian(y, m, 1);
  return new Intl.DateTimeFormat('fa-IR-u-ca-persian', {month: 'long', year: 'numeric', timeZone: 'UTC'}).format(new Date(day + 'T12:00:00Z')); };
const rows = d => d.cases.filter(matches).filter(c => !state.month || (c.activityDates || []).some(x => ym(x) === state.month) || (state.unknown && !(c.activityDates || []).length));
const LABELS = [['goal', 'هدف'], ['request', 'درخواست'], ['advice', 'شرح مشاوره'], ['actions', 'اقدام'], ['outcome', 'نتیجه'], ['notes', 'یادداشت']];
const contacts = c => Object.values(c.record.contacts || {}).map(o => [o.date || 'تاریخ نامعلوم', ...LABELS.filter(([k]) => o[k]).map(([k, l]) => l + ': ' + o[k])].join(' — ')).join('\n\n');
const HEADERS = ['کلاینت', 'شرح مشاوره و تماس‌ها', 'تاریخ مشاوره', 'نوع', 'وضعیت', 'دانشگاه پیشنهادی', 'شهریه پیشنهادی', 'نتیجه پیشنهاد', 'پرداخت دانشجو', 'ثبت‌نام نهایی', 'پیگیری‌ها'];
const cells = c => [c.name, contacts(c), c.date || 'تاریخ نامعلوم', c.type, c.status, c.offers.map(o => o.university).join(' / '),
  c.offers.map(o => (o.amount || '') + ' ' + (o.currency || '')).join(' / '), c.offers.map(o => o.response).join(' / '), c.payment, c.finalRegistration,
  c.followups.map(f => `${f.topic || ''} (${f.status || ''}؛ ${f.due || 'موعد نامعلوم'})`).join(' / ')];
const reportTable = d => table({empty: 'در این بازه موردی پیدا نشد.', rows: rows(d), columns: HEADERS.map((title, i) => ({title, cell: c => text.show(cells(c)[i], {lines: i === 1})}))});
function csv(d) {
  const cell = v => '"' + String(v ?? '').replace(/^[=+@\-\t\r]/, "'$&").replaceAll('"', '""') + '"';
  const body = [HEADERS, ...rows(d).map(cells)].map(r => r.map(cell).join(',')).join('\r\n');
  const url = URL.createObjectURL(new Blob(['﻿' + body], {type: 'text/csv;charset=utf-8'}));
  const a = document.createElement('a'); a.href = url; a.download = 'report-' + (state.month || 'all') + '.csv'; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export default {
  id: 'reports', nav: 'گزارش شرکت', title: 'گزارش شرکت',
  render(ctx) {
    const d = ctx.data;
    const months = [...new Set(d.cases.flatMap(c => (c.activityDates || []).map(ym)))].sort().reverse();
    const extra = h`<select data-report="month" aria-label="ماه گزارش"><option value="">همهٔ دوره‌ها</option>${months.map(m => h`<option value="${m}"${m === state.month ? h` selected` : ''}>${monthLabel(m)}</option>`)}</select>
      <label class="w-check"><input type="checkbox" data-report="unknown"${state.unknown ? h` checked` : ''}> شامل تاریخ نامعلوم</label>`;
    return h`<section class="panel"><h2 class="print-heading" id="report-heading">گزارش مشاوره و پیگیری ${me()} — ${monthLabel(state.month)}</h2>
      <div class="panel-head"><div><h2>گزارش آمادهٔ مرور</h2><p>پرونده‌هایی با فعالیت ثبت‌شده در ماه انتخابی؛ «همهٔ دوره‌ها» یعنی بدون فیلتر ماه.</p></div>
      <div><button class="secondary" data-action="report-csv">دریافت CSV</button> <button class="secondary" data-action="report-print">چاپ / PDF</button></div></div>
      ${filterBar(d, extra)}<p class="report-note">خروجی فقط ردیف‌های فیلترشده را دربر می‌گیرد و شامل نام کلاینت است. پیش از اشتراک مرور کنید. شهریهٔ پیشنهادی به معنی پرداخت نیست.</p>
      <div id="report-table">${reportTable(d)}</div></section>`;
  },
  actions: {'report-csv': (el, ctx) => csv(ctx.data), 'report-print': () => window.print()},
  input(e, ctx) {
    const f = e.target.dataset.filter, r = e.target.dataset.report;
    if (f && f in filters) filters[f] = e.target.value;
    else if (r === 'month') state.month = e.target.value;
    else if (r === 'unknown') state.unknown = e.target.checked;
    else return;
    mount(document.getElementById('report-table'), reportTable(ctx.data));
    mount(document.getElementById('report-heading'), h`گزارش مشاوره و پیگیری ${me()} — ${monthLabel(state.month)}`);
  },
};
