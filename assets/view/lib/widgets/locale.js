// How a reader's language writes what a widget shows, and reads what a person types: its digits, its separators, its
// calendar, its direction and its words for today and its neighbours — each from the runtime's own CLDR data (Intl),
// never from a table kept here, so that no language, script, calendar or digit is privileged (manifesto: sibling).
// What CLDR does not hold — a widget's own sentences — is the one table here (`SAID`): English, the law's language,
// and every language a sentence has been written in; a sentence not yet written in the reader's language is said in
// English.
import { settings } from './settings.js';

const cache = new Map();
const once = (key, make) => { if (!cache.has(key)) cache.set(key, make()); return cache.get(key); };

// the reader's language: the option, the garden's setting, the page's own, else the runtime's
export function langOf(o = {}) {
  if (o.lang) return o.lang;
  if (settings.lang) return settings.lang;
  const page = typeof document !== 'undefined' && document.documentElement && document.documentElement.lang;
  return page || new Intl.DateTimeFormat().resolvedOptions().locale;
}

// the numbering system a number is shown in: the option (`latn`, `arabext`, `arab`, `deva` …), else the language's own
export function digitsOf(o = {}) {
  if (o.digits) return o.digits;
  const lang = langOf(o);
  return once(`ns|${lang}`, () => new Intl.NumberFormat(lang).resolvedOptions().numberingSystem);
}

// the ten digits of a numbering system, 0 to 9, as CLDR writes them
export function glyphs(ns) {
  return once(`glyphs|${ns}`, () => {
    const nf = new Intl.NumberFormat(`en-u-nu-${ns}`, {useGrouping: false});
    return Array.from({length: 10}, (_, d) => nf.format(d));
  });
}

// ASCII digits written in a numbering system
export const inDigits = (s, ns) => ns === 'latn' ? String(s) : String(s).replace(/[0-9]/g, d => glyphs(ns)[d]);

// a language's grouping and decimal separators, in the numbering system shown
export function separators(o = {}) {
  const lang = langOf(o), ns = digitsOf(o);
  return once(`sep|${lang}|${ns}`, () => {
    const parts = new Intl.NumberFormat(`${lang}-u-nu-${ns}`).formatToParts(1234567.5);
    return {group: (parts.find(p => p.type === 'group') || {}).value || ',',
            decimal: (parts.find(p => p.type === 'decimal') || {}).value || '.'};
  });
}

// every decimal digit of every numbering system the runtime knows, mapped to ASCII: what a person types is read in
// whatever digits they type it in
const DIGIT = once('digits', () => {
  const map = new Map();
  const systems = typeof Intl.supportedValuesOf === 'function' ? Intl.supportedValuesOf('numberingSystem') : ['latn'];
  for (const ns of systems) {
    let g;
    try { g = glyphs(ns); } catch { continue; }
    if (g.every(c => [...c].length === 1)) g.forEach((c, d) => { if (!map.has(c)) map.set(c, String(d)); });
  }
  return map;
});
export const toAscii = s => [...String(s ?? '')].map(c => DIGIT.get(c) ?? c).join('');

// the calendar a day is shown in: the option, the garden's setting, else the language's own (CLDR)
export function calendarOf(o = {}) {
  if (o.calendar) return o.calendar;
  if (settings.calendar) return settings.calendar;
  const lang = langOf(o);
  return once(`cal|${lang}`, () => new Intl.DateTimeFormat(lang).resolvedOptions().calendar);
}

// a language's direction, from CLDR's layout of its script
export function dirOf(lang) {
  if (!lang) return 'auto';
  return once(`dir|${lang}`, () => {
    try {
      const L = new Intl.Locale(lang);
      const info = typeof L.getTextInfo === 'function' ? L.getTextInfo() : L.textInfo;
      if (info && info.direction) return info.direction;
    } catch { /* a tag the runtime does not read: its direction is the text's own */ }
    return 'auto';
  });
}

// yesterday, today, tomorrow in the reader's language (CLDR's relative day names), or null for another day
export function relativeDay(diff, o = {}) {
  if (![-1, 0, 1].includes(diff)) return null;
  const lang = langOf(o);
  return once(`rel|${lang}|${diff}`, () => new Intl.RelativeTimeFormat(lang, {numeric: 'auto'}).format(diff, 'day'));
}

// THE WIDGETS' OWN SENTENCES, by key, in each language one has been written in. A value in a sentence is passed in
// `vars` and written by its widget's caller (a count in the reader's digits).
export const SAID = {
  required: {en: 'This is required.', fa: 'این بخش لازم است.'},
  'too-long': {en: 'At most {n} characters.', fa: 'حداکثر {n} نویسه.'},
  'number-group': {en: 'The thousands separator is out of place.', fa: 'جداکنندهٔ هزارگان سر جایش نیست.'},
  'number-form': {en: 'Write the number in digits, with at most one decimal separator.',
                  fa: 'عدد را با رقم و حداکثر یک ممیز بنویسید.'},
  'number-places': {en: 'At most {n} decimal places.', fa: 'حداکثر {n} رقم اعشار.'},
  'number-positive': {en: 'It must be more than zero.', fa: 'باید بزرگ‌تر از صفر باشد.'},
  uneven: {en: 'It does not come out even in this currency’s places: who takes the remainder is a clause of the agreement, not rounding.',
           fa: 'به رقم‌های اعشار این ارز سرراست نمی‌شود؛ اینکه باقی‌مانده با کیست را بند توافق می‌گوید، نه گرد کردن'},
  'day-required': {en: 'Write the day.', fa: 'تاریخ را بنویسید.'},
  'day-form': {en: 'Write the day as {example}, or as the law writes it, {written}.',
               fa: 'تاریخ را به شکل {example} بنویسید، یا آن‌طور که قانون می‌نویسد، {written}.'},
  'day-written': {en: 'In this calendar a day is taken as the law writes it: {written}.',
                  fa: 'در این تقویم، تاریخ را آن‌طور که قانون می‌نویسد بنویسید: {written}.'},
  'day-none': {en: 'There is no such day in this calendar.', fa: 'چنین روزی در این تقویم نیست.'},
  'time-required': {en: 'Write the time.', fa: 'ساعت را بنویسید.'},
  'time-form': {en: 'Write the time as {example}.', fa: 'ساعت را به شکل {example} بنویسید.'},
  'phone-form': {en: 'Write the number in digits (for example +90 532 123 45 67).',
                 fa: 'شماره را با رقم بنویسید (مثلاً +90 532 123 45 67).'},
  'email-form': {en: 'This is not a mail address.', fa: 'نشانی ایمیل درست نیست.'},
  'choose-one': {en: 'Choose one.', fa: 'یکی را انتخاب کنید.'},
  'not-listed': {en: 'This is not one of the list.', fa: 'این گزینه در فهرست نیست.'},
};
export function say(key, o = {}, vars = {}) {
  const row = SAID[key] || {};
  const lang = langOf(o), base = String(lang).split('-')[0];
  const s = row[lang] ?? row[base] ?? row.en ?? key;
  return s.replace(/\{(\w+)\}/g, (m, k) => (k in vars ? String(vars[k]) : m));
}
