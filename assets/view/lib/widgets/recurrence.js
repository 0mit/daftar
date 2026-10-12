// recurrence (core/law/values.yaml: recurrence): a rule of repetition — each week on two days, the first of each month
// six times — shown as a sentence in the reader's language and taken in as the law writes it (core/law/measures.yaml,
// `recurrence`): `of` the line it runs along, `in` the system it is counted in, `each` cell of a level of that system or
// `every` N neighbours or units, `at` its places in the cell, `from`, `to`, `times`, `lasts`, and `closures` kept as
// written. Never walked here: its moments are read by bin/stale.py. The systems it can be counted in, their levels and
// their written forms, and the units of a duration, are the law's, sent by the host (`settings.systems`,
// `settings.durations`); the reader's calendar is theirs (locale.js); no calendar, language or unit is named here.
import { h } from './safe.js';
import { settings } from './settings.js';
import { langOf, digitsOf, inDigits, toAscii, calendarOf, say } from './locale.js';
import * as moment from './moment.js';
import * as choice from './choice.js';
const IMPL = 'recurrence';
export { IMPL as implements };
const pad = n => String(n).padStart(2, '0');
const DAY = 86400000;
const noon = day => { const [y, m, d] = day.split('-').map(Number); const t = new Date(Date.UTC(2000, m - 1, d, 12)); t.setUTCFullYear(y); return t.getTime(); };
const iso = t => { const c = new Date(t); return `${String(c.getUTCFullYear()).padStart(4, '0')}-${pad(c.getUTCMonth() + 1)}-${pad(c.getUTCDate())}`; };

// THE SYSTEMS, as the law gives them: {system, calendar (CLDR's), prefix (`persian:` — what its written form begins
// with), week (true for a system whose positions are a year's weeks and a week's days), levels}
const systems = () => settings.systems || [];
const sys = id => systems().find(s => s.system === id) || null;
// the system a level is counted in for this reader: a week in the system of weeks, every other level in the reader's
// own calendar — the one whose CLDR calendar is theirs
function systemFor(level, o) {
  const cal = calendarOf(o), all = systems().filter(s => (s.levels || []).includes(level));
  return (level === 'week' ? all.find(s => s.week) : all.find(s => s.calendar === cal && !s.week)) || all[0] || null;
}

// A DAY AS A SYSTEM WRITES IT, and back: a week system's `YYYY-Www-D` (ISO 8601), a calendar's own `YYYY-MM-DD` behind
// its prefix, read through CLDR's data for that calendar (moment.js), never through a table here
function isoWeek(day) {
  const t = noon(day), wd = (new Date(t).getUTCDay() + 6) % 7 + 1, thu = t + (4 - wd) * DAY, y = new Date(thu).getUTCFullYear();
  const w = 1 + Math.floor((thu - noon(`${String(y).padStart(4, '0')}-01-01`)) / (7 * DAY));
  return `${y}-W${pad(w)}-${wd}`;
}
function fromIsoWeek(s) {
  const m = String(s).match(/^(-?\d{4})-W(\d{2})-([1-7])$/);
  if (!m) return null;
  const jan4 = noon(`${m[1]}-01-04`), wd4 = (new Date(jan4).getUTCDay() + 6) % 7 + 1;
  return iso(jan4 - (wd4 - 1) * DAY + ((+m[2] - 1) * 7 + (+m[3] - 1)) * DAY);
}
export function written(day, system) {
  const s = sys(system);
  if (!s || !day) return '';
  if (s.week) return isoWeek(day);
  if (!s.prefix) return day;
  const p = moment.toCalendar(day, s.calendar);
  return `${s.prefix}${p.y}-${pad(p.m)}-${pad(p.d)}`;
}
export function dayOf(position, system) {
  const s = sys(system), v = String(position ?? '').split(/[T ]/)[0];
  if (!s || !v) return null;
  if (s.week) return fromIsoWeek(v);
  if (!s.prefix) return /^\d{4}-\d{2}-\d{2}$/.test(v) ? v : null;
  const m = v.startsWith(s.prefix) && v.slice(s.prefix.length).match(/^(-?\d+)-(\d{2})-(\d{2})$/);
  return m ? moment.fromCalendar(s.calendar, +m[1], +m[2], +m[3]) : null;
}

