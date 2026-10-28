'use strict';
// The garden's calendar (timetable/timetable.py, read through /api/calendar): a week laid out like a school timetable, a
// month, and a list; her yoga classes and her own recurring events, each session noted, called off or added. The
// follow-ups due and the card's payment day are shown beside them, read from the dashboard's own data.
let cal = null, calLoading = false, calError = '', calView = 'week', calAnchor = '', calKey = '';
const DAY_MS = 86400000;
const weekNames = ['شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنج‌شنبه', 'جمعه'];
const isoNames = {1: 'دوشنبه', 2: 'سه‌شنبه', 3: 'چهارشنبه', 4: 'پنج‌شنبه', 5: 'جمعه', 6: 'شنبه', 7: 'یکشنبه'};
const HOURS = [6, 23];
const ymd = t => new Date(t).toISOString().slice(0, 10);
const utc = d => Date.UTC(+d.slice(0, 4), +d.slice(5, 7) - 1, +d.slice(8, 10));
const addDays = (d, n) => ymd(utc(d) + n * DAY_MS);
const weekStart = d => addDays(d, -((new Date(utc(d)).getUTCDay() + 1) % 7));          // Saturday
const jalali = (d, o = {day: 'numeric', month: 'long'}) => new Date(utc(d) + 12 * 3600000).toLocaleDateString('fa-IR', o);
const minutes = t => +t.slice(0, 2) * 60 + +t.slice(3, 5);

function calRange() {
  const a = calAnchor || data.asOf;
  if (calView === 'month') { const first = a.slice(0, 8) + '01'; const s = weekStart(first); return [s, addDays(s, 41)]; }
  if (calView === 'list') return [a, addDays(a, 30)];
  const s = weekStart(a); return [s, addDays(s, 6)];
}
async function loadCalendar() {
  const [from, to] = calRange(); calLoading = true;
  try {
    const r = await fetch(`/api/calendar?from=${from}&to=${to}`, {cache: 'no-store'});
    const result = await r.json();
    if (!r.ok) throw Error(result.error || 'خواندن تقویم ممکن نشد.');
    cal = result; calKey = from + '|' + to + '|' + data.head; calError = '';
  } catch (e) { calError = e.message; } finally { calLoading = false; }
  if (tab === 'calendar') render();
}
function calReady() {
  const [from, to] = calRange();
  if (cal && calKey === from + '|' + to + '|' + data.head && !calError) return true;
  if (!calLoading) loadCalendar();
  return false;
}
function allSessions() {
  return cal.series.flatMap(s => s.sessions.map(x => ({...x, title: s.title, category: s.category, place: s.place, with: s.with})));
}
function dueItems(from, to) {
  const out = [];
  for (const c of data.cases) for (const [id, f] of Object.entries(c.record.followups || {})) if (f.status !== 'انجام‌شده' && f.due && f.due >= from && f.due <= to) out.push({day: f.due, label: 'پیگیری: ' + c.name, detail: f.topic, client: c.id});
  for (const s of data.statements || []) if (s.due_on && s.due_on >= from && s.due_on <= to) out.push({day: s.due_on, label: 'سررسید کارت', detail: s.title + ' · حداقل ' + Number(s.minimum_payment?.count || 0).toLocaleString('fa-IR')});
  return out;
}
const stateBadge = x => x.cancelled ? badge('لغو', 'late') : x.state === 'attended' ? badge('رفتم', 'done') : x.state === 'missed' ? badge('نرفتم', 'late') : '';
function sessionBlock(x) {
  return `<button class="session cat-${esc(x.category)}${x.cancelled ? ' cancelled' : ''}" data-cal="session" data-series="${esc(x.series)}" data-day="${esc(x.day)}" data-extra="${esc(x.extra || '')}"><b>${esc(x.title)}</b><small dir="ltr">${esc(x.start)}–${esc(x.end)}</small>${x.place ? `<small>${esc(x.place)}</small>` : ''}${stateBadge(x)}</button>`;
}

