// The calendar (تقویم هفته): the garden's series of classes and events (timetable/timetable.py, read through
// /api/calendar), as a week laid out like a school timetable, a month of the reader's own calendar, or a list of thirty
// days; each session noted, moved, called off or added, and each series' package of sessions. The follow-ups due and
// the card's payment day stand beside them, read from the dashboard's own data. Where the page stands is its address:
// #calendar?view=month&at=2026-10-08.
import { h } from '/toolbox/safe.js';
import * as moment from '/toolbox/moment.js';
import * as money from '/toolbox/money.js';
import * as number from '/toolbox/number.js';
import * as text from '/toolbox/text.js';
import * as choice from '/toolbox/choice.js';
import { settings, gardenerId } from '/toolbox/settings.js';
import { table } from '/toolbox/table.js';
import { form, collect, showErrors } from '/toolbox/form.js';
import { openDialog, isOpen } from '/toolbox/dialog.js';
import { badge, fact, count, isOpenFollowup } from '../common.js';
import { currencyOptions } from './cases.js';

const DAY = 86400000;
const HOURS = [6, 23];                                      // the timetable's first and last hour
const VIEWS = {week: 'هفته', month: 'ماه', list: 'فهرست'};
const pad = n => String(n).padStart(2, '0');
const utc = d => Date.UTC(+d.slice(0, 4), +d.slice(5, 7) - 1, +d.slice(8, 10));
const ymd = t => new Date(t).toISOString().slice(0, 10);
const addDays = (d, n) => ymd(utc(d) + n * DAY);
const isoWeekday = d => ((new Date(utc(d)).getUTCDay() + 6) % 7) + 1;         // 1 Monday … 7 Sunday
const firstWeekday = () => settings.lang === 'fa' ? 6 : 1;                     // a Persian week begins on Saturday
const weekStart = d => addDays(d, -((isoWeekday(d) - firstWeekday() + 7) % 7));
const minutes = t => +t.slice(0, 2) * 60 + +t.slice(3, 5);
const isDay = s => /^\d{4}-\d{2}-\d{2}$/.test(s || '');
const formats = {};
const format = (key, o) => (formats[settings.lang + key] ||= new Intl.DateTimeFormat(settings.lang, {...o, timeZone: 'UTC'}));
const weekdayName = d => format('wd', {weekday: 'long'}).format(new Date(utc(d) + DAY / 2));
const weekdayOfIso = n => weekdayName(addDays('2026-10-05', n - 1));          // 2026-10-05 is a Monday
// an ISO week day (2026-W45-7, as a weekly series' end is written) as its ISO day
function isoDay(s) {
  const m = /^(\d{4})-W(\d{2})-([1-7])$/.exec(s || '');
  if (!m) return s;
  const jan4 = utc(m[1] + '-01-04'), monday = jan4 - ((new Date(jan4).getUTCDay() + 6) % 7) * DAY;
  return ymd(monday + ((+m[2] - 1) * 7 + (+m[3] - 1)) * DAY);
}
// the month that holds `day`, in the reader's calendar: its first and last day, and its name
function monthOf(day) {
  if (settings.calendar === 'persian') {
    const p = moment.toPersian(day), first = moment.fromPersian(p.y, p.m, 1);
    const next = p.m === 12 ? moment.fromPersian(p.y + 1, 1, 1) : moment.fromPersian(p.y, p.m + 1, 1);
    return {first, last: addDays(next, -1), next};
  }
  const first = day.slice(0, 8) + '01', d = new Date(utc(first));
  d.setUTCMonth(d.getUTCMonth() + 1);
  return {first, last: addDays(ymd(d), -1), next: ymd(d)};
}
const monthName = m => new Intl.DateTimeFormat(`${settings.lang}-u-ca-${settings.calendar}`, {month: 'long', year: 'numeric', timeZone: 'UTC'})
  .format(new Date(utc(m.first) + DAY / 2));
// the day of its month a cell shows: in the reader's calendar, and the other one beside it
const dayOfMonth = d => number.plain(String(settings.calendar === 'persian' ? moment.toPersian(d).d : +d.slice(8)), {group: false});
function range(view, at) {
  if (view === 'month') { const m = monthOf(at), s = weekStart(m.first); return [s, addDays(s, 41), m]; }
  if (view === 'list') return [at, addDays(at, 30)];
  const s = weekStart(at);
  return [s, addDays(s, 6)];
}