// a week's days, in the order the reader's region begins a week (CLDR's firstDay, through Intl), each by its name
function firstDay(lang) {
  try { const L = new Intl.Locale(lang).maximize(), i = L.getWeekInfo ? L.getWeekInfo() : L.weekInfo; if (i && i.firstDay) return i.firstDay; } catch (e) { /* the standard's */ }
  return 1;
}
function weekdays(o) {
  const lang = langOf(o), f = new Intl.DateTimeFormat(lang, {weekday: 'long', timeZone: 'UTC'}), first = firstDay(lang);
  const out = [];
  for (let i = 0; i < 7; i++) {
    const n = (first - 1 + i) % 7 + 1;                     // ISO 8601 numbers a week's days from Monday, 1, to 7
    out.push({value: String(n), label: f.format(new Date(Date.UTC(2024, 0, n, 12)))});   // 2024-01-01 was a Monday
  }
  return out;
}
const unitName = (u, n, o) => {
  const row = (settings.durations || []).find(x => x.unit === u), lang = langOf(o);
  try { return new Intl.NumberFormat(`${lang}-u-nu-${digitsOf(o)}`, {style: 'unit', unit: row ? row.name : u, unitDisplay: 'long'}).format(Number(n)); }
  catch (e) { return `${inDigits(String(n), digitsOf(o))} ${u}`; }
};
// THE UNITS OF A LENGTH OF TIME a reader can be offered: the law's units of duration whose name is a unit CLDR names
// (through Intl) — a minute, an hour, a day — in the order the law lists them; a unit no language names is never offered
export function durations(o = {}) {
  return (settings.durations || []).filter(d => {
    try { new Intl.NumberFormat(langOf(o), {style: 'unit', unit: d.name}); return true; } catch (e) { return false; }
  });
}
// a unit's own words, without a number: CLDR's long name for the unit, read from Intl's parts of a formatted amount
export function unitWords(u, o) {
  const row = (settings.durations || []).find(x => x.unit === u);
  try {
    return new Intl.NumberFormat(langOf(o), {style: 'unit', unit: row ? row.name : u, unitDisplay: 'long'}).formatToParts(2)
      .filter(p => p.type === 'unit').map(p => p.value).join(' ') || u;
  } catch (e) { return u; }
}
const levelWord = (lv, o) => say('rec-level-' + lv, o) === 'rec-level-' + lv ? lv : say('rec-level-' + lv, o);

// THE RULE IN WORDS: each <level> (on <places>), from <day>, to <day> or <n> times, each lasting <length>
export function text(v, o = {}) {
  if (!v || typeof v !== 'object') return '';
  const ns = digitsOf(o), parts = [];
  const at = v.at === undefined ? [] : [].concat(v.at).map(String);
  if (v.each) {
    let s = say('rec-each', o, {level: levelWord(v.each, o)});
    if (at.length && v.each === 'week' && (sys(v.in) || {}).week) {
      // each day by its name, and the time of day a place names after it, ISO 8601's way (`5T17:45`)
      const names = weekdays(o).flatMap(d => at.filter(a => a.split('T')[0] === d.value)
        .map(a => a.includes('T') ? `${d.label} ${inDigits(a.split('T')[1], ns)}` : d.label));
      s += ' ' + say('rec-on', o, {places: names.join(say('rec-and', o))});
    } else if (at.length) s += ' ' + say('rec-at', o, {places: at.map(a => inDigits(a, ns)).join(say('rec-and', o))});
    parts.push(s);
  } else if (v.every && typeof v.every === 'object') {
    parts.push(v.every.unit ? say('rec-every-units', o, {n: unitName(v.every.unit, v.every.count, o)})
      : say('rec-every-nth', o, {n: inDigits(String(v.every.count), ns)}));
  }
  const d1 = dayOf(v.from, v.in), d2 = dayOf(v.to, v.in);
  if (v.from) parts.push(say('rec-from', o, {day: d1 ? moment.text(d1, o) : String(v.from)}));
  if (v.to) parts.push(say('rec-to', o, {day: d2 ? moment.text(d2, o) : String(v.to)}));
  if (v.times) parts.push(say('rec-times', o, {n: inDigits(String(v.times), ns)}));
  const len = v.lasts && v.lasts.measure;
  if (len && len.count) parts.push(say('rec-lasts', o, {length: unitName(len.unit, len.count, o)}));
  if (Array.isArray(v.closures) && v.closures.length) parts.push(say('rec-closures', o, {n: inDigits(String(v.closures.length), ns)}));
  return parts.join(say('rec-sep', o));
}
export function show(v, o = {}) {
  const s = text(v, o);
  return s ? h`<span class="w-recurrence">${s}</span>` : h`<span class="w-none">—</span>`;
}

