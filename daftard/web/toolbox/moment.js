// moment (types tree: day, time-of-day): a position in time shown in the reader's calendar (systems.yaml:
// persian-calendar, gregorian-civil), written as the garden writes it (an ISO day, `2026-10-08`, or a moment with its
// offset). Persian dates come from the browser's own calendar data (Intl, CLDR); the way back to the written day is
// found and then checked against that same data, so the two directions can never disagree. A day that does not exist
// (30 Esfand in a common year) is refused with a sentence, never moved to a neighbour.
import { h, BIDI_CONTROLS } from './safe.js';
import { settings } from './settings.js';
const IMPL = 'day';
export { IMPL as implements };
const FA = '۰۱۲۳۴۵۶۷۸۹';
const ascii = s => String(s).replace(/[۰-۹]/g, d => FA.indexOf(d)).replace(/[٠-٩]/g, d => '٠١٢٣٤٥٦٧٨٩'.indexOf(d));
const persianDigits = s => String(s).replace(/[0-9]/g, d => FA[d]);
const pad = n => String(n).padStart(2, '0');
const DAY = 86400000;
const iso = t => { const c = new Date(t); return `${c.getUTCFullYear()}-${pad(c.getUTCMonth() + 1)}-${pad(c.getUTCDate())}`; };

// the written forms: a day, or a moment to the minute or finer with its offset
export function parse(v) {
  const s = String(v ?? '').trim();
  let m = s.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (m) return {day: s, y: +m[1], m: +m[2], d: +m[3]};
  m = s.match(/^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})(?::\d{2}(?:\.\d+)?)?(Z|[+-]\d{2}:?\d{2})?$/);
  if (m) return {day: `${m[1]}-${m[2]}-${m[3]}`, y: +m[1], m: +m[2], d: +m[3], time: `${m[4]}:${m[5]}`, offset: m[6] || ''};
  return null;
}

const PERSIAN = new Intl.DateTimeFormat('en-u-ca-persian-nu-latn', {year: 'numeric', month: 'numeric', day: 'numeric', timeZone: 'UTC'});
// an ISO (Gregorian) day as {y, m, d} of the Persian calendar
export function toPersian(day) {
  const [y, m, d] = day.split('-').map(Number);
  const parts = PERSIAN.formatToParts(new Date(Date.UTC(y, m - 1, d, 12)));
  const get = t => Number(parts.find(p => p.type === t).value);
  return {y: get('year'), m: get('month'), d: get('day')};
}
// a Persian day as an ISO day, or null when there is no such day
export function fromPersian(y, m, d) {
  if (!(m >= 1 && m <= 12 && d >= 1 && d <= (m <= 6 ? 31 : m <= 11 ? 30 : 30))) return null;
  const guess = Date.UTC(y + 621, 2, 20, 12) + ((m <= 6 ? (m - 1) * 31 : 186 + (m - 7) * 30) + (d - 1)) * DAY;
  for (const k of [0, 1, -1, 2, -2, 3, -3]) {
    const day = iso(guess + k * DAY), p = toPersian(day);
    if (p.y === y && p.m === m && p.d === d) return day;
  }
  return null;
}

