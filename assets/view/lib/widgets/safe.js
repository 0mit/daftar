// The one way HTML is built and put into a page (escaping by context, every value isolated). h`...${value}...`
// escapes every interpolation unless it is Safe (a widget's output); mount() is the only door into the page's HTML.
// Every bidi control character is written here as an escape, never as itself: an invisible character in source is
// Trojan Source's tool (CVE-2021-42574), and the release's own test refuses one.
export class Safe {
  constructor(html) { this.html = html; }
  toString() { return this.html; }
}
const ESC = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'};
export function escape(v) {
  if (v instanceof Safe) return v.html;
  if (Array.isArray(v)) return v.map(escape).join('');
  if (v === null || v === undefined || v === false) return '';
  return String(v).replace(/[&<>"']/g, c => ESC[c]);
}
export const h = (strings, ...values) => new Safe(strings.reduce((out, s, i) => out + s + (i < values.length ? escape(values[i]) : ''), ''));
export const join = (parts, sep = '') => new Safe(parts.map(escape).join(escape(sep)));
export const isSafe = v => v instanceof Safe;
export function mount(el, safe) {
  if (!(safe instanceof Safe)) throw new TypeError('mount takes only Safe HTML (widgets/lib/safe.js h``)');
  el.innerHTML = safe.html;
  if (el.querySelectorAll) place(el);
}
// A position a page computes (a session's place on a timetable) cannot be a style attribute where the page's CSP
// allows none. It is written as data-gc (grid-column), data-gr (grid-row) or data-rows (grid-template-rows) and set by
// mount through the CSSOM. A value that is not a grid-line expression is left unset.
const GRID = /^[0-9a-z ()\/,.+-]{1,80}$/;
const PLACES = {gc: 'gridColumn', gr: 'gridRow', rows: 'gridTemplateRows'};
export function place(root) {
  for (const el of root.querySelectorAll('[data-gc],[data-gr],[data-rows]')) {
    for (const [key, prop] of Object.entries(PLACES)) if (el.dataset[key] && GRID.test(el.dataset[key])) el.style[prop] = el.dataset[key];
  }
}
// plain text has no markup: a value goes between FSI and PDI (LRI … PDI for a number), so it cannot reorder the line
export const FSI = '\u2068', LRI = '\u2066', RLI = '\u2067', PDI = '\u2069';
export const isolated = v => FSI + String(v ?? '') + PDI;
// Unicode's Bidi_Control (PropList.txt): never part of a number, an id or a code (core/law/lines.yaml, `coding`)
export const BIDI_CONTROLS = /[\u061C\u200E\u200F\u202A-\u202E\u2066-\u2069]/g;
