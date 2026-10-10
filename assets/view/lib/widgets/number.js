// number (core/law/values.yaml: number, count, fraction): a value exactly, never through a float. The wire form is
// the law's: a count as written (`-1950`, `260.50`), or the exact fraction n/d (`9650/3`) when a read value's decimals
// do not end. Shown in the reader's digits and separators (CLDR, through Intl), grouped, in a left-to-right isolate
// holding only number characters.
import { h, Safe, LRI, PDI, isolated, BIDI_CONTROLS } from './safe.js';
import { digitsOf, inDigits, separators, toAscii, say } from './locale.js';
const IMPL = 'number';
export { IMPL as implements };
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
  const ns = digitsOf(o), sep = separators(o);
  let decimals = p.decimals;
  if (o.places !== undefined && !p.rest && decimals.length < o.places) decimals = decimals.padEnd(o.places, '0');
  const grouped = o.group === false ? String(p.whole) : String(p.whole).replace(/\B(?=(\d{3})+(?!\d))/g, '\u0001');
  return {neg: p.neg, whole: inDigits(grouped, ns).replace(/\u0001/g, sep.group),
          decimal: decimals ? sep.decimal + inDigits(decimals, ns) : '',
          num: p.rest ? inDigits(String(p.rest), ns) : '', den: p.rest ? inDigits(String(p.den), ns) : '',
          showWhole: !p.rest || p.whole !== 0n, uneven: Boolean(p.rest)};
}
// options: digits (a numbering system: latn, arabext …); lang; group; places; fraction 'mixed'|'math'|'inline'; className
export function show(v, o = {}) {
  const p = parts(v, o);
  if (!p) return h`<bdi class="w-num w-bad">${v ?? '—'}</bdi>`;
  let frac = '';
  if (p.uneven) {
    frac = (o.fraction || 'mixed') === 'inline'
      ? h`<span class="w-inline">${p.num}⁄${p.den}</span>`
      : h`<span class="w-frac"><span class="w-n">${p.num}</span><span class="w-x">⁄</span><span class="w-d">${p.den}</span></span>`;
  }
  const gap = p.uneven && p.showWhole ? ' ' : '';
  const label = (p.neg ? MINUS : '') + (p.showWhole ? p.whole + p.decimal : '') + gap + (p.uneven ? p.num + '/' + p.den : '');
  return h`<bdi dir="ltr" class="w-num${o.className ? ' ' + o.className : ''}" aria-label="${label}">${p.neg ? MINUS : ''}${p.showWhole ? p.whole + p.decimal : ''}${gap}${frac}</bdi>`;
}
// a count inside running text its caller escapes and isolates (a badge): the characters alone, or null
export function plain(v, o = {}) {
  const p = parts(String(v ?? ''), o);
  if (!p) return null;
  return (p.neg ? MINUS : '') + (p.showWhole ? p.whole + p.decimal : '') + (p.uneven ? (p.showWhole ? ' ' : '') + p.num + '/' + p.den : '');
}
export const count = (v, o = {}) => plain(v, o) ?? String(v ?? '');
export function text(v, o = {}) {
  const p = parts(v, o);
  if (!p) return isolated(v);
  return LRI + (p.neg ? MINUS : '') + (p.showWhole ? p.whole + p.decimal : '') + (p.uneven ? (p.showWhole ? ' ' : '') + p.num + '/' + p.den : '') + PDI;
}
const re = c => c.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
// what a person typed, as the law writes a count (lines.yaml types: count), or a refusal in words. Digits of any
// numbering system are read; the separators are the reader's language's, and the ASCII `.` and `,` where that
// language does not use them the other way round.
export function take(input, o = {}) {
  const sep = separators(o);
  const decimals = new Set([sep.decimal, ...(sep.group === '.' ? [] : ['.'])]);
  const groups = new Set([sep.group, ...(sep.decimal === ',' ? [] : [',']), ...(/\s/.test(sep.group) ? [' ', ' ', ' '] : [])]);
  let s = toAscii(String(input ?? '').trim()).replace(BIDI_CONTROLS, '').replace(/^[−]/, '-');
  if (s === '' && !o.required) return {value: ''};
  const g = `[${[...groups].map(re).join('')}]`, d = `[${[...decimals].map(re).join('')}]`;
  if (new RegExp(g).test(s)) {
    if (!new RegExp(`^-?\\d{1,3}(${g}\\d{3})+(${d}\\d+)?$`).test(s)) return {error: say('number-group', o)};
    s = s.replace(new RegExp(g, 'g'), '');
  }
  s = s.replace(new RegExp(d), '.');
  if (!/^-?(0|[1-9]\d{0,39})(\.\d{1,40})?$/.test(s)) return {error: say('number-form', o)};
  if (o.places !== undefined && (s.split('.')[1] || '').length > o.places) {
    return {error: say('number-places', o, {n: inDigits(String(o.places), digitsOf(o))})};
  }
  if (o.positive && (s.startsWith('-') || /^0(\.0+)?$/.test(s))) return {error: say('number-positive', o)};
  return {value: s.replace(/^-0(\.0+)?$/, '0')};
}
export function edit(name, value, o = {}) {
  const shown = value === undefined || value === null || value === '' ? '' : plain(value, {...o, group: false}) ?? value;
  return h`<input class="w-input w-num-input" name="${name}" dir="ltr" inputmode="decimal" autocomplete="off" value="${shown}"${o.required ? new Safe(' required') : ''}>`;
}