const state = {view: 'week', at: '', cal: null};
const allSessions = cal => cal.series.flatMap(s => s.sessions.map(x => ({...x, title: s.title, category: s.category, place: s.place, with: s.with})));
// what else falls on a day: the follow-ups due, and the card's payment day
export function dueItems(d, from, to) {
  const out = [];
  for (const c of d.cases) for (const f of Object.values(c.record.followups || {})) {
    const day = f.due && f.due !== 'null' ? String(f.due).slice(0, 10) : '';
    if (isOpenFollowup(f) && day >= from && day <= to) out.push({day, label: 'پیگیری: ' + c.name, detail: f.topic || '', case: c.id});
  }
  for (const s of d.statements || []) {
    if (s.due_on && s.due_on >= from && s.due_on <= to) {
      const min = s.minimum_payment;
      out.push({day: s.due_on, label: 'سررسید کارت', detail: s.title + (min?.count ? ' · حداقل ' + money.text(min.count, min.unit) : '')});
    }
  }
  return out;
}
const dueChip = x => x.case
  ? h`<button type="button" class="due-chip" data-action="open-case" data-id="${x.case}" title="${x.detail}">${x.label}</button>`
  : h`<button type="button" class="due-chip" data-nav="posting" title="${x.detail}">${x.label}</button>`;
const timeRange = x => h`<bdi dir="ltr" class="w-time-range">${moment.showTime(x.start)}–${moment.showTime(x.end)}</bdi>`;
const stateBadge = (x, cal) => x.cancelled ? badge('لغو', 'late') : x.state === 'attended' ? badge(cal.states.attended || 'رفتم', 'done')
  : x.state === 'missed' ? badge(cal.states.missed || 'نرفتم', 'late') : '';
const sessionAttrs = x => h`data-action="cal-session" data-series="${x.series}" data-day="${x.day}" data-extra="${x.extra || ''}"`;
const sessionBlock = (x, cal) => h`<button type="button" class="session cat-${x.category}${x.cancelled ? ' cancelled' : ''}" ${sessionAttrs(x)}><b>${text.show(x.title)}</b><small>${timeRange(x)}</small>${x.place ? h`<small>${text.show(x.place)}</small>` : ''}${stateBadge(x, cal)}</button>`;

function weekGrid(ctx, cal, from) {
  const days = [...Array(7).keys()].map(n => addDays(from, n)), asOf = ctx.data.asOf;
  const sessions = allSessions(cal).filter(x => days.includes(x.day)), due = dueItems(ctx.data, days[0], days[6]);
  const slots = (HOURS[1] - HOURS[0]) * 4;                                     // a row a quarter of an hour
  const rowOf = t => Math.max(1, Math.min(slots + 1, Math.round((minutes(t) - HOURS[0] * 60) / 15) + 1));
  const outside = x => minutes(x.start) < HOURS[0] * 60 || minutes(x.end) > HOURS[1] * 60;
  return h`<div class="timetable" data-rows="auto auto repeat(${slots},11px)"><div class="tt-corner"></div>
    ${days.map((d, i) => h`<div class="tt-day${d === asOf ? ' today' : ''}" data-gc="${i + 2}"><b>${weekdayName(d)}</b><small>${moment.show(d, {style: 'long', year: false})}</small><small dir="ltr">${d.slice(5)}</small></div>`)}
    <div class="tt-corner tt-allday">کارها</div>${days.map((d, i) => h`<div class="tt-allday" data-gc="${i + 2}">${due.filter(x => x.day === d).map(dueChip)}</div>`)}
    ${[...Array(HOURS[1] - HOURS[0]).keys()].map(k => h`<div class="tt-hour" data-gr="${k * 4 + 3} / span 4">${moment.showTime(pad(HOURS[0] + k) + ':00')}</div>`)}
    ${days.map((d, i) => h`<div class="tt-col" data-gc="${i + 2}" data-gr="3 / span ${slots}"></div>`)}
    ${sessions.map(x => h`<div class="tt-slot" data-gc="${days.indexOf(x.day) + 2}" data-gr="${rowOf(x.start) + 2} / ${Math.max(rowOf(x.end), rowOf(x.start) + 2) + 2}">${sessionBlock(x, cal)}</div>`)}</div>
    ${sessions.some(outside) ? h`<p class="muted">جلسه‌ای بیرون از ساعت‌های جدول هست؛ آن را در «فهرست» ببینید.</p>` : ''}`;
}

