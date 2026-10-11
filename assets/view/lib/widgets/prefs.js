// prefs: a reader's own way of reading, chosen in a panel in their own language — their language and, as the Unicode
// extension of its BCP 47 tag (UTS #35), the calendar (`ca`), the digits (`nu`), the hour cycle (`hc`), the first day
// of the week (`fw`) and the zone moments are shown in (`tz`); beside the tag, named, how a day is written (`date`) and
// how a currency is named (`currency`). Each choice is shown at once on a sample day, time, amount and number. The tag
// is composed and read by Intl.Locale, never by a pattern of ours; the host reads it again by the grammar
// (view_prefs.py) and keeps it with the reader's account. What is not chosen is the language's own, as CLDR says it.
// The lists are the runtime's own (Intl.supportedValuesOf) and the host's (the zones CLDR names a `tz` for).
import { h, join, mount } from './safe.js';
import { settings, configure } from './settings.js';
import { langOf, say, glyphs } from './locale.js';
import * as moment from './moment.js';
import * as money from './money.js';
import * as number from './number.js';

const KEYS = ['ca', 'fw', 'hc', 'nu', 'tz'];
const DAYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'];
const supported = k => { try { return Intl.supportedValuesOf(k); } catch { return []; } };

// THE TAG'S PARTS, as Intl.Locale reads them: its language (base name) and the Unicode keys a reader sets
export function split(tag) {
  const out = {lang: '', ca: '', fw: '', hc: '', nu: '', tz: ''};
  let L;
  try { L = new Intl.Locale(tag || ''); } catch { return out; }
  out.lang = L.baseName;
  const ext = (L.toString().split(/-u-/i)[1] || '').split(/-[a-z0-9]-/i)[0];
  let key = null;
  for (const part of ext ? ext.split('-') : []) {
    if (part.length === 2 && /[a-z]/i.test(part[1])) { key = part.toLowerCase(); if (key in out) out[key] = ''; }
    else if (key && key in out) out[key] = out[key] ? out[key] + '-' + part : part;
  }
  return out;
}
// the tag of a language and the keys chosen, in the order a canonical tag has them; Intl.Locale refuses a malformed one
export function compose(f) {
  const keys = KEYS.filter(k => f[k]).map(k => `${k}-${f[k]}`).join('-');
  const tag = (f.lang || '') + (keys ? '-u-' + keys : '');
  return new Intl.Locale(tag).toString();
}

function select(name, rows, value) {
  return h`<select class="w-input w-prefs-select" name="${name}">${rows.map(r => h`<option value="${r[0]}"${r[0] === value ? h` selected` : ''}>${r[1]}</option>`)}</select>`;
}
const display = (lang, type) => { try { return new Intl.DisplayNames([lang], {type}); } catch { return null; } };
const named = (dn, code) => { try { return (dn && dn.of(code)) || code; } catch { return code; } };

