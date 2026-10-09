// name (core/law/values.yaml: name): a name a namespace gives (a phone number, a mail address, an id), shown left to
// right as its namespace writes it, so a phone's groups never reverse in a right-to-left page.
import { h, BIDI_CONTROLS } from './safe.js';
import { toAscii, say } from './locale.js';
const IMPL = 'name';
export { IMPL as implements };
// options: kind 'phone'|'email'|'id'; link (tel:/mailto:)
export function show(v, o = {}) {
  const s = String(v ?? '').trim();
  if (!s) return h`<span class="w-none">—</span>`;
  const shown = o.kind === 'phone' ? toAscii(s) : s;
  const href = o.link && o.kind === 'phone' ? 'tel:' + shown.replace(/[^\d+]/g, '') : o.link && o.kind === 'email' ? 'mailto:' + shown : '';
  return href ? h`<a class="w-name" dir="ltr" href="${href}">${shown}</a>` : h`<bdi dir="ltr" class="w-name">${shown}</bdi>`;
}
export const text = v => '\u2066' + String(v ?? '') + '\u2069';
export function take(input, o = {}) {
  let s = toAscii(String(input ?? '').trim()).replace(BIDI_CONTROLS, '');
  if (!s) return o.required ? {error: say('required', o)} : {value: ''};
  if (o.kind === 'phone') {
    s = s.replace(/\s+/g, ' ');
    return /^\+?[\d ()-]{6,24}$/.test(s) ? {value: s} : {error: say('phone-form', o)};
  }
  if (o.kind === 'email') return /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(s) ? {value: s} : {error: say('email-form', o)};
  return {value: s};
}
export const edit = (name, value, o = {}) =>
  h`<input class="w-input w-name-input" name="${name}" dir="ltr" type="${o.kind === 'email' ? 'email' : o.kind === 'phone' ? 'tel' : 'text'}" autocomplete="off" value="${value ?? ''}">`;