function monthGrid(ctx, cal, from, m) {
  const days = [...Array(42).keys()].map(n => addDays(from, n)), asOf = ctx.data.asOf;
  const sessions = allSessions(cal), due = dueItems(ctx.data, days[0], days[41]);
  return h`<div class="month-grid">${days.slice(0, 7).map(d => h`<div class="mg-head">${weekdayName(d)}</div>`)}${days.map(d =>
    h`<div class="mg-day${d >= m.first && d <= m.last ? '' : ' other'}${d === asOf ? ' today' : ''}"><small>${dayOfMonth(d)} <span dir="ltr">${d.slice(8)}</span></small>${
      sessions.filter(x => x.day === d).sort((a, b) => a.start.localeCompare(b.start)).map(x => sessionBlock(x, cal))}${due.filter(x => x.day === d).map(dueChip)}</div>`)}</div>`;
}

export function agenda(ctx, cal, from, to) {
  const items = [...allSessions(cal).filter(x => x.day >= from && x.day <= to).map(x => ({...x, kind: 'session'})),
    ...dueItems(ctx.data, from, to).map(x => ({...x, kind: 'due', start: ''}))].sort((a, b) => (a.day + a.start).localeCompare(b.day + b.start));
  return table({rows: items, empty: 'در این ۳۰ روز چیزی نیست.', cls: 'cal-agenda', columns: [
    {title: 'روز', cell: x => h`${moment.show(x.day, {style: 'weekday', year: false})}<small>${moment.show(x.day, {calendar: 'gregory', lang: 'en'})}</small>`},
    {title: 'ساعت', cell: x => x.kind === 'session' ? timeRange(x) : ''},
    {title: 'چه', cell: x => x.kind === 'session' ? h`<button type="button" class="text-button" ${sessionAttrs(x)}>${text.show(x.title)}</button>`
      : h`${dueChip(x)}<small>${text.show(x.detail)}</small>`},
    {title: 'کجا / با چه کسی', cell: x => text.show([x.place, x.with].filter(Boolean).join(' · '), {empty: ''})},
    {title: 'وضعیت', cell: x => x.kind === 'session' ? h`${stateBadge(x, cal)}${x.note ? h`<small>${text.show(x.note)}</small>` : ''}` : ''},
  ]});
}

const packageCell = p => !p ? '—' : h`${count(p.used)} از ${count(p.sessions)} جلسه${p.left <= 1 ? h` ${badge(p.left <= 0 ? 'تمام شد' : 'یک جلسه مانده', 'late')}` : ''}
  <small>${p.from ? moment.show(p.from) : ''}${p.from && p.until ? ' تا ' : ''}${p.until ? moment.show(p.until) : ''}${p.price ? h`${p.from || p.until ? ' · ' : ''}${money.show(p.price.count, p.price.unit)}` : ''}</small>`;
function seriesList(cal) {
  return h`<section class="panel"><div class="panel-head"><div><h2>کلاس‌ها و رویدادهای تکراری</h2><p>هر سری یک بار تعریف می‌شود و جلسه‌هایش از قاعدهٔ تکرار خوانده می‌شوند. لغو یک جلسه، آن روز را از تکرار کنار می‌گذارد.</p></div></div>
    ${table({rows: cal.series, empty: 'هنوز کلاسی ثبت نشده است. با «کلاس یا رویداد» اولی را بساز.', cls: 'cal-series', columns: [
      {title: 'عنوان', cell: s => h`${text.show(s.title)}${s.note ? h`<small>${text.show(s.note)}</small>` : ''}`, sort: s => s.title},
      {title: 'دسته', cell: s => h`<span class="dot cat-${s.category}"></span>${choice.show(s.category, cal.categories)}`, sort: s => s.category},
      {title: 'تکرار', cell: s => h`${text.show(s.repeat)}${s.every?.to ? h`<small>تا ${moment.show(s.every.in === 'iso-week' ? isoDay(s.every.to) : s.every.to)}</small>` : ''}`},
      {title: 'ساعت', cell: s => s.base ? timeRange(s.base) : ''},
      {title: 'کجا', cell: s => text.show([s.place, s.with].filter(Boolean).join(' · '))},
      {title: 'بستهٔ جلسات', cell: s => packageCell(s.package)},
      {title: '', cell: s => h`<div class="cal-row-actions"><button type="button" class="text-button" data-action="cal-edit" data-series="${s.id}">ویرایش</button>
        <button type="button" class="text-button" data-action="cal-package" data-series="${s.id}">بسته</button><button type="button" class="text-button" data-action="cal-extra" data-series="${s.id}">جلسهٔ اضافه</button></div>`},
    ]})}</section>`;
}

