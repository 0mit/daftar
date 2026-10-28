// The handplace's calls to daftard: reads, saves (with the session's CSRF token, the head the form was opened at and a
// request id that a retry reuses, so a lost answer never saves twice), and the garden's change events (server-sent:
// a page reads again only when its garden changed, and not while hidden).
import { GuidedError } from './guided.js';
import { log, timed } from './log.js';
import { T } from './say.js';
const session = {csrf: '', head: ''};
export const setSession = data => { if (data?.csrf) session.csrf = data.csrf; if (data?.head) session.head = data.head; };
// the garden a page reads: the one its landing address names (/go/<garden>/…), else ?g=, else the machine's first
export const gardenName = () => {
  const m = /^\/go\/([^/?#]+)/.exec(location.pathname);
  return m ? decodeURIComponent(m[1]) : new URLSearchParams(location.search).get('g');
};
const withGarden = path => {
  const g = gardenName();
  return g ? path + (path.includes('?') ? '&' : '?') + 'g=' + encodeURIComponent(g) : path;
};
function call(path, init) { return timed(`${init?.method || 'GET'} ${path}`, () => doCall(path, init)); }
// A write a garden refuses for want of a sitting (409, `sitting`: it takes only its people's own signed writes) asks
// who is at the keyboard (sitting.js), and is made again, once, when a sitting is begun.
let askSitting = null;
export const whenSittingAsked = fn => { askSitting = fn; };
async function doCall(path, init) {
  let r;
  try { r = await fetch(withGarden(path), init); }
  catch { throw new GuidedError({message: T('به دفتر دسترسی نیست: برنامهٔ دفتر روی این رایانه اجرا نمی‌شود یا دوباره راه می‌افتد. چند لحظه بعد دوباره تلاش کنید.', 'The garden cannot be reached: daftar is not running on this machine, or is starting again. Try again in a moment.')}); }
  let j = {};
  try { j = await r.json(); } catch { /* an answer that is not JSON is said below */ }
  log('←', path, r.status, r.headers.get('content-length') || '', j.ref ? 'ref ' + j.ref : '');
  if (r.status === 409 && j.sitting && askSitting && !init?.again && await askSitting()) return doCall(path, {...init, again: true});
  if (!r.ok) throw new GuidedError({message: j.message || j.error || T(`انجام نشد (${r.status}).`, `It did not go ahead (${r.status}).`), ref: j.ref, followUp: j.followUp, status: r.status});
  return j;
}
export const get = path => call(path, {cache: 'no-store'});
export const newRequest = () => crypto.randomUUID().replace(/-/g, '');
// save one change; `request` is the form's own id (reused on a retry), `head` the commit the form was opened at
export function save(kind, bean, values, {head, request} = {}) {
  const body = {kind, bean, values, head: head || session.head, request: request || newRequest()};
  return call('/api/save', {method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRF-Token': session.csrf}, body: JSON.stringify(body)});
}
// a write whose refusal is the page's to show at the facts it names (a sheet's Save): {status, answer} — the answer
// JSON whatever the status, a failure to reach daftard thrown as the guided error it is; a garden that takes only signed
// writes asks who sits here first, as every save does
export async function postRaw(path, body = {}, again = false) {
  let r;
  try { r = await fetch(withGarden(path), {method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRF-Token': session.csrf}, body: JSON.stringify(body)}); }
  catch { throw new GuidedError({message: T('به دفتر دسترسی نیست: برنامهٔ دفتر روی این رایانه اجرا نمی‌شود یا دوباره راه می‌افتد. چند لحظه بعد دوباره تلاش کنید.', 'The garden cannot be reached: daftar is not running on this machine, or is starting again. Try again in a moment.')}); }
  let j = {};
  try { j = await r.json(); } catch { /* said by the status */ }
  log('←', path, r.status, j.ref ? 'ref ' + j.ref : '');
  if (r.status === 409 && j.sitting && askSitting && !again && await askSitting()) return postRaw(path, body, true);
  return {status: r.status, answer: j};
}
export const post = (path, body = {}) =>
  call(path, {method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRF-Token': session.csrf}, body: JSON.stringify(body)});
// onChanged runs once per change, only when the page is seen and `busy()` (a form open) says no
export function events(onChanged, busy = () => false) {
  let pending = false;
  const catchUp = () => { if (pending && !document.hidden && !busy()) { pending = false; log('events', 'reading the garden again'); onChanged(); } };
  try {
    const es = new EventSource(withGarden('/api/events'));
    es.addEventListener('head', e => log('events', 'connected at', e.data.slice(0, 12)));
    es.addEventListener('changed', e => { log('events', 'garden changed:', e.data.slice(0, 12), document.hidden ? '(hidden: later)' : busy() ? '(a form is open: later)' : ''); pending = true; catchUp(); });
  } catch { /* no events: the page still reads on demand */ }
  document.addEventListener('visibilitychange', catchUp);
  return catchUp;
}
