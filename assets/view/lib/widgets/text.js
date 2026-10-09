// text (core/law/values.yaml: text): prose, isolated so it cannot reorder what is around it, its direction from its
// first strong character (dir="auto") unless its language is known (CLDR's layout of its script). Line breaks are
// kept. In inspect mode the bidi controls a value carries are shown («⟨RLO⟩»), so what a text does to its own display
// is visible; free text keeps them as written.
import { h, BIDI_CONTROLS } from './safe.js';
import { dirOf, say } from './locale.js';
const IMPL = 'text';
export { IMPL as implements };
const NAMES = {'\u200E': 'LRM', '\u200F': 'RLM', '\u061C': 'ALM', '\u202A': 'LRE', '\u202B': 'RLE', '\u202C': 'PDF',
  '\u202D': 'LRO', '\u202E': 'RLO', '\u2066': 'LRI', '\u2067': 'RLI', '\u2068': 'FSI', '\u2069': 'PDI'};
export const reveal = s => String(s ?? '').replace(BIDI_CONTROLS, c => `⟨${NAMES[c]}⟩`);
// options: lang (a BCP 47 tag: its direction is then known), inspect, lines (keep line breaks), empty (what nothing shows
// as), block (a paragraph of its own: aligned by its own direction)
export function show(v, o = {}) {
  const s = v === null || v === undefined ? '' : String(v);
  if (!s.trim()) return h`<span class="w-none">${o.empty ?? '—'}</span>`;
  const dir = o.lang ? dirOf(o.lang) : 'auto';
  const cls = 'w-text' + (o.lines ? ' w-lines' : '') + (o.block ? ' w-block' : '');
  return o.block
    ? h`<div dir="${dir}" class="${cls}"${o.lang ? h` lang="${o.lang}"` : ''}>${o.inspect ? reveal(s) : s}</div>`
    : h`<bdi dir="${dir}" class="${cls}"${o.lang ? h` lang="${o.lang}"` : ''}>${o.inspect ? reveal(s) : s}</bdi>`;
}
export const text = v => '\u2068' + String(v ?? '') + '\u2069';
export function take(input, o = {}) {
  const s = String(input ?? '').replace(/\r\n?/g, '\n');
  const v = o.lines ? s.split('\n').map(l => l.replace(/[ \t]+$/, '')).join('\n').trim() : s.trim();
  if (!v && o.required) return {error: say('required', o)};
  if (o.max && v.length > o.max) return {error: say('too-long', o, {n: o.max})};
  return {value: v};
}
// options: lines, max, suggest (words offered as the person types; anything else may still be written), placeholder
export function edit(name, value, o = {}) {
  if (o.lines) return h`<textarea class="w-input w-text-input" name="${name}" dir="auto" maxlength="${o.max || 5000}">${value ?? ''}</textarea>`;
  const list = o.suggest?.length ? 'w-suggest-' + name : '';
  return h`<input class="w-input w-text-input" name="${name}" dir="auto" maxlength="${o.max || 500}" value="${value ?? ''}"${list ? h` list="${list}"` : ''}${o.placeholder ? h` placeholder="${o.placeholder}"` : ''}>${list ? h`<datalist id="${list}">${o.suggest.map(s => h`<option value="${s}"></option>`)}</datalist>` : ''}`;
}
