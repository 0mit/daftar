// Debug mode: verbose, grouped console logs of what the page does — every read and save (path, status, size, time),
// every change event, every render and action, every guided error's reference. On with ?debug=1 (remembered in this
// browser until ?debug=0); off, it costs nothing. In debug mode the page's state is window.daftar.
const KEY = 'daftar.debug';
function initial() {
  const q = new URLSearchParams(location.search).get('debug');
  try {
    if (q === '1') localStorage.setItem(KEY, '1');
    if (q === '0') localStorage.removeItem(KEY);
    return localStorage.getItem(KEY) === '1';
  } catch { return q === '1'; }
}
export const debug = typeof location !== 'undefined' && initial();
const t0 = typeof performance !== 'undefined' ? performance.now() : 0;
const stamp = () => `[daftar +${((performance.now() - t0) / 1000).toFixed(2)}s]`;
export function log(topic, ...args) { if (debug) console.log(stamp(), topic, ...args); }
export function warn(topic, ...args) { if (debug) console.warn(stamp(), topic, ...args); }
// time an async step: its result is returned, its duration logged
export async function timed(topic, fn) {
  if (!debug) return fn();
  const s = performance.now();
  try { const r = await fn(); console.log(stamp(), topic, `${(performance.now() - s).toFixed(0)} ms`); return r; }
  catch (e) { console.warn(stamp(), topic, 'failed', `${(performance.now() - s).toFixed(0)} ms`, e?.ref || '', e); throw e; }
}
export function expose(name, value) { if (debug) (window.daftar ||= {})[name] = value; }