function renderCalendar() {
  if (!calReady()) return `<section class="panel empty">${calError ? esc(calError) : 'در حال خواندن تقویم…'}</section>`;
  const [from, to] = calRange();
  const head = `<div class="panel-head cal-head"><div class="header-actions"><button class="secondary" data-cal="prev" aria-label="قبلی">‹</button><button class="secondary" data-cal="today">امروز</button><button class="secondary" data-cal="next" aria-label="بعدی">›</button><b>${calView === 'month' ? jalali((calAnchor || data.asOf), {month: 'long', year: 'numeric'}) + ' · ' + esc((calAnchor || data.asOf).slice(0, 7)) : jalali(from) + ' تا ' + jalali(to)}</b></div><div class="header-actions">${[['week', 'هفته'], ['month', 'ماه'], ['list', 'فهرست']].map(([k, n]) => `<button class="${k === calView ? 'primary' : 'secondary'}" data-cal="view" data-view="${k}">${n}</button>`).join('')}<button class="primary" data-cal="new">＋ کلاس یا رویداد</button></div></div>`;
  const body = calView === 'month' ? monthGrid(from) : calView === 'list' ? agenda(from, to) : weekGrid(from);
  return `<section class="panel">${head}${body}</section>${seriesList()}`;
}
function weekGrid(from) {
  const days = [...Array(7).keys()].map(n => addDays(from, n));
  const sessions = allSessions(); const due = dueItems(days[0], days[6]);
  const slots = (HOURS[1] - HOURS[0]) * 4;                                   // a row a quarter of an hour
  const rowOf = t => Math.max(1, Math.min(slots + 1, Math.round((minutes(t) - HOURS[0] * 60) / 15) + 1));
  return `<div class="timetable" data-rows="auto auto repeat(${slots},11px)"><div class="tt-corner"></div>${days.map((d, i) => `<div class="tt-day${d === data.asOf ? ' today' : ''}" data-gc="${i + 2}"><b>${weekNames[i]}</b><small>${jalali(d)}</small><small dir="ltr">${d.slice(5)}</small></div>`).join('')}
  <div class="tt-corner tt-allday">کارها</div>${days.map((d, i) => `<div class="tt-allday" data-gc="${i + 2}">${due.filter(x => x.day === d).map(x => `<button class="due-chip" ${x.client ? `data-client="${esc(x.client)}"` : ''} title="${esc(x.detail)}">${esc(x.label)}</button>`).join('')}</div>`).join('')}
  ${[...Array(HOURS[1] - HOURS[0]).keys()].map(h => `<div class="tt-hour" data-gr="${h * 4 + 3} / span 4" dir="ltr">${String(HOURS[0] + h).padStart(2, '0')}:00</div>`).join('')}
  ${days.map((d, i) => `<div class="tt-col" data-gc="${i + 2}" data-gr="3 / span ${slots}"></div>`).join('')}
  ${sessions.filter(x => days.includes(x.day)).map(x => `<div class="tt-slot" data-gc="${days.indexOf(x.day) + 2}" data-gr="${rowOf(x.start) + 2} / ${Math.max(rowOf(x.end), rowOf(x.start) + 2) + 2}">${sessionBlock(x)}</div>`).join('')}</div>
  ${sessions.some(x => days.includes(x.day) && (minutes(x.start) < HOURS[0] * 60 || minutes(x.end) > HOURS[1] * 60)) ? '<p class="muted">جلسه‌ای بیرون از ساعت‌های جدول هست؛ آن را در «فهرست» ببینید.</p>' : ''}`;
}
function monthGrid(from) {
  const days = [...Array(42).keys()].map(n => addDays(from, n));
  const month = (calAnchor || data.asOf).slice(0, 7);
  const sessions = allSessions(); const due = dueItems(days[0], days[41]);
  return `<div class="month-grid">${weekNames.map(n => `<div class="mg-head">${n}</div>`).join('')}${days.map(d => `<div class="mg-day${d.slice(0, 7) === month ? '' : ' other'}${d === data.asOf ? ' today' : ''}"><small>${jalali(d, {day: 'numeric'})} <span dir="ltr">${d.slice(8)}</span></small>${sessions.filter(x => x.day === d).sort((a, b) => a.start.localeCompare(b.start)).map(sessionBlock).join('')}${due.filter(x => x.day === d).map(x => `<button class="due-chip" ${x.client ? `data-client="${esc(x.client)}"` : ''} title="${esc(x.detail)}">${esc(x.label)}</button>`).join('')}</div>`).join('')}</div>`;
}
function agenda(from, to) {
  const items = [...allSessions().map(x => ({...x, kind: 'session'})), ...dueItems(from, to).map(x => ({...x, kind: 'due', start: ''}))].sort((a, b) => (a.day + a.start).localeCompare(b.day + b.start));
  return items.length ? `<div class="table-scroll"><table><thead><tr><th>روز</th><th>ساعت</th><th>چه</th><th>کجا / با چه کسی</th><th>وضعیت</th></tr></thead><tbody>${items.map(x => `<tr><td>${esc(jalali(x.day, {weekday: 'long', day: 'numeric', month: 'long'}))}<small dir="ltr">${esc(x.day)}</small></td><td dir="ltr">${x.kind === 'session' ? esc(x.start + '–' + x.end) : ''}</td><td>${x.kind === 'session' ? `<button class="text-button" data-cal="session" data-series="${esc(x.series)}" data-day="${esc(x.day)}" data-extra="${esc(x.extra || '')}">${esc(x.title)}</button>` : esc(x.label) + `<small>${esc(x.detail)}</small>`}</td><td>${esc([x.place, x.with].filter(Boolean).join(' · '))}</td><td>${x.kind === 'session' ? stateBadge(x) + (x.note ? `<small>${esc(x.note)}</small>` : '') : ''}</td></tr>`).join('')}</tbody></table></div>` : '<div class="empty">در این ۳۰ روز چیزی نیست.</div>';
}
function seriesList() {
  return `<section class="panel"><div class="panel-head"><div><h2>کلاس‌ها و رویدادهای تکراری</h2><p>هر سری یک بار تعریف می‌شود و جلسه‌هایش از قاعدهٔ تکرار خوانده می‌شوند. لغو یک جلسه، آن روز را از تکرار کنار می‌گذارد.</p></div></div>${cal.series.length ? `<div class="table-scroll"><table><thead><tr><th>عنوان</th><th>دسته</th><th>تکرار</th><th>ساعت</th><th>کجا</th><th>بستهٔ جلسات</th><th></th></tr></thead><tbody>${cal.series.map(s => `<tr><td>${esc(s.title)}${s.note ? `<small>${esc(s.note)}</small>` : ''}</td><td><span class="dot cat-${esc(s.category)}"></span>${esc(cal.categories[s.category] || s.category)}</td><td>${esc(s.repeat)}${s.every?.to ? `<small>تا ${esc(s.every.in === 'iso-week' ? isoDay(s.every.to) : s.every.to)}</small>` : ''}</td><td dir="ltr">${s.base ? esc(s.base.start + '–' + s.base.end) : ''}</td><td>${esc([s.place, s.with].filter(Boolean).join(' · '))}</td><td>${s.package ? `${fa(s.package.used)} از ${fa(s.package.sessions)} جلسه${s.package.left <= 1 ? ' ' + badge(s.package.left <= 0 ? 'تمام شد' : 'یک جلسه مانده', 'late') : ''}<small>${esc([s.package.from, s.package.until].filter(Boolean).join(' تا '))}${s.package.price ? ' · ' + Number(s.package.price.count).toLocaleString('fa-IR') + ' ' + esc(s.package.price.unit) : ''}</small>` : '—'}</td><td class="actions"><button class="text-button" data-cal="edit" data-series="${esc(s.id)}">ویرایش</button><button class="text-button" data-cal="package" data-series="${esc(s.id)}">بسته</button><button class="text-button" data-cal="extra" data-series="${esc(s.id)}">جلسهٔ اضافه</button></td></tr>`).join('')}</tbody></table></div>` : '<div class="empty">هنوز کلاسی ثبت نشده است. با «کلاس یا رویداد» اولی را بساز.</div>'}</section>`;
}
function isoDay(s) { const m = /^(\d{4})-W(\d{2})-([1-7])$/.exec(s); if (!m) return s; const jan4 = utc(m[1] + '-01-04'); const monday = jan4 - ((new Date(jan4).getUTCDay() + 6) % 7) * DAY_MS; return ymd(monday + ((+m[2] - 1) * 7 + (+m[3] - 1)) * DAY_MS); }

