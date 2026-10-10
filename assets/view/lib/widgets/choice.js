// choice (core/law/values.yaml: choice, choices, code): a row of a table, shown by its label, written by its key. The
// table is given as [{value, label}] or {value: label}; nothing is kept here.
import { h } from './safe.js';
import { say } from './locale.js';
const IMPL = 'choice';
export { IMPL as implements };
export const rows = table => Array.isArray(table) ? table.map(r => typeof r === 'object' ? r : {value: r, label: r})
  : Object.entries(table || {}).map(([value, label]) => ({value, label}));
export const label = (v, table) => (rows(table).find(r => String(r.value) === String(v)) || {}).label ?? v;
export function show(v, table, o = {}) {
  if (v === null || v === undefined || v === '') return h`<span class="w-none">${o.empty ?? '—'}</span>`;
  return h`<span class="w-choice${o.badge ? ' badge' : ''}${o.tone ? ' ' + o.tone : ''}">${label(v, table)}</span>`;
}
export const text = (v, table) => '\u2068' + String(label(v, table) ?? '') + '\u2069';
// a row {disabled: true} is shown and never taken (a heading among the rows: an account that only groups others)
export function take(input, table, o = {}) {
  const v = String(input ?? '');
  if (!v) return o.required ? {error: say('choose-one', o)} : {value: ''};
  return rows(table).some(r => String(r.value) === v && !r.disabled) || o.free ? {value: v} : {error: say('not-listed', o)};
}
// options: required; none (the empty choice's words); placeholder (an empty first choice that asks, even when required)
export function edit(name, value, table, o = {}) {
  const opts = rows(table);
  return h`<select class="w-input w-choice-input" name="${name}">${o.required && o.placeholder === undefined ? '' : h`<option value="">${o.placeholder ?? o.none ?? '—'}</option>`}${opts.map(r =>
    h`<option value="${r.value}"${String(r.value) === String(value ?? '') ? h` selected` : ''}${r.disabled ? h` disabled` : ''}>${r.label}</option>`)}</select>`;
}