// options: {languages: [tags offered], zones: [[tz type, IANA zone]], currency: a code for the sample, gardenZone}
export function panel(current = {}, o = {}) {
  const f = split(current.locale || ''), lang = f.lang || langOf({}), now = new Date();
  const dl = display(lang, 'language'), dc = display(lang, 'calendar');
  const langs = [...new Set([...(o.languages || []), f.lang].filter(Boolean))];
  const def = x => say('prefs-default', {}, {x});
  const weekday = n => new Intl.DateTimeFormat(lang, {weekday: 'long', timeZone: 'UTC'}).format(new Date(Date.UTC(2024, 0, n, 12)));
  const rows = {
    lang: langs.map(l => [l, named(dl, l)]),
    ca: [['', def(named(dc, new Intl.DateTimeFormat(lang).resolvedOptions().calendar))]].concat(supported('calendar').map(c => [c, named(dc, c)])),
    nu: [['', def(new Intl.NumberFormat(lang).format(123))]].concat(supported('numberingSystem')
      .filter(n => { try { const g = glyphs(n); return g.every(c => [...c].length === 1) && new Set(g).size === 10; } catch { return false; } })
      .map(n => [n, glyphs(n).join('') + ' · ' + n])),
    hc: [['', def(new Intl.DateTimeFormat(lang, {hour: 'numeric', minute: '2-digit', timeZone: 'UTC'}).format(Date.UTC(2000, 0, 1, 13, 5)))],
         ['h23', new Intl.DateTimeFormat(lang, {hour: 'numeric', minute: '2-digit', hourCycle: 'h23', timeZone: 'UTC'}).format(Date.UTC(2000, 0, 1, 13, 5))],
         ['h12', new Intl.DateTimeFormat(lang, {hour: 'numeric', minute: '2-digit', hourCycle: 'h12', timeZone: 'UTC'}).format(Date.UTC(2000, 0, 1, 13, 5))]],
    fw: [['', def(weekday(firstDay(lang)))]].concat(DAYS.map((d, i) => [d, weekday(i + 1)])),
    tz: [['', say('prefs-garden-zone', {}, {x: o.gardenZone || settings.zone || '—'})]].concat((o.zones || []).map(z => [z[0], z[1]])),
    date: [['', def(dated(lang, 'numeric'))]].concat(['short', 'medium', 'long', 'full'].map(x => [x, dated(lang, x)])),
    currency: [['', def(o.currency || 'EUR')]].concat(['symbol', 'narrowSymbol', 'code', 'name'].map(x => [x, priced(lang, o.currency, x)])),
  };
  const field = (k, value) => h`<label class="w-prefs-field" data-pref="${k}"><span class="w-prefs-label">${say('prefs-' + k)}</span> ${select('pref.' + k, rows[k], value)}</label>`;
  return h`<form class="w-prefs">
    <h3 class="w-prefs-title">${say('prefs-title')}</h3>
    ${join(['lang', 'ca', 'nu', 'hc', 'fw', 'tz'].map(k => field(k, k === 'lang' ? (f.lang || lang) : f[k] || '')), '')}
    ${field('date', current.date || '')}${field('currency', current.currency || '')}
    <div class="w-prefs-sample" aria-live="polite"></div>
    <p class="w-prefs-error" role="alert"></p>
    <div class="w-prefs-bar"><button type="button" class="w-prefs-save" data-prefs="save">${say('prefs-save')}</button> <button type="button" data-prefs="cancel">${say('prefs-cancel')}</button></div>
  </form>`;
}
// a day written in each style, and an amount with its currency named each way: what each choice looks like
function dated(lang, style) {
  try {
    const opt = style === 'numeric' ? {year: 'numeric', month: '2-digit', day: '2-digit'} : {dateStyle: style};
    return new Intl.DateTimeFormat(lang, {...opt, timeZone: 'UTC'}).format(new Date(Date.UTC(2026, 9, 11, 12)));
  } catch { return style; }
}
function priced(lang, code, how) {
  try { return new Intl.NumberFormat(lang, {style: 'currency', currency: code || 'EUR', currencyDisplay: how}).format(1234.5); } catch { return how; }
}
function firstDay(lang) {
  try { const L = new Intl.Locale(lang).maximize(), i = L.getWeekInfo ? L.getWeekInfo() : L.weekInfo; return (i && i.firstDay) || 1; } catch { return 1; }
}
const zoneOf = (tz, zones) => ((zones || []).find(z => z[0] === tz) || [])[1] || '';

// WHAT THE PANEL HOLDS, as the host keeps it: {value: {locale, date, currency}} or {error}
export function read(form) {
  const v = n => (form.querySelector(`[name="pref.${n}"]`) || {}).value || '';
  try {
    const locale = compose({lang: v('lang'), ca: v('ca'), nu: v('nu'), hc: v('hc'), fw: v('fw'), tz: v('tz')});
    const out = {locale};
    if (v('date')) out.date = v('date');
    if (v('currency')) out.currency = v('currency');
    return {value: out};
  } catch (e) {
    return {error: say('prefs-bad', {}, {why: String(e.message || e)})};
  }
}

// THE SAMPLE: a day, a time, an amount and a number as the choice in the panel shows them — drawn with the widgets
// themselves, the reader's settings set to the choice for the moment of drawing and put back after
export function sample(el, value, o = {}) {
  const was = {locale: settings.locale, zone: settings.readerZone, date: settings.date, currency: settings.currency};
  configure({reader: {...value, zone: zoneOf(split(value.locale).tz, o.zones)}});
  const day = settings.asOf || new Date().toISOString().slice(0, 10), at = `${day}T13:05:00Z`;
  mount(el, h`<span class="w-prefs-s" data-s="day">${moment.show(day, {style: 'long'})}</span> · <span class="w-prefs-s" data-s="time">${moment.show(at)}</span> · <span class="w-prefs-s" data-s="amount">${money.show('1234.50', o.currency || 'EUR')}</span> · <span class="w-prefs-s" data-s="number">${number.show('1234567.89')}</span>`);
  configure({reader: was});
}

// THE PANEL IN AN ELEMENT: drawn, its sample redrawn at each change, and `save(value)` — a Promise of {ok} or
// {error} — asked when the reader saves; `done()` when they save or cancel
export function open(el, current, o = {}, save, done) {
  mount(el, panel(current, o));
  const form = el.querySelector('form'), out = el.querySelector('.w-prefs-sample'), err = el.querySelector('.w-prefs-error');
  const redraw = () => { const r = read(form); err.textContent = r.error || ''; if (r.value) sample(out, r.value, o); };
  form.addEventListener('change', redraw);
  redraw();
  form.querySelector('[data-prefs="cancel"]').addEventListener('click', () => done && done(false));
  form.querySelector('[data-prefs="save"]').addEventListener('click', () => {
    const r = read(form);
    if (r.error) { err.textContent = r.error; return; }
    Promise.resolve(save(r.value)).then(a => {
      if (a && a.error) { err.textContent = a.error; return; }
      if (done) done(true, r.value);
    });
  });
}