// ---------------------------------------------------------------------------------------------- forms
const REPEATS = [['none', 'یک‌بار'], ['daily', 'روزانه'], ['weekly', 'هفتگی'], ['monthly', 'ماهانه (همان روزِ ماه)']];
const ENDS = [['never', 'بدون پایان'], ['until', 'تا تاریخ'], ['times', 'بعد از چند بار']];
function recurrenceControls(f) {
  const opt = (list, at) => list.map(([k, n]) => `<option value="${k}"${at === k ? ' selected' : ''}>${n}</option>`).join('');
  return `<fieldset class="wide recurrence" id="cal-recurrence"><legend>تکرار</legend>
  <label>تکرار *<select name="repeat" id="cal-repeat">${opt(REPEATS, f.repeat)}</select></label>
  <label data-rec="interval"><span>هر چند <span id="cal-interval-unit"></span></span><input type="number" name="interval" min="1" max="52" value="${esc(f.interval || 1)}"></label>
  <fieldset class="weekdays" data-rec="weekdays"><legend>روزهای هفته</legend>${[6, 7, 1, 2, 3, 4, 5].map(n => `<label><input type="checkbox" data-wd="${n}"${f.weekdays.includes(String(n)) ? ' checked' : ''}> ${isoNames[n]}</label>`).join('')}</fieldset>
  <label data-rec="ends">پایان تکرار<select name="ends" id="cal-ends">${opt(ENDS, f.ends)}</select></label>
  <label data-rec="until">تا تاریخ *<input type="date" name="until" value="${esc(f.until || '')}"></label>
  <label data-rec="times">چند بار در کل *<input type="number" name="times" min="1" max="500" value="${esc(f.times || '')}"></label>
  <p class="muted" data-rec="note" id="cal-rec-note"></p></fieldset>`;
}
// Only the controls the chosen repetition asks for are shown; what is hidden is disabled, so it is neither checked
// by the browser nor sent.
function showRecurrence() {
  const box = $('cal-recurrence'); if (!box) return;
  const repeat = $('cal-repeat').value, ends = $('cal-ends').value, n = +box.querySelector('[name=interval]').value || 1;
  const on = {interval: repeat === 'daily' || repeat === 'weekly', weekdays: repeat === 'weekly', ends: repeat !== 'none',
              until: repeat !== 'none' && ends === 'until', times: repeat !== 'none' && ends === 'times', note: repeat === 'weekly' && n > 1};
  for (const el of box.querySelectorAll('[data-rec]')) {
    el.hidden = !on[el.dataset.rec];
    for (const i of el.querySelectorAll('input,select')) i.disabled = el.hidden;
  }
  box.querySelector('[name=until]').required = on.until; box.querySelector('[name=times]').required = on.times;
  $('cal-interval-unit').textContent = repeat === 'daily' ? 'روز یک‌بار' : 'هفته یک‌بار';
  $('cal-rec-note').textContent = 'برای هر چند هفته یک‌بار، یک روز هفته انتخاب کنید.';
}
function openSeries(id = '') {
  const s = id && cal.series.find(x => x.id === id);
  const f = s ? s.form : {repeat: 'weekly', interval: 1, weekdays: [], ends: 'never', until: '', times: ''};
  if (f.repeat === 'other') { notice('این تکرار را فرم تقویم نمی‌شناسد؛ آن را از پرونده ویرایش کنید.', true); return; }
  const html = `<input type="hidden" name="original" value="${esc(id)}">
  <label class="wide">عنوان *<input name="title" required maxlength="120" value="${esc(s?.title || '')}" placeholder="مثلاً کلاس هفتگی"></label>
  <label>دسته *<select name="category">${Object.entries(cal.categories).map(([k, n]) => `<option value="${k}"${(s?.category || Object.keys(cal.categories)[0]) === k ? ' selected' : ''}>${n}</option>`).join('')}</select></label>
  <label>ساعت شروع *<input type="time" name="start" required value="${esc(s?.base?.start || '18:00')}"></label>
  <label>ساعت پایان *<input type="time" name="end" required value="${esc(s?.base?.end || '19:30')}"></label>
  <label>${s ? 'نخستین جلسه' : 'از تاریخ'} *<input type="date" name="from" required value="${esc(s?.base?.day || data.asOf)}"></label>
  ${recurrenceControls(f)}
  <label>کجا<input name="place" maxlength="300" value="${esc(s?.place || '')}" placeholder="نام استودیو یا نشانی"></label>
  <label>با چه کسی<input name="with" maxlength="300" value="${esc(s?.with || '')}" placeholder="مربی یا همراه"></label>
  <label class="wide">یادداشت<textarea name="note" maxlength="300">${esc(s?.note || '')}</textarea></label>`;
  openBooksForm('cal-series', s ? s.id : gardenerId(), s ? 'ویرایش «' + s.title + '»' : 'کلاس یا رویداد تازه', html, s ? 'تغییر ساعت یا روزها روی همهٔ جلسه‌های این سری اثر دارد. برای جابه‌جایی فقط یک جلسه، روی همان جلسه در تقویم بزنید. برای تغییر از یک تاریخ به بعد، این سری را با «تا تاریخ» ببند و سری تازه بساز.' : '');
  showRecurrence();
}
function openSession(series, day, extra) {
  const s = cal.series.find(x => x.id === series); const x = s?.sessions.find(y => y.day === day && (y.extra || '') === (extra || ''));
  if (!x) return;
  const actions = [['attended', 'رفتم'], ['missed', 'نرفتم'], ...(x.cancelled ? [] : [['move', s.every || extra ? 'تغییر روز یا ساعتِ فقط همین جلسه' : 'تغییر روز یا ساعت']]), ...(x.state || x.note ? [['clear', 'پاک کردن یادداشت']] : []), ...(!extra && s.every ? [x.cancelled ? ['restore', 'بازگرداندن جلسه'] : ['cancel', 'لغو این جلسه']] : [])];
  const html = `<div class="wide facts">${fact('کلاس', s.title)}${fact('روز', jalali(day, {weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'}) + ' · ' + day)}${fact('ساعت', x.start + '–' + x.end)}${fact('کجا', [s.place, s.with].filter(Boolean).join(' · '))}${fact('وضعیت', x.cancelled ? 'لغو شده' : (cal.states[x.state] || 'ثبت نشده'))}${x.note ? fact('یادداشت', x.note) : ''}</div>
  <div class="wide header-actions"><button type="button" class="secondary" data-cal="edit" data-series="${esc(s.id)}">ویرایش رویداد${s.every ? ' و تکرارش (همهٔ جلسه‌ها)' : ''}</button></div>
  <input type="hidden" name="day" value="${esc(day)}"><input type="hidden" name="extra" value="${esc(extra || '')}">
  <label class="wide">چه شد؟<select name="action" id="cal-action">${actions.map(([k, n]) => `<option value="${k}">${n}</option>`).join('')}</select></label>
  <fieldset class="wide move" id="cal-move" hidden disabled><legend>${s.every || extra ? 'فقط همین جلسه' : 'روز و ساعت تازه'}</legend>
  <label>روز *<input type="date" name="to_day" required value="${esc(day)}"></label>
  <label>شروع *<input type="time" name="start" required value="${esc(x.start)}"></label>
  <label>پایان *<input type="time" name="end" required value="${esc(x.end)}"></label></fieldset>
  <label class="wide">یادداشت<textarea name="note" maxlength="500" placeholder="مثلاً علت لغو یا چیزی که در کلاس گذشت"></textarea></label>`;
  openBooksForm('cal-session', s.id, 'جلسهٔ ' + s.title, html, s.every ? 'لغو، آن روز را از تکرار کنار می‌گذارد؛ «بازگرداندن» آن را برمی‌گرداند. جابه‌جایی همین جلسه، آن روز را لغو و جلسه را در روز و ساعت تازه ثبت می‌کند؛ بقیهٔ جلسه‌ها دست نمی‌خورند.' : '');
}
function openExtra(series) {
  const s = cal.series.find(x => x.id === series); if (!s) return;
  openBooksForm('cal-extra', s.id, 'جلسهٔ اضافهٔ ' + s.title, `<label>روز *<input type="date" name="day" required value="${esc(data.asOf)}"></label><label>شروع *<input type="time" name="start" required value="${esc(s.base?.start || '18:00')}"></label><label>پایان *<input type="time" name="end" required value="${esc(s.base?.end || '19:30')}"></label>`, 'جلسهٔ جبرانی یا اضافه، بیرون از تکرار همیشگی.');
}
function openPackage(series) {
  const s = cal.series.find(x => x.id === series); if (!s) return;
  const p = s.package || {};
  openBooksForm('cal-package', s.id, 'بستهٔ جلسات ' + s.title, `<label>تعداد جلسه‌ها *<input name="sessions" inputmode="numeric" required value="${esc(p.sessions || '')}"></label><label>از<input type="date" name="from" value="${esc(p.from || '')}"></label><label>تا<input type="date" name="until" value="${esc(p.until || '')}"></label><label>بها<input name="count" inputmode="decimal" value="${esc(p.price?.count || '')}"></label><label>ارز<select name="unit">${(data.currencies || []).map(c => `<option${c.code === (p.price?.unit || 'TRY') ? ' selected' : ''}>${esc(c.code)}</option>`).join('')}</select></label><label class="wide">یادداشت<textarea name="note" maxlength="300">${esc(p.note || '')}</textarea></label>`,
    'جلسه‌هایی که «رفتم» خورده‌اند از بسته کم می‌شوند. پرداخت بسته را از صفحهٔ خریدهای کارت به حساب و مرکز هزینهٔ مربوط ببرید. صفر یعنی حذف بسته.');
}
$('entry-form').addEventListener('formdata', e => {
  if (edit?.kind !== 'cal-series') return;
  e.formData.set('weekdays', e.formData.get('repeat') === 'weekly' ? JSON.stringify([...document.querySelectorAll('[data-wd]:checked:not(:disabled)')].map(i => i.dataset.wd)) : '[]');
});