// ---------------------------------------------------------------------------------------------- forms
const REPEATS = {none: 'یک‌بار', daily: 'روزانه', weekly: 'هفتگی', monthly: 'ماهانه (همان روزِ ماه)'};
const ENDS = {never: 'بدون پایان', until: 'تا تاریخ', times: 'بعد از چند بار'};
const WEEKDAYS = [6, 7, 1, 2, 3, 4, 5];                                      // ISO week days, from Saturday
const SAVE_NOTE = 'ذخیره از دروازهٔ دفتر می‌گذرد؛ اگر همین پرونده در همین دقیقه ذخیره شده باشد، تا یک دقیقه طول می‌کشد.';
// a dialog over another (a session's, opening its series) takes its place
const fresh = () => { if (isOpen()) document.querySelector('dialog.w-dialog')?.close(); };
const whole = (v, max) => /^\d+$/.test(v) && +v >= 1 && +v <= max;
const endsAfter = (values, errors) => { if (values.start && values.end && values.end <= values.start) errors.end = 'پایان باید بعد از شروع باشد.'; };

// Only the controls the chosen repetition asks for are shown; what is hidden is disabled and neither checked nor sent.
function showRecurrence(f) {
  const repeat = f.elements.namedItem('repeat').value, ends = f.elements.namedItem('ends').value;
  const n = number.take(f.elements.namedItem('interval').value).value;
  const on = {interval: repeat === 'daily' || repeat === 'weekly', weekdays: repeat === 'weekly', ends: repeat !== 'none',
    until: repeat !== 'none' && ends === 'until', times: repeat !== 'none' && ends === 'times', note: repeat === 'weekly' && +n > 1};
  for (const [key, shown] of Object.entries(on)) {
    for (const el of f.querySelectorAll(`[data-field="${key}"],[data-rec="${key}"]`)) {
      el.hidden = !shown;
      el.querySelectorAll('input,select').forEach(i => { i.disabled = !shown; });
    }
  }
  const label = f.querySelector('[data-field="interval"] .w-label');
  if (label) label.textContent = repeat === 'daily' ? 'هر چند روز یک‌بار' : 'هر چند هفته یک‌بار';
  return on;
}

