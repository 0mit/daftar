// Labels: every word a page shows that is not data — a section's name, a title, a button — is L(key, default). A
// label is ONE PERSON'S CUSTOMISATION of their own handplace (admin mode), never the garden's: a garden's names and
// data are its beans', shown by the value widgets and changed as data. What a person changes is kept for them alone,
// in the garden's repository beside its data (daftard internal/custom), so each machine they read on agrees.
//
// Each label holds the page's own word it replaced (`was`). When a page's own word has changed since, the label is
// one to look at again: admin mode marks it, and the person's list of their labels says so.
import { h } from './safe.js';
import { T } from './say.js';
const state = {labels: {}, admin: false};
const known = new Map();                 // key → the page's own word, for every label a page has offered
const KEY = 'daftar.admin';
export function configureLabels(data = {}, {admin} = {}) {
  if (data.labels) state.labels = data.labels;
  if (admin !== undefined) state.admin = admin;
}
export function adminFromUrl() {
  const q = new URLSearchParams(location.search).get('admin');
  try {
    if (q === '1') sessionStorage.setItem(KEY, '1');
    if (q === '0') sessionStorage.removeItem(KEY);
    return sessionStorage.getItem(KEY) === '1';
  } catch { return q === '1'; }
}
export const isAdmin = () => state.admin;
// a page's own word for a key, offered before it is shown (a page's name in the menu and its title)
export const offer = (key, fallback) => known.set(key, fallback);
// the label as plain text: for a document title, an attribute, a placeholder
export function Lt(key, fallback) { known.set(key, fallback); return state.labels[key]?.text || fallback; }
// a label whose page word changed since it was set
export const stale = (key, fallback) => Boolean(state.labels[key] && state.labels[key].was !== undefined && state.labels[key].was !== fallback);
// the label in a page: plain text, or in admin mode with its edit mark (a span, since a label may sit in a button)
export function L(key, fallback) {
  const text = Lt(key, fallback);
  if (!state.admin) return text;
  const cls = key in state.labels ? (stale(key, fallback) ? ' changed stale' : ' changed') : '';
  const note = stale(key, fallback) ? T(`واژهٔ خود صفحه از «${state.labels[key].was}» به «${fallback}» تغییر کرده است`, `The page's own word changed from “${state.labels[key].was}” to “${fallback}”`) : '';
  return h`<span class="w-label-edit${cls}" data-label-key="${key}" data-label-default="${fallback}"${note ? h` title="${note}"` : ''}>${text}<span role="button" tabindex="0" class="w-label-pen" data-action="edit-label" data-key="${key}" aria-label="${T('ویرایش برچسب', 'Edit the label')}">✎</span></span>`;
}
// the person's labels, each with the page's own word now (where a page has offered it) and whether to look again:
// [{key, text, was, now, state: 'ok' | 'stale' | 'gone' | 'unseen'}]
export function mine(isPageKey = () => false) {
  return Object.entries(state.labels).sort(([a], [b]) => a.localeCompare(b)).map(([key, l]) => {
    const now = known.get(key);
    const st = now !== undefined ? (l.was !== undefined && l.was !== now ? 'stale' : 'ok') : isPageKey(key) ? 'gone' : 'unseen';
    return {key, text: l.text, was: l.was, now, state: st};
  });
}
