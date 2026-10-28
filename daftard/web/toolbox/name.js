// name (types tree: name): a name a namespace gives (a phone number, an e-mail address, an id), shown left to right
// as its namespace writes it, so a phone's groups never reverse in a right-to-left page (the case found in review).
import { h, BIDI_CONTROLS } from './safe.js';
const IMPL = 'name';
export { IMPL as implements };
const FA = '۰۱۲۳۴۵۶۷۸۹';
const ascii = s => String(s).replace(/[۰-۹]/g, d => FA.indexOf(d)).replace(/[٠-٩]/g, d => '٠١٢٣٤٥٦٧٨٩'.indexOf(d));
// options: kind 'phone'|'email'|'id'; link (tel:/mailto:)
export function show(v, o = {}) {
  const s = String(v ?? '').trim();
  if (!s) return h`<span class="w-none">—</span>`;
  const shown = o.kind === 'phone' ? ascii(s) : s;
  const href = o.link && o.kind === 'phone' ? 'tel:' + shown.replace(/[^\d+]/g, '') : o.link && o.kind === 'email' ? 'mailto:' + shown : '';
  return href ? h`<a class="w-name" dir="ltr" href="${href}">${shown}</a>` : h`<bdi dir="ltr" class="w-name">${shown}</bdi>`;
}
export const text = v => '\u2066' + String(v ?? '') + '\u2069';
export function take(input, o = {}) {
  let s = ascii(String(input ?? '').trim()).replace(BIDI_CONTROLS, '');
  if (!s) return o.required ? {error: 'این بخش لازم است.'} : {value: ''};
  if (o.kind === 'phone') {
    s = s.replace(/\s+/g, ' ');
    return /^\+?[\d ()-]{6,24}$/.test(s) ? {value: s} : {error: 'شماره را با رقم بنویسید (مثلاً +90 532 123 45 67).'};
  }
  if (o.kind === 'email') return /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(s) ? {value: s} : {error: 'نشانی ایمیل درست نیست.'};
  return {value: s};
}
export const edit = (name, value, o = {}) =>
  h`<input class="w-input w-name-input" name="${name}" dir="ltr" type="${o.kind === 'email' ? 'email' : o.kind === 'phone' ? 'tel' : 'text'}" autocomplete="off" value="${value ?? ''}">`;