function openSeries(ctx, cal, id = '') {
  const s = id ? cal.series.find(x => x.id === id) : null;
  if (id && !s) return;
  const rec = s ? s.form : {repeat: 'weekly', interval: 1, weekdays: [], ends: 'never', until: '', times: ''};
  if (rec.repeat === 'other') throw new Error('این تکرار را فرم تقویم نمی‌شناسد؛ آن را از پرونده ویرایش کنید.');
  const head = [
    {name: 'original', type: 'hidden'},
    {name: 'title', label: 'عنوان', required: true, max: 120, wide: true},
    {name: 'category', label: 'دسته', type: 'choice', options: cal.categories, required: true},
    {name: 'start', label: 'ساعت شروع', type: 'time', required: true},
    {name: 'end', label: 'ساعت پایان', type: 'time', required: true},
    {name: 'from', label: s ? 'نخستین جلسه' : 'از تاریخ', type: 'date', required: true},
  ];
  const repeat = [
    {name: 'repeat', label: 'تکرار', type: 'choice', options: REPEATS, required: true},
    {name: 'interval', label: 'هر چند هفته یک‌بار', type: 'number', required: true},
    {name: 'ends', label: 'پایان تکرار', type: 'choice', options: ENDS, required: true},
    {name: 'until', label: 'تا تاریخ', type: 'date', required: true},
    {name: 'times', label: 'چند بار در کل', type: 'number', required: true},
  ];
  const tail = [
    {name: 'place', label: 'کجا', max: 300, hint: 'نام استودیو یا نشانی'},
    {name: 'with', label: 'با چه کسی', max: 300, hint: 'مربی یا همراه'},
    {name: 'note', label: 'یادداشت', type: 'lines', max: 300},
  ];
  const values = {original: id, title: s?.title || '', category: s?.category || Object.keys(cal.categories)[0], start: s?.base?.start || '18:00',
    end: s?.base?.end || '19:30', from: s?.base?.day || ctx.data.asOf, repeat: rec.repeat, interval: String(rec.interval || 1), ends: rec.ends || 'never',
    until: rec.until || '', times: rec.times ? String(rec.times) : '', place: s?.place || '', with: s?.with || '', note: s?.note || ''};
  const weekdays = h`<fieldset class="weekdays" data-rec="weekdays"><legend>روزهای هفته</legend>${WEEKDAYS.map(n =>
    h`<label><input type="checkbox" name="wd" value="${n}"${(rec.weekdays || []).map(String).includes(String(n)) ? h` checked` : ''}> ${weekdayOfIso(n)}</label>`)}<small class="w-field-error" hidden></small></fieldset>`;
  const body = h`${form(head, values)}<fieldset class="wide recurrence"><legend>تکرار</legend>${form(repeat, values)}${weekdays}
    <p class="muted" data-rec="note">برای هر چند هفته یک‌بار، یک روز هفته انتخاب کنید.</p></fieldset>${form(tail, values)}`;
  fresh();
  const d = openDialog({title: s ? 'ویرایش «' + s.title + '»' : 'کلاس یا رویداد تازه', body, wide: true,
    note: s ? 'تغییر ساعت یا روزها روی همهٔ جلسه‌های این سری اثر دارد. برای جابه‌جایی فقط یک جلسه، روی همان جلسه در تقویم بزنید. برای تغییر از یک تاریخ به بعد، این سری را با «تا تاریخ» ببند و سری تازه بساز.' : SAVE_NOTE,
    onSubmit: async f => {
      const on = showRecurrence(f);
      const fields = [...head, ...repeat.filter(x => x.name === 'repeat' || on[x.name]), ...tail];
      const {values: v, errors} = collect(f, fields);
      endsAfter(v, errors);
      if (on.interval && v.interval && !whole(v.interval, 52)) errors.interval = 'عددی درست از ۱ تا ۵۲.';
      if (on.times && v.times && !whole(v.times, 500)) errors.times = 'عددی درست از ۱ تا ۵۰۰.';
      const wd = on.weekdays ? [...f.querySelectorAll('[name=wd]:checked')].map(i => i.value) : [];
      const wdError = on.weekdays && !wd.length ? 'روزهای هفته را انتخاب کنید.' : '';
      const box = f.querySelector('[data-rec="weekdays"]'), small = box.querySelector('.w-field-error');
      box.classList.toggle('w-invalid', Boolean(wdError)); small.textContent = wdError; small.hidden = !wdError;
      if (!showErrors(f, errors) || wdError) return false;
      const out = {original: v.original, title: v.title, category: v.category, start: v.start, end: v.end, from: v.from, repeat: v.repeat,
        weekdays: JSON.stringify(wd), place: v.place, with: v.with, note: v.note};
      for (const k of ['interval', 'ends', 'until', 'times']) if (on[k]) out[k] = v[k];
      await ctx.save('cal-series', s ? s.id : gardenerId(), out);
      return true;
    }});
  const f = d.querySelector('form');
  showRecurrence(f);
  f.addEventListener('change', e => { if (['repeat', 'ends'].includes(e.target.name)) showRecurrence(f); });
  f.addEventListener('input', e => { if (e.target.name === 'interval') showRecurrence(f); });
}

