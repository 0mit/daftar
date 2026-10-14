// money (core/law/values.yaml: money, a quantity): the number widget is its digits, at the currency's places
// (quantities.yaml money: units_from currencies, digits); the currency's label stays outside the number's isolate, in
// the sentence's own direction.
//
// AT THE CURRENCY'S PLACES, ROUNDED FOR THE EYE (the operator, 2026-10-14): an amount that does not end at its
// currency's places is shown rounded to them, half away from zero, with a mark whose title says so and gives the exact
// amount. Only the showing rounds: what is kept, summed and compared is the exact amount (exact.js, n/d where it is
// uneven), and who takes a remainder stays a clause of the agreement, never arithmetic. A unit with no places (none
// known for it) is shown exactly, the fraction it is; `exact: true` asks the exact anywhere.
import { h } from './safe.js';
import { settings } from './settings.js';
import { langOf, say } from './locale.js';
import * as number from './number.js';
const IMPL = 'money';
export { IMPL as implements };
const names = {};
function nameOf(code, lang) {
  try { return (names[lang] ||= new Intl.DisplayNames([lang], {type: 'currency'})).of(code); } catch { return code; }
}
// a currency's symbol as the reader's language writes it (CLDR, through Intl), or its code where none
function symbolOf(code, lang, display) {
  try {
    const p = new Intl.NumberFormat(lang, {style: 'currency', currency: code, currencyDisplay: display}).formatToParts(1).find(x => x.type === 'currency');
    return p ? p.value : code;
  } catch { return code; }
}
// how a currency is named: the option, else the reader's choice (`settings.currency`), else its code
function labelOf(unit, o) {
  const how = o.label || settings.currency || 'code';
  if (!unit || how === 'none') return '';
  if (how === 'name') return nameOf(unit, langOf(o));
  if (how === 'symbol' || how === 'narrowSymbol') return symbolOf(unit, langOf(o), how);
  return unit;
}
export const places = unit => settings.places[unit];
// the amount at `places`, rounded half away from zero, as the law writes a count; null where it ends there already
export function rounded(v, places) {
  const p = number.parse(v);
  if (!p || places === undefined) return null;
  let n = p.whole * p.den + p.rest, d = p.den;
  if (p.decimals) {
    d = 10n ** BigInt(p.decimals.length);
    n = p.whole * d + BigInt(p.decimals);
  }
  const scale = 10n ** BigInt(places);
  if ((n * scale) % d === 0n) return null;
  const q = n * scale / d + (2n * ((n * scale) % d) >= d ? 1n : 0n);
  const s = q.toString().padStart(places + 1, '0');
  const neg = p.neg && q !== 0n ? '-' : '';
  return neg + (places ? s.slice(0, -places) + '.' + s.slice(-places) : s);
}
// options: label 'code'|'name'|'none'; abs (no sign); everything number.show takes
export function show(v, unit, o = {}) {
  const at = o.places ?? settings.places[unit];
  const value = o.abs ? String(v ?? '').trim().replace(/^-/, '') : v;
  const round = o.exact ? null : rounded(value, at);
  let flag = '';
  if (round !== null) {
    const said = say('rounded', o, {exact: number.count(value, o)});
    flag = h`<span class="w-uneven w-rounded" title="${said}" aria-label="${said}">*</span>`;
  } else {
    const p = number.parts(value, {...o, places: at});
    const said = say('uneven', o);
    flag = p && p.uneven ? h`<span class="w-uneven" title="${said}" aria-label="${said}">*</span>` : '';
  }
  const n = number.show(round ?? value, {...o, places: at});
  const label = labelOf(unit, o);
  return label ? h`<span class="w-money">${n}${flag} <span class="w-unit">${label}</span></span>` : h`<span class="w-money">${n}${flag}</span>`;
}
export function text(v, unit, o = {}) {
  const label = labelOf(unit, o), at = o.places ?? settings.places[unit];
  return number.text((o.exact ? null : rounded(v, at)) ?? v, {...o, places: at}) + (label ? ' ' + label : '');
}
export const take = (input, unit, o = {}) => number.take(input, {...o, places: settings.places[unit]});
export const edit = (name, value, unit, o = {}) => number.edit(name, value, o);
export const negative = v => (number.parse(v) || {}).neg === true;
export const uneven = (v, unit) => Boolean((number.parts(v, {places: settings.places[unit]}) || {}).uneven);
export const sign = v => { const p = number.parse(v); return !p ? 0 : p.neg ? -1 : (p.whole || p.rest || /[1-9]/.test(p.decimals)) ? 1 : 0; };
