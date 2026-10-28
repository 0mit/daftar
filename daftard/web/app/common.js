// What several pages share: badges, facts, a case's follow-ups, the clients' table.
import { h } from '/toolbox/safe.js';
import * as moment from '/toolbox/moment.js';
import * as text from '/toolbox/text.js';
import * as name from '/toolbox/name.js';
import * as being from '/toolbox/being.js';
import * as number from '/toolbox/number.js';
import { table } from '/toolbox/table.js';
export const badge = (v, tone = '') => h`<span class="badge ${tone}">${v}</span>`;
// a fact: a label, and its value as a widget (Safe) or as text
export const fact = (label, value) => h`<div class="fact"><small>${label}</small>${value && typeof value === 'object' && 'html' in value ? value : text.show(value)}</div>`;
export const count = v => number.plain(v) ?? String(v);
const DONE = 'انجام‌شده';
export const isOpenFollowup = f => f.status !== DONE;
export function openFollowups(data) {
  return data.cases.flatMap(c => Object.entries(c.record.followups || {}).filter(([, f]) => isOpenFollowup(f)).map(([id, f]) => ({...f, id, case: c})));
}
// late, today, future, or unknown: a follow-up's due day against the server's today
export function bucket(f, asOf) {
  const day = f.due && f.due !== 'null' ? String(f.due).slice(0, 10) : '';
  return !day ? 'unknown' : day < asOf ? 'late' : day === asOf ? 'today' : 'future';
}
export const BUCKETS = {late: 'موعد گذشته', today: 'امروز', future: 'روزهای آینده', unknown: 'بدون موعد'};
export const sortDue = rows => [...rows].sort((a, b) => (a.due || '9999').localeCompare(b.due || '9999'));
export const caseLink = c => being.show(c.id, c.name, {action: 'open-case'});
export function taskRow(f, asOf) {
  const b = bucket(f, asOf);
  return h`<div class="row"><div>${caseLink(f.case)}<small>${text.show(f.topic)}</small><small>${text.show(f.responsible)} · ${f.due ? moment.show(f.due, {relative: true}) : 'موعد تعیین نشده'}</small></div>
    <div>${badge(b === 'late' ? BUCKETS.late : b === 'today' ? BUCKETS.today : 'باز', b === 'late' ? 'late' : '')}
    <button class="secondary" data-action="complete-followup" data-case="${f.case.id}" data-entry="${f.id}">ثبت نتیجه</button></div></div>`;
}
export function clientTable(rows, asOf) {
  return table({empty: 'پرونده‌ای با این فیلتر پیدا نشد.', rows, columns: [
    {title: 'کلاینت', cell: c => h`${caseLink(c)}<small>${name.show(c.phone, {kind: 'phone'})}</small>`, sort: c => c.name},
    {title: 'مشاوره', cell: c => h`${text.show(c.type)}<small>${c.date ? moment.show(c.date) : 'تاریخ نامعلوم'}</small>`, sort: c => c.date || ''},
    {title: 'وضعیت پرونده', cell: c => badge(c.status), sort: c => c.status},
    {title: 'پیگیری بعدی', cell: c => {
      const f = sortDue(Object.values(c.record.followups || {}).filter(isOpenFollowup))[0];
      return f ? h`${text.show(f.topic)}<small>${f.due ? moment.show(f.due, {relative: true}) : 'موعد تعیین نشده'}</small>` : 'پیگیری باز ندارد';
    }, sort: c => (sortDue(Object.values(c.record.followups || {}).filter(isOpenFollowup))[0] || {}).due || '9999'},
    {title: 'ثبت‌نام', cell: c => text.show(c.registration)},
  ]});
}