function openSession(ctx, cal, series, day, extra) {
  const s = cal.series.find(x => x.id === series), x = s?.sessions.find(y => y.day === day && (y.extra || '') === (extra || ''));
  if (!x) return;
  const acts = {attended: 'رفتم', missed: 'نرفتم', ...(x.cancelled ? {} : {move: s.every || extra ? 'تغییر روز یا ساعتِ فقط همین جلسه' : 'تغییر روز یا ساعت'}),
    ...(x.state || x.note ? {clear: 'پاک کردن یادداشت'} : {}), ...(!extra && s.every ? (x.cancelled ? {restore: 'بازگرداندن جلسه'} : {cancel: 'لغو این جلسه'}) : {})};
  const top = [{name: 'day', type: 'hidden'}, {name: 'extra', type: 'hidden'}, {name: 'action', label: 'چه شد؟', type: 'choice', options: acts, required: true, wide: true}];
  const move = [{name: 'to_day', label: 'روز', type: 'date', required: true}, {name: 'start', label: 'شروع', type: 'time', required: true},
    {name: 'end', label: 'پایان', type: 'time', required: true}];
  const note = [{name: 'note', label: 'یادداشت', type: 'lines', max: 500, hint: 'مثلاً علت لغو یا چیزی که در کلاس گذشت'}];
  const values = {day, extra: extra || '', action: 'attended', to_day: day, start: x.start, end: x.end};
  const body = h`<div class="facts wide">${fact('کلاس', s.title)}${fact('روز', moment.show(day, {style: 'weekday'}))}${fact('ساعت', timeRange(x))}
      ${fact('کجا', [s.place, s.with].filter(Boolean).join(' · '))}${fact('وضعیت', x.cancelled ? 'لغو شده' : (cal.states[x.state] || 'ثبت نشده'))}${x.note ? fact('یادداشت', x.note) : ''}</div>
    <div class="wide cal-bar"><button type="button" class="secondary" data-action="cal-edit" data-series="${s.id}">ویرایش رویداد${s.every ? ' و تکرارش (همهٔ جلسه‌ها)' : ''}</button></div>
    ${form(top, values)}<fieldset class="wide move" data-rec="move"><legend>${s.every || extra ? 'فقط همین جلسه' : 'روز و ساعت تازه'}</legend>${form(move, values)}</fieldset>${form(note, values)}`;
  fresh();
  const d = openDialog({title: 'جلسهٔ ' + s.title, body, wide: true,
    note: s.every ? 'لغو، آن روز را از تکرار کنار می‌گذارد؛ «بازگرداندن» آن را برمی‌گرداند. جابه‌جایی همین جلسه، آن روز را لغو و جلسه را در روز و ساعت تازه ثبت می‌کند؛ بقیهٔ جلسه‌ها دست نمی‌خورند.' : SAVE_NOTE,
    onSubmit: async f => {
      const moving = f.elements.namedItem('action').value === 'move';
      const {values: v, errors} = collect(f, [...top, ...(moving ? move : []), ...note]);
      if (moving) endsAfter(v, errors);
      if (!showErrors(f, errors)) return false;
      await ctx.save('cal-session', s.id, {day: v.day, extra: v.extra, action: v.action, note: v.note, ...(moving ? {to_day: v.to_day, start: v.start, end: v.end} : {})});
      return true;
    }});
  const f = d.querySelector('form'), box = f.querySelector('[data-rec="move"]');
  const sync = () => { box.hidden = box.disabled = f.elements.namedItem('action').value !== 'move'; };
  sync();
  f.addEventListener('change', e => { if (e.target.name === 'action') sync(); });
}

function openExtra(ctx, cal, series) {
  const s = cal.series.find(x => x.id === series);
  if (!s) return;
  const fields = [{name: 'day', label: 'روز', type: 'date', required: true}, {name: 'start', label: 'شروع', type: 'time', required: true},
    {name: 'end', label: 'پایان', type: 'time', required: true}];
  fresh();
  openDialog({title: 'جلسهٔ اضافهٔ ' + s.title, note: 'جلسهٔ جبرانی یا اضافه، بیرون از تکرار همیشگی.',
    body: form(fields, {day: ctx.data.asOf, start: s.base?.start || '18:00', end: s.base?.end || '19:30'}), onSubmit: async f => {
      const {values: v, errors} = collect(f, fields);
      endsAfter(v, errors);
      if (!showErrors(f, errors)) return false;
      await ctx.save('cal-extra', s.id, v);
      return true;
    }});
}