extraTabs.calendar = {title: 'تقویم هفته', render: renderCalendar};
document.addEventListener('click', e => {
  const b = e.target.closest('[data-cal]'); if (!b || !cal) return;
  const k = b.dataset.cal, step = calView === 'month' ? 0 : calView === 'list' ? 30 : 7;
  if (k === 'view') { calView = b.dataset.view; render(); }
  else if (k === 'today') { calAnchor = ''; render(); }
  else if (k === 'prev' || k === 'next') {
    const a = calAnchor || data.asOf;
    if (calView === 'month') { const d = new Date(utc(a.slice(0, 8) + '15')); d.setUTCMonth(d.getUTCMonth() + (k === 'next' ? 1 : -1)); calAnchor = ymd(d); }
    else calAnchor = addDays(a, k === 'next' ? step : -step);
    render();
  }
  else if (k === 'new') openSeries();
  else if (k === 'edit') openSeries(b.dataset.series);
  else if (k === 'session') openSession(b.dataset.series, b.dataset.day, b.dataset.extra);
  else if (k === 'extra') openExtra(b.dataset.series);
  else if (k === 'package') openPackage(b.dataset.series);
});
document.addEventListener('change', e => {
  if (['cal-repeat', 'cal-ends'].includes(e.target.id)) showRecurrence();
  if (e.target.id === 'cal-action') { const m = $('cal-move'); m.hidden = m.disabled = e.target.value !== 'move'; }
});
document.addEventListener('input', e => { if (e.target.name === 'interval' && $('cal-recurrence')) showRecurrence(); });