// EDITING: the level, the places in it, the first day (in the reader's calendar), the last day or how many times, and
// how long each lasts. What the form does not offer — `every`, `closures`, a place it cannot draw — is kept as written:
// a day of the week with its time of day (`5T17:45`) is no box to tick, so the places are a field that holds them.
export function edit(name, value, o = {}) {
  const v = value && typeof value === 'object' ? value : {};
  const levels = [...new Set(systems().flatMap(s => (s.levels || []).filter(l => ['day', 'week', 'month', 'year'].includes(l))))];
  const each = v.each || '', at = v.at === undefined ? [] : [].concat(v.at).map(String);
  const s = v.in ? sys(v.in) : systemFor(each || 'week', o);
  const week = (each || 'week') === 'week' && s && s.week && !at.some(a => a.includes('T'));
  const places = week
    ? h`<span class="w-rec-days">${weekdays(o).map(d => h`<label class="w-rec-day"><input type="checkbox" name="${name}.at" value="${d.value}"${at.includes(d.value) ? h` checked` : ''}> ${d.label}</label>`)}</span>`
    : h`<input class="w-input w-name-input" name="${name}.at" dir="ltr" value="${at.join(', ')}">`;
  const len = (v.lasts && v.lasts.measure) || {};
  return h`<span class="w-recurrence-input" data-name="${name}" data-in="${v.in || ''}" data-keep="${JSON.stringify(
    {every: v.every, closures: v.closures, of: v.of})}">
    <label>${say('rec-each-label', o)} ${choice.edit(name + '.each', each, levels.map(l => ({value: l, label: levelWord(l, o)})), {none: '—'})}</label>
    <label>${say('rec-places-label', o)} ${places}</label>
    <label>${say('rec-from-label', o)} ${moment.edit(name + '.from', dayOf(v.from, v.in) || '', o)}</label>
    <label>${say('rec-to-label', o)} ${moment.edit(name + '.to', dayOf(v.to, v.in) || '', {...o, placeholder: ''})}</label>
    <label>${say('rec-times-label', o)} <input class="w-input w-num-input" name="${name}.times" dir="ltr" inputmode="numeric" value="${v.times ? inDigits(String(v.times), digitsOf(o)) : ''}"></label>
    <label>${say('rec-lasts-label', o)} <input class="w-input w-num-input" name="${name}.lasts.count" dir="ltr" inputmode="numeric" value="${len.count ? inDigits(String(len.count), digitsOf(o)) : ''}">
      ${choice.edit(name + '.lasts.unit', len.unit || '', durations(o).map(d => ({value: d.unit, label: unitWords(d.unit, o)})), {none: '—'})}</label>
  </span>`;
}

// what the fields hold, as the law writes a recurrence — or the first error, said in the reader's language. `fields` is
// {each, at: [..] | 'a, b', from, to, times, 'lasts.count', 'lasts.unit', in, keep}
export function take(fields, o = {}) {
  const f = fields || {}, keep = (() => { try { return JSON.parse(f.keep || '{}'); } catch (e) { return {}; } })();
  const each = String(f.each || '').trim();
  if (!each && !keep.every) return o.required ? {error: say('rec-level-required', o)} : {value: ''};
  const s = f.in && sys(f.in) && (!each || (sys(f.in).levels || []).includes(each)) ? sys(f.in) : systemFor(each, o);
  if (each && !s) return {error: say('rec-no-system', o, {level: levelWord(each, o)})};
  const v = {of: keep.of || 'time'};
  if (s) v.in = s.system;
  if (each) v.each = each; else v.every = keep.every;
  const at = (Array.isArray(f.at) ? f.at : String(f.at || '').split(',')).map(x => toAscii(String(x)).trim()).filter(Boolean);
  if (at.some(a => !/^[A-Za-z0-9-]*(T([01]\d|2[0-3]):[0-5]\d)?$/.test(a))) {   // a place, and its time of day `hh:mm`
    const ns = digitsOf(o);
    return {error: say('rec-place-form', o, {ex: inDigits('15', ns), lo: inDigits('1', ns), hi: inDigits('7', ns)})};
  }
  // the places in the system's own order (a week's days 1 to 7), never in the order a reader's week shows them
  if (at.every(a => /^\d+(T\d\d:\d\d)?$/.test(a))) {
    at.sort((a, b) => Number(a.split('T')[0]) - Number(b.split('T')[0]) || (a < b ? -1 : a > b ? 1 : 0));
  }
  if (at.length) v.at = at.length === 1 ? at[0] : at;
  for (const side of ['from', 'to']) {
    const d = moment.take(f[side], o);
    if (d.error) return {error: d.error};
    if (d.value) v[side] = written(d.value, v.in);
  }
  const t = toAscii(String(f.times || '')).trim();
  if (t) { if (!/^[1-9]\d*$/.test(t)) return {error: say('rec-times-form', o)}; v.times = t; }
  const lc = toAscii(String(f['lasts.count'] || '')).trim(), lu = String(f['lasts.unit'] || '').trim();
  if (lc || lu) {
    if (!/^[1-9]\d*(\.\d+)?$/.test(lc) || !lu) return {error: say('rec-lasts-form', o)};
    v.lasts = {of: v.of, measure: {count: lc, unit: lu}};
  }
  if (keep.closures) v.closures = keep.closures;
  return {value: v};
}