function openPackage(ctx, cal, series) {
  const s = cal.series.find(x => x.id === series);
  if (!s) return;
  const p = s.package || {};
  const fields = [{name: 'sessions', label: 'تعداد جلسه‌ها', type: 'number', required: true, hint: 'صفر یعنی حذف بسته.'},
    {name: 'from', label: 'از', type: 'date'}, {name: 'until', label: 'تا', type: 'date'},
    {name: 'count', label: 'بها', type: 'number'}, {name: 'unit', label: 'ارز', type: 'choice', options: currencyOptions(ctx.data), required: true},
    {name: 'note', label: 'یادداشت', type: 'lines', max: 300}];
  fresh();
  openDialog({title: 'بستهٔ جلسات ' + s.title,
    note: 'جلسه‌هایی که «رفتم» خورده‌اند از بسته کم می‌شوند. پرداخت بسته را از صفحهٔ خریدهای کارت به حساب و مرکز هزینهٔ مربوط ببرید. صفر یعنی حذف بسته.',
    body: form(fields, {sessions: p.sessions || '', from: p.from || '', until: p.until || '', count: p.price?.count || '', unit: p.price?.unit || 'TRY', note: p.note || ''}),
    onSubmit: async f => {
      const {values: v, errors} = collect(f, fields.filter(x => x.name !== 'count'));
      if (v.sessions && !/^\d{1,3}$/.test(v.sessions)) errors.sessions = 'تعداد جلسه‌ها عددی درست تا ۹۹۹ است؛ صفر یعنی حذف بسته.';
      const price = money.take(f.elements.namedItem('count').value, v.unit, {positive: true});   // at the chosen currency's places
      if (price.error) errors.count = price.error;
      if (v.from && v.until && v.until < v.from) errors.until = 'پایان پیش از آغاز است.';
      if (!showErrors(f, errors)) return false;
      await ctx.save('cal-package', s.id, {sessions: v.sessions, from: v.from, until: v.until, count: price.value, unit: v.unit, note: v.note});
      return true;
    }});
}

// ---------------------------------------------------------------------------------------------- the page
const go = (ctx, view, at) => ctx.open(ctx.part === 'calendar' ? ctx.page.id : 'calendar', at ? {view, at, part: 'calendar'} : {view, part: 'calendar'});
export const actions = {
  'cal-view': (el, ctx) => go(ctx, el.dataset.view, state.at === ctx.data.asOf ? '' : state.at),
  'cal-today': (el, ctx) => go(ctx, state.view, ''),
  'cal-step': (el, ctx) => {
    const forward = el.dataset.step === '1';
    if (state.view === 'month') { const m = monthOf(state.at); go(ctx, 'month', forward ? m.next : monthOf(addDays(m.first, -1)).first); }
    else go(ctx, state.view, addDays(state.at, (forward ? 1 : -1) * (state.view === 'list' ? 30 : 7)));
  },
  'cal-new': (el, ctx) => openSeries(ctx, state.cal),
  'cal-edit': (el, ctx) => openSeries(ctx, state.cal, el.dataset.series),
  'cal-session': (el, ctx) => openSession(ctx, state.cal, el.dataset.series, el.dataset.day, el.dataset.extra),
  'cal-extra': (el, ctx) => openExtra(ctx, state.cal, el.dataset.series),
  'cal-package': (el, ctx) => openPackage(ctx, state.cal, el.dataset.series),
};

export default {
  id: 'calendar', nav: 'تقویم', title: 'تقویم هفته', actions,
  async render(ctx) {
    const p = ctx.params, view = Object.hasOwn(VIEWS, p.get('view') || '') ? p.get('view') : 'week';
    const at = isDay(p.get('at')) ? p.get('at') : ctx.data.asOf;
    const [from, to, m] = range(view, at);
    const cal = await ctx.calendar(from, to);
    Object.assign(state, {view, at, cal});
    const label = view === 'month'
      ? h`${monthName(m)}<small dir="ltr">${m.first} – ${m.last}</small>`
      : h`${moment.show(from, {style: 'long', year: false})} تا ${moment.show(to, {style: 'long'})}`;
    const head = h`<div class="panel-head cal-head"><div class="cal-bar"><button type="button" class="secondary" data-action="cal-step" data-step="-1" aria-label="قبلی">‹</button>
      <button type="button" class="secondary" data-action="cal-today">امروز</button><button type="button" class="secondary" data-action="cal-step" data-step="1" aria-label="بعدی">›</button>
      <b class="cal-label">${label}</b></div><div class="cal-bar">${Object.entries(VIEWS).map(([k, n]) =>
        h`<button type="button" class="${k === view ? 'primary' : 'secondary'}" data-action="cal-view" data-view="${k}"${k === view ? h` aria-pressed="true"` : ''}>${n}</button>`)}
      <button type="button" class="primary" data-action="cal-new">＋ کلاس یا رویداد</button></div></div>`;
    const body = view === 'month' ? monthGrid(ctx, cal, from, m) : view === 'list' ? agenda(ctx, cal, from, to) : weekGrid(ctx, cal, from);
    return h`<section class="panel cal-panel">${head}${body}</section>${seriesList(cal)}`;
  },
};
