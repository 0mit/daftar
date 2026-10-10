// moment (core/law/values.yaml: day, time-of-day): a position in time shown in the reader's calendar — any calendar
// the runtime's CLDR data holds (systems.yaml: persian-calendar, gregorian-civil, hijri …) — and written as the garden
// writes it: an ISO day, `2026-10-08`, or a moment with its offset. The way back from a day typed in the reader's
// calendar is searched in that calendar's own data and then checked against it, so the two directions can never
// disagree; a day that does not exist (30 Esfand in a common year) is refused with a sentence, never moved to a
// neighbour. The law's written form is always taken as written.
import { h, BIDI_CONTROLS } from './safe.js';
import { settings } from './settings.js';
import { langOf, digitsOf, inDigits, toAscii, calendarOf, relativeDay, dirOf, say } from './locale.js';
const IMPL = 'day';
export { IMPL as implements };
const pad = n => String(n).padStart(2, '0');
const DAY = 86400000;
const iso = t => { const c = new Date(t); return `${String(c.getUTCFullYear()).padStart(4, '0')}-${pad(c.getUTCMonth() + 1)}-${pad(c.getUTCDate())}`; };
const noon = day => { const [y, m, d] = day.split('-').map(Number); const t = new Date(Date.UTC(2000, m - 1, d, 12)); t.setUTCFullYear(y); return t.getTime(); };
const WRITTEN = new Set(['gregory', 'iso8601']);   // the calendars whose numeric day is the written form itself

// the written forms: a day, or a moment to the minute or finer with its offset
export function parse(v) {
  const s = String(v ?? '').trim();
  let m = s.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (m) return {day: s, y: +m[1], m: +m[2], d: +m[3]};
  m = s.match(/^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})(?::\d{2}(?:\.\d+)?)?(Z|[+-]\d{2}:?\d{2})?$/);
  if (m) return {day: `${m[1]}-${m[2]}-${m[3]}`, y: +m[1], m: +m[2], d: +m[3], time: `${m[4]}:${m[5]}`, offset: m[6] || ''};
  return null;
}

const fmts = new Map();
function partsAt(cal, t) {               // a moment's day in a calendar, as numbers, with its era where it has one
  let f = fmts.get(cal);
  if (!f) fmts.set(cal, f = new Intl.DateTimeFormat(`en-u-ca-${cal}-nu-latn`, {era: 'short', year: 'numeric', month: 'numeric', day: 'numeric', timeZone: 'UTC'}));
  const ps = f.formatToParts(new Date(t)), get = k => (ps.find(p => p.type === k) || {}).value;
  return {era: get('era') || '', y: Number(get('year') ?? get('relatedYear')), m: Number(get('month')), d: Number(get('day'))};
}
// a written day as {y, m, d} of a calendar
export const toCalendar = (day, cal) => partsAt(cal, noon(day));
// a day of a calendar, in the era it is in today, as the written day — or null when the calendar has no such day
export function fromCalendar(cal, y, m, d) {
  if (![y, m, d].every(Number.isInteger)) return null;
  const today = Date.now(), era = partsAt(cal, today).era;
  let lo = Date.UTC(2000, 0, 1, 12); lo = new Date(lo).setUTCFullYear(1);
  const hi = new Date(Date.UTC(2000, 11, 31, 12)).setUTCFullYear(9999);
  if (era) {                             // the first day of today's era: a year count restarts at an era's start
    let a = lo, b = today;
    while (b - a > DAY) { const mid = a + Math.floor((b - a) / DAY / 2) * DAY; partsAt(cal, mid).era === era ? (b = mid) : (a = mid); }
    lo = partsAt(cal, a).era === era ? a : b;
  }
  const key = p => [p.y, p.m, p.d];
  const before = (p, q) => { for (let i = 0; i < 3; i++) if (p[i] !== q[i]) return p[i] < q[i]; return false; };
  let a = lo, b = hi;
  while (b - a > DAY) { const mid = a + Math.floor((b - a) / DAY / 2) * DAY; before(key(partsAt(cal, mid)), [y, m, d]) ? (a = mid) : (b = mid); }
  for (const t of [a, b]) { const p = partsAt(cal, t); if (p.y === y && p.m === m && p.d === d && (!era || p.era === era)) return iso(t); }
  return null;
}
// the order a language writes a numeric day's parts in, in a calendar (CLDR): e.g. ['year', 'month', 'day']
function order(lang, cal) {
  return new Intl.DateTimeFormat(`${lang}-u-ca-${cal}-nu-latn`, {year: 'numeric', month: '2-digit', day: '2-digit', timeZone: 'UTC'})
    .formatToParts(new Date(Date.UTC(2001, 1, 3, 12))).map(p => p.type).filter(t => ['year', 'month', 'day'].includes(t));
}

