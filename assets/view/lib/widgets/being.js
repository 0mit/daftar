// being (core/law/values.yaml: being): a bean, shown by its title and reached by its id. A page that can open it passes
// an action; the bean's id stays an attribute, never shown as the name.
import { h } from './safe.js';
const IMPL = 'being';
export { IMPL as implements };
export function show(id, title, o = {}) {
  const shown = title || id || '—';
  return o.action
    ? h`<button type="button" class="w-being text-button" data-action="${o.action}" data-id="${id ?? ''}"><bdi dir="auto">${shown}</bdi></button>`
    : h`<bdi dir="auto" class="w-being">${shown}</bdi>`;
}
export const text = (id, title) => '\u2068' + String(title || id || '') + '\u2069';