const longFormats = {};
function long(day, o) {
  const cal = o.calendar || settings.calendar, lang = o.lang || settings.lang;
  const key = [cal, lang, o.style, o.year].join('|');
  longFormats[key] ||= new Intl.DateTimeFormat(`${lang}-u-ca-${cal}`, {day: 'numeric', month: 'long',
    year: o.year === false ? undefined : 'numeric', weekday: o.style === 'weekday' ? 'long' : undefined, timeZone: 'UTC'});
  const [y, m, d] = day.split('-').map(Number);
  return longFormats[key].format(new Date(Date.UTC(y, m - 1, d, 12)));
}
function numeric(day, o) {
  const cal = o.calendar || settings.calendar;
  const s = cal === 'persian' ? (p => `${p.y}/${pad(p.m)}/${pad(p.d)}`)(toPersian(day)) : day;
  return (o.lang || settings.lang) === 'fa' ? persianDigits(s) : s;
}
// the day relative to today (the server's, settings.asOf): امروز, دیروز, فردا; otherwise null
function relative(day) {
  if (!settings.asOf) return null;
  const diff = Math.round((Date.parse(day + 'T12:00:00Z') - Date.parse(settings.asOf + 'T12:00:00Z')) / DAY);
  return {0: 'امروز', [-1]: 'دیروز', 1: 'فردا'}[diff] ?? null;
}
// options: style 'numeric'|'long'|'weekday'; calendar; lang; year: false; relative: true
export function show(v, o = {}) {
  const p = parse(v);
  if (!p) return v ? h`<span class="w-moment w-bad">${v}</span>` : h`<span class="w-moment w-none">—</span>`;
  const style = o.style || 'numeric';
  const cal = o.calendar || settings.calendar, lang = o.lang || settings.lang;
  let text = (o.relative && relative(p.day)) || (style === 'numeric' ? numeric(p.day, o) : long(p.day, {...o, style}));
  if (p.time) text += ' ' + (lang === 'fa' ? persianDigits(p.time) : p.time);
  const other = cal === 'persian' ? numeric(p.day, {calendar: 'gregory', lang: 'en'}) : numeric(p.day, {calendar: 'persian', lang: 'fa'});
  const dir = style === 'numeric' && !(o.relative && relative(p.day)) ? 'ltr' : (lang === 'fa' ? 'rtl' : 'ltr');
  return h`<time class="w-moment" datetime="${p.day}${p.time ? 'T' + p.time : ''}" dir="${dir}" title="${other}">${text}</time>`;
}
export function text(v, o = {}) {
  const p = parse(v);
  return p ? '\u2068' + numeric(p.day, o) + (p.time ? ' ' + p.time : '') + '\u2069' : '';
}
// what a person typed, as the written day: a Persian date (a year under 1700) or a Gregorian one, in any digits
export function take(input, o = {}) {
  const s = ascii(String(input ?? '').trim()).replace(BIDI_CONTROLS, '');
  if (!s) return o.required ? {error: 'تاریخ را بنویسید.'} : {value: ''};
  const m = s.match(/^(\d{4})\s*[\/\-.]\s*(\d{1,2})\s*[\/\-.]\s*(\d{1,2})$/);
  if (!m) return {error: 'تاریخ را به شکل ۱۴۰۵/۰۷/۱۶ بنویسید.'};
  const [y, mo, d] = [+m[1], +m[2], +m[3]];
  if (y < 1700) {
    const day = fromPersian(y, mo, d);
    return day ? {value: day} : {error: 'چنین روزی در تقویم خورشیدی نیست.'};
  }
  const day = `${y}-${pad(mo)}-${pad(d)}`;
  return iso(Date.UTC(y, mo - 1, d, 12)) === day ? {value: day} : {error: 'چنین روزی در تقویم میلادی نیست.'};
}
export function edit(name, value, o = {}) {
  const p = parse(value);
  const shown = p ? numeric(p.day, o) : '';
  // placeholder: what an empty field means («از آغاز»), where an example day would read as a value
  return h`<input class="w-input w-moment-input" name="${name}" dir="ltr" inputmode="numeric" autocomplete="off" placeholder="${o.placeholder ?? numeric(settings.asOf || '2026-01-01', o)}" value="${shown}">`;
}
// a time of day, HH:MM, shown in the reader's digits
export const showTime = (t, o = {}) => /^\d{2}:\d{2}$/.test(String(t ?? '')) ? h`<bdi dir="ltr" class="w-time">${(o.lang || settings.lang) === 'fa' ? persianDigits(t) : t}</bdi>` : h`<span class="w-none">—</span>`;
export function takeTime(input, o = {}) {
  const s = ascii(String(input ?? '').trim());
  if (!s) return o.required ? {error: 'ساعت را بنویسید.'} : {value: ''};
  const m = s.match(/^(\d{1,2}):(\d{2})$/);
  return m && +m[1] < 24 && +m[2] < 60 ? {value: `${pad(+m[1])}:${m[2]}`} : {error: 'ساعت را به شکل ۰۸:۳۰ بنویسید.'};
}