const longFormats = {};
function long(day, o) {
  const cal = calendarOf(o), lang = langOf(o), ns = digitsOf(o);
  const key = [cal, lang, ns, o.style, o.year].join('|');
  longFormats[key] ||= new Intl.DateTimeFormat(`${lang}-u-ca-${cal}-nu-${ns}`, {day: 'numeric', month: 'long',
    year: o.year === false ? undefined : 'numeric', weekday: o.style === 'weekday' ? 'long' : undefined, timeZone: 'UTC'});
  return longFormats[key].format(new Date(noon(day)));
}
const numFormats = {};
function numeric(day, o) {
  const cal = calendarOf(o), lang = langOf(o), ns = digitsOf(o);
  if (WRITTEN.has(cal)) return inDigits(day, ns);
  const key = [cal, lang, ns].join('|');
  numFormats[key] ||= new Intl.DateTimeFormat(`${lang}-u-ca-${cal}-nu-${ns}`, {year: 'numeric', month: '2-digit', day: '2-digit', timeZone: 'UTC'});
  return numFormats[key].format(new Date(noon(day))).replace(BIDI_CONTROLS, '');
}
// the day relative to today (the server's, settings.asOf), in the reader's words; otherwise null
function relative(day, o) {
  if (!settings.asOf) return null;
  return relativeDay(Math.round((noon(day) - noon(settings.asOf)) / DAY), o);
}
// options: style 'numeric'|'long'|'weekday'; calendar; lang; digits; year: false; relative: true
export function show(v, o = {}) {
  const p = parse(v);
  if (!p) return v ? h`<span class="w-moment w-bad">${v}</span>` : h`<span class="w-moment w-none">—</span>`;
  const style = o.style || 'numeric', rel = o.relative ? relative(p.day, o) : null;
  let text = rel || (style === 'numeric' ? numeric(p.day, o) : long(p.day, {...o, style}));
  if (p.time) text += ' ' + inDigits(p.time, digitsOf(o));
  const dir = style === 'numeric' && !rel ? 'ltr' : dirOf(langOf(o));
  const written = p.day + (p.time ? ' ' + p.time : '');
  return h`<time class="w-moment" datetime="${p.day}${p.time ? 'T' + p.time : ''}" dir="${dir}"${text === written ? '' : h` title="${written}"`}>${text}</time>`;
}
export function text(v, o = {}) {
  const p = parse(v);
  return p ? '\u2068' + numeric(p.day, o) + (p.time ? ' ' + inDigits(p.time, digitsOf(o)) : '') + '\u2069' : '';
}
// what a person typed, as the written day: the law's form (`2026-10-08`) as written, or a day of the reader's calendar
// with `/` or `.` between its parts, in the order its language writes them, in any digits
export function take(input, o = {}) {
  const s = toAscii(String(input ?? '').trim()).replace(BIDI_CONTROLS, '');
  const today = settings.asOf || iso(Date.now());
  if (!s) return o.required ? {error: say('day-required', o)} : {value: ''};
  let m = s.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (m) return iso(noon(s)) === s ? {value: s} : {error: say('day-none', o)};
  m = s.match(/^(\d{1,4})\s*[\/.]\s*(\d{1,4})\s*[\/.]\s*(\d{1,4})$/);
  if (!m) return {error: say('day-form', o, {example: numeric(today, o), written: today})};
  const cal = calendarOf(o), at = {};
  const probe = toCalendar(today, cal);         // a calendar whose months CLDR writes only by name takes the law's form
  if (!WRITTEN.has(cal) && ![probe.y, probe.m, probe.d].every(Number.isFinite)) return {error: say('day-written', o, {written: today})};
  order(langOf(o), cal).forEach((k, i) => { at[k] = +m[i + 1]; });
  const day = WRITTEN.has(cal) ? `${String(at.year).padStart(4, '0')}-${pad(at.month)}-${pad(at.day)}` : fromCalendar(cal, at.year, at.month, at.day);
  return day && (!WRITTEN.has(cal) || iso(noon(day)) === day) ? {value: day} : {error: say('day-none', o)};
}
export function edit(name, value, o = {}) {
  const p = parse(value);
  const shown = p ? numeric(p.day, o) : '';
  // placeholder: what an empty field means («from the start»), where an example day would read as a value
  const ph = o.placeholder ?? (settings.asOf ? numeric(settings.asOf, o) : '');
  return h`<input class="w-input w-moment-input" name="${name}" dir="ltr" inputmode="numeric" autocomplete="off" placeholder="${ph}" value="${shown}">`;
}
// a time of day, HH:MM, shown in the reader's digits
export const showTime = (t, o = {}) => /^\d{2}:\d{2}$/.test(String(t ?? '')) ? h`<bdi dir="ltr" class="w-time">${inDigits(t, digitsOf(o))}</bdi>` : h`<span class="w-none">—</span>`;
export function takeTime(input, o = {}) {
  const s = toAscii(String(input ?? '').trim()).replace(BIDI_CONTROLS, '');
  if (!s) return o.required ? {error: say('time-required', o)} : {value: ''};
  const m = s.match(/^(\d{1,2}):(\d{2})$/);
  return m && +m[1] < 24 && +m[2] < 60 ? {value: `${pad(+m[1])}:${m[2]}`} : {error: say('time-form', o, {example: inDigits('08:30', digitsOf(o))})};
}
