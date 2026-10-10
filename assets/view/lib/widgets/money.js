// money (core/law/values.yaml: money, a quantity): the number widget is its digits, at the currency's places
// (quantities.yaml money: units_from currencies, digits); the currency's label stays outside the number's isolate, in
// the sentence's own direction. An amount that does not come out even in those places is shown as the fraction it is
// and says so, never rounded: who takes the remainder is a clause, not arithmetic.
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
const labelOf = (unit, o) => !unit || o.label === 'none' ? '' : o.label === 'name' ? nameOf(unit, langOf(o)) : unit;
export const places = unit => settings.places[unit];
// options: label 'code'|'name'|'none'; abs (no sign); everything number.show takes
export function show(v, unit, o = {}) {
  const at = o.places ?? settings.places[unit];
  const value = o.abs ? String(v ?? '').trim().replace(/^-/, '') : v;
  const p = number.parts(value, {...o, places: at});
  const n = number.show(value, {...o, places: at});
  const said = say('uneven', o);
  const flag = p && p.uneven ? h`<span class="w-uneven" title="${said}" aria-label="${said}">*</span>` : '';
  const label = labelOf(unit, o);
  return label ? h`<span class="w-money">${n}${flag} <span class="w-unit">${label}</span></span>` : h`<span class="w-money">${n}${flag}</span>`;
}
export function text(v, unit, o = {}) {
  const label = labelOf(unit, o);
  return number.text(v, {...o, places: o.places ?? settings.places[unit]}) + (label ? ' ' + label : '');
}
export const take = (input, unit, o = {}) => number.take(input, {...o, places: settings.places[unit]});
export const edit = (name, value, unit, o = {}) => number.edit(name, value, o);
export const negative = v => (number.parse(v) || {}).neg === true;
export const uneven = (v, unit) => Boolean((number.parts(v, {places: settings.places[unit]}) || {}).uneven);
export const sign = v => { const p = number.parse(v); return !p ? 0 : p.neg ? -1 : (p.whole || p.rest || /[1-9]/.test(p.decimals)) ? 1 : 0; };
