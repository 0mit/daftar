// THE CHROME'S WORDS IN ITS READER'S LANGUAGE (the operator, 2026-10-14: button labels and the UI not translated to
// English). daftard's own chrome — its shell, its notices, its dialogs and the page of what waits — speaks Persian to a
// reader who reads Persian and English to every other; each word is written once where it is used, as a pair, T(fa, en),
// so a word never loses its translation beside it. The language is the reader's own way of reading where a page gave it
// (the release's prefs), else the garden's; the page takes its direction from it. A page bean's own words are the
// garden's, in the language the garden wrote them in.
const RTL = new Set(['fa', 'ar', 'he', 'ur', 'ps', 'ckb', 'dv', 'yi']);
let current = 'fa';
const said = new Set();
export function setLang(tag) {
  const l = String(tag || '').split(/[-_]/)[0].toLowerCase() || 'fa';
  current = l;
  if (typeof document !== 'undefined') {
    document.documentElement.lang = l;
    document.documentElement.dir = RTL.has(l) ? 'rtl' : 'ltr';
  }
  for (const f of said) f();
}
export const lang = () => current;
export const T = (fa, en) => (current === 'fa' ? fa : en);
// a part of the page that says its words again when the language changes (the shell's fixed words)
export function onLang(f) { said.add(f); f(); }
