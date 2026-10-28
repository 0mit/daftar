// number (types tree: number, count, fraction): a value exactly, never through a float. The wire form is the law's: a
// count as written (`-1950`, `260.50`), or the exact fraction n/d (`9650/3`) when a read value's decimals do not end.
// Shown in Persian digits, grouped, in a left-to-right isolate holding only number characters (TEXT.md rule 2).
import { h, Safe, LRI, PDI, isolated, BIDI_CONTROLS } from './safe.js';
import { settings } from './settings.js';
const IMPL = 'number';
export { IMPL as implements };
const FA = '۰۱۲۳۴۵۶۷۸۹';
export const MINUS = '−';
export function parse(v) {
  const s = String(v ?? '').trim();
  let m = s.match(/^(-?)(\d+)\/(\d+)$/);
  if (m) {
    const n = BigInt(m[2]), d = BigInt(m[3]);
    if (d === 0n) return null;
    return {neg: m[1] === '-' && n !== 0n, whole: n / d, rest: n % d, den: d, decimals: ''};
  }
  m = s.match(/^(-?)(\d+)(?:\.(\d+))?$/);
  if (!m) return null;
  return {neg: m[1] === '-' && /[1-9]/.test(m[2] + (m[3] || '')), whole: BigInt(m[2]), rest: 0n, den: 1n, decimals: m[3] || ''};
}
const digitsIn = (s, o) => (o.digits || (settings.lang === 'fa' ? 'fa' : 'latn')) === 'latn' ? String(s) : String(s).replace(/[0-9]/g, d => FA[d]);
const seps = o => (o.digits || (settings.lang === 'fa' ? 'fa' : 'latn')) === 'latn' ? {group: ',', decimal: '.'} : {group: '٬', decimal: '٫'};
function ending(p, places) {          // a fraction that ends at the given places is those decimals (2/8 at 2 places: 0.25)
  if (!p.rest || places === undefined) return p;
  const scale = 10n ** BigInt(places);
  if ((p.rest * scale) % p.den) return p;
  return {...p, rest: 0n, den: 1n, decimals: String(p.rest * scale / p.den).padStart(places, '0')};
}
export function parts(v, o = {}) {
  let p = parse(v);
  if (!p) return null;
  p = ending(p, o.places);
  const sep = seps(o);
  let decimals = p.decimals;
  if (o.places !== undefined && !p.rest && decimals.length < o.places) decimals = decimals.padEnd(o.places, '0');
  const grouped = o.group === false ? String(p.whole) : String(p.whole).replace(/\B(?=(\d{3})+(?!\d))/g, '\u0001');
  return {neg: p.neg, whole: digitsIn(grouped, o).replace(/\u0001/g, sep.group), decimal: decimals ? sep.decimal + digitsIn(decimals, o) : '',
          num: p.rest ? digitsIn(String(p.rest), o) : '', den: p.rest ? digitsIn(String(p.den), o) : '',
          showWhole: !p.rest || p.whole !== 0n, uneven: Boolean(p.rest)};
}
// options: digits 'fa'|'latn'; group; places; fraction 'mixed'|'math'|'inline'; className
export function show(v, o = {}) {
  const p = parts(v, o);
  if (!p) return h`<bdi class="w-num w-bad">${v ?? '—'}</bdi>`;
  let frac = '';
  if (p.uneven) {
    frac = (o.fraction || 'mixed') === 'inline'
      ? h`<span class="w-inline">${p.num}⁄${p.den}</span>`
      : h`<span class="w-frac"><span class="w-n">${p.num}</span><span class="w-x">⁄</span><span class="w-d">${p.den}</span></span>`;
  }
  const gap = p.uneven && p.showWhole ? ' ' : '';
  const label = (p.neg ? MINUS : '') + (p.showWhole ? p.whole + p.decimal : '') + gap + (p.uneven ? p.num + '/' + p.den : '');
  return h`<bdi dir="ltr" class="w-num${o.className ? ' ' + o.className : ''}" aria-label="${label}">${p.neg ? MINUS : ''}${p.showWhole ? p.whole + p.decimal : ''}${gap}${frac}</bdi>`;
}
// a count inside running text its caller escapes and isolates (a badge): the characters alone, or null
export function plain(v, o = {}) {
  const p = parts(String(v ?? ''), o);
  if (!p) return null;
  return (p.neg ? MINUS : '') + (p.showWhole ? p.whole + p.decimal : '') + (p.uneven ? (p.showWhole ? ' ' : '') + p.num + '/' + p.den : '');
}
export const count = v => plain(v) ?? String(v ?? '');
export function text(v, o = {}) {
  const p = parts(v, o);
  if (!p) return isolated(v);
  return LRI + (p.neg ? MINUS : '') + (p.showWhole ? p.whole + p.decimal : '') + (p.uneven ? (p.showWhole ? ' ' : '') + p.num + '/' + p.den : '') + PDI;
}
// what a person typed, as the law writes a count (lines.yaml types: count), or a refusal in words
export function take(input, o = {}) {
  let s = String(input ?? '').trim().replace(/[۰-۹]/g, d => FA.indexOf(d)).replace(/[٠-٩]/g, d => '٠١٢٣٤٥٦٧٨٩'.indexOf(d))
    .replace(BIDI_CONTROLS, '').replace(/^[−]/, '-').replace(/٫/g, '.');
  if (s === '' && !o.required) return {value: ''};
  if (/[٬,]/.test(s)) {
    if (!/^-?\d{1,3}([٬,]\d{3})+(\.\d+)?$/.test(s)) return {error: 'جداکنندهٔ هزارگان سر جایش نیست.'};
    s = s.replace(/[٬,]/g, '');
  }
  if (!/^-?(0|[1-9]\d{0,39})(\.\d{1,40})?$/.test(s)) return {error: 'عدد را با رقم و حداکثر یک ممیز بنویسید.'};
  if (o.places !== undefined && (s.split('.')[1] || '').length > o.places) return {error: `حداکثر ${digitsIn(String(o.places), o)} رقم اعشار.`};
  if (o.positive && (s.startsWith('-') || /^0(\.0+)?$/.test(s))) return {error: 'باید بزرگ‌تر از صفر باشد.'};
  return {value: s.replace(/^-0(\.0+)?$/, '0')};
}
export function edit(name, value, o = {}) {
  const shown = value === undefined || value === null || value === '' ? '' : plain(value, {group: false, digits: o.digits}) ?? value;
  return h`<input class="w-input w-num-input" name="${name}" dir="ltr" inputmode="decimal" autocomplete="off" value="${shown}"${o.required ? new Safe(' required') : ''}>`;
}
