// THE PAGES OF A GARDEN WHOSE HANDPLACE IS ITS PAGE BEANS (daftard.json `handplace: "view"`). The
// chrome stays daftard's — the garden, its sync, who sits here, the notices and «منتظر شما» (pages/lead.js) — and each
// entry of the navigation is one of the garden's page beans, in the order its handplace gives them. A page is drawn by
// the view's own runtime and renderers, with the view's own widgets, all from the release the garden runs: loaded here as
// the files they are (/release/<garden>/…, its assets/view/lib), the release saying which (`assets`). Its data is the
// view's own reading of the page for the person reading (/api/view/page), and a Save goes to the view's one write path
// (/api/view/write). Nothing of a page is drawn, read or written here.
import { h } from '/toolbox/safe.js';
import * as api from '/toolbox/api.js';
import lead from './pages/lead.js';
import { T } from '/toolbox/say.js';

const loading = new Map();            // per garden, the release's files: loaded once a page
function css(href) {
  if (document.querySelector(`link[data-release="${CSS.escape(href)}"]`)) return;
  const l = document.createElement('link');
  l.rel = 'stylesheet'; l.href = href; l.dataset.release = href;
  document.head.appendChild(l);
}
function script(src) {
  return new Promise((ok, no) => {
    const s = document.createElement('script');
    s.src = src; s.onload = ok; s.onerror = () => no(new Error('the release has no ' + src));
    document.head.appendChild(s);
  });
}
// THE PAGE IN A LANGUAGE: its `lang`, and its direction CLDR's for the language's script, which the renderers read
function readIn(lang) {
  const W = window.daftarWidgets, dir = lang && W && W.locale ? W.locale.dirOf(lang) : '';
  if (dir === 'rtl' || dir === 'ltr') { document.documentElement.lang = lang; document.documentElement.dir = dir; }
}
// the release's widgets as the modules they are, set where its renderers look for them (window.daftarWidgets), then
// its classic scripts in the order they lean on one another, then their styles — each from the garden's own release.
// The page takes the garden's language and its direction, CLDR's for the language's script, as the view's own page
// does (its renderers read the direction of <html>): a Persian garden's pages run right to left, an English one's left
// to right.
function release(garden, assets = {}, lang = '') {
  if (loading.has(garden)) return loading.get(garden);
  const base = `/release/${encodeURIComponent(garden)}/`;
  const p = (async () => {
    for (const s of assets.styles || []) css(base + s);
    const names = assets.widgets || [];
    const mods = await Promise.all(names.map(n => import(base + `widgets/${n}.js`)));
    window.daftarWidgets = Object.fromEntries(names.map((n, i) => [n, mods[i]]));
    readIn(lang);
    for (const s of assets.scripts || []) await script(base + s);
  })();
  loading.set(garden, p);
  return p;
}

const read = new Map();               // the payload each page was drawn from, until the garden changes
async function render(ctx, bean) {
  const g = ctx.data.garden.name;
  await release(g, ctx.data.assets, ctx.data.garden.lang);
  css(`/release/${encodeURIComponent(g)}/kit.css?page=${encodeURIComponent(bean)}`);
  const P = await api.get('/api/view/page?page=' + encodeURIComponent(bean));
  read.set(bean, P);
  const order = P.order || [];
  const part = ctx.params.get('part') || order[0];
  // a page of more than one drawing shows one at a time, chosen by its switch (each drawing's own title)
  return h`<section class="vp" data-page="${bean}">${order.length > 1 ? h`<nav class="vp-parts" aria-label="${P.page.title}">${order.map(k =>
    h`<button type="button" class="secondary${k === part ? ' active' : ''}" data-action="view-part" data-part="${k}">${title(P.views[k])}</button>`)}</nav>` : ''}${
    order.map(k => h`<div class="vp-drawing" data-key="${k}" id="part-${k}"${k === part ? '' : h` hidden`}></div>`)}</section>`;
}
const title = v => new DOMParser().parseFromString(String(v?.title ?? v?.key ?? ''), 'text/html').body.textContent;

// each drawing mounted by the release's runtime, at the lens that draws the drawing itself (its schematic form, where a
// drawing engraved from a reading is its archetype's own drawing)
function mounted(ctx, el, bean) {
  const P = read.get(bean);
  if (!P || !window.viewMount) return;
  // the reader's own way of reading, where they set one (prefs.go): their language and direction for the page
  const st = (P.engraved || {}).settings || {};
  window.daftarWidgets.settings.configure(st);
  readIn((st.reader || {}).locale || ctx.data.garden.lang);
  configured = true;
  document.dispatchEvent(new CustomEvent('daftar:reader'));   // the chrome's own days, drawn again in the reader's way
  const level = ((P.levels || []).find(l => l.form === 'schematic') || {}).id;
  const state = {level, live: true, engraved: P.engraved, values: {}, history: {},
    write: body => api.postRaw('/api/view/write', body),
    act: body => api.postRaw('/api/view/act', Object.assign({page: bean}, body)),   // a page's action, or its plan decided
    onOpen: k => ctx.open(bean, {part: k})};
  // in the kit's light palette (`.vw.light`), the chrome's own page being light
  prefsButton(ctx);
  el.querySelectorAll('.vp-drawing').forEach(box => { window.viewMount(box, {levels: P.levels, ...P.views[box.dataset.key]}, state); box.classList.add('light'); });
}

// THE SHEET'S DIALOG, which the release's renderers open on the page's body (a being opened from any drawing), takes
// the light palette too: watched for once, as the renderers make it
let watching = false;
function lightDialogs() {
  if (watching) return;
  watching = true;
  const mark = n => { if (n.nodeType === 1 && n.matches('dialog.vw')) n.classList.add('light'); };
  document.querySelectorAll('dialog.vw').forEach(mark);
  new MutationObserver(list => list.forEach(m => m.addedNodes.forEach(mark))).observe(document.body, {childList: true});
}

// HOW THE PERSON READS (prefs.go; the release's widgets/prefs.js): reached from the chrome on every page of a garden whose
// pages are its page beans, kept on this machine for the person reading, never in the garden; a Save draws the page
// again in place, in their choice
const LANGS = ['fa', 'en', 'tr', 'ar', 'de', 'fr', 'it'];
async function openPrefs(ctx) {
  await release(ctx.data.garden.name, ctx.data.assets, ctx.data.garden.lang);
  const W = window.daftarWidgets;
  if (!W || !W.prefs) return;
  const j = await api.get('/api/prefs');
  let d = document.getElementById('prefsdlg');
  if (!d) { d = document.createElement('dialog'); d.id = 'prefsdlg'; d.className = 'vw light eg-dialog'; document.body.appendChild(d); }
  W.prefs.open(d, j.prefs || {}, {languages: LANGS, zones: j.zones || []},
    v => api.postRaw('/api/prefs', v).then(r => r.status === 200 ? r.answer : {error: (r.answer || {}).error || (r.answer || {}).message || String(r.status)}),
    saved => { d.close(); if (saved) ctx.reload(); });
  d.showModal();
}
function prefsButton(ctx) {
  const aside = document.querySelector('aside');
  if (!aside || aside.querySelector('[data-action="view-prefs"]')) return;
  const b = document.createElement('button');
  b.type = 'button'; b.className = 'secondary prefs-open'; b.dataset.action = 'view-prefs';
  b.textContent = (window.daftarWidgets && window.daftarWidgets.locale) ? window.daftarWidgets.locale.say('prefs-open') : T('شیوهٔ خواندن', 'How you read');
  b.addEventListener('click', () => openPrefs(ctx));
  const nav = aside.querySelector('#nav');
  (nav ? nav.parentNode : aside).insertBefore(b, nav ? nav.nextSibling : null);
}

export function viewPageSet(d) {
  lightDialogs();
  const pages = (d.pages || []).map(p => ({
    id: p.bean, nav: p.title, title: p.title,
    render: ctx => render(ctx, p.bean),
    mounted: (ctx, el) => mounted(ctx, el, p.bean),
    actions: {'view-part': (a, ctx) => ctx.open(p.bean, {part: a.dataset.part})},
  }));
  return [...pages, {...lead, nav: undefined}];
}

// A DECISION THE QUEUE LISTS is answered where every decision is, on «منتظر شما» (pages/lead.js): its line opens it
// the release's widgets, once a page has given them the reader's settings: what the chrome draws its own days with
let configured = false;
export function readerWidgets() { return configured && window.daftarWidgets && window.daftarWidgets.moment ? window.daftarWidgets : null; }

export function bindDecisions(ctx) {
  document.addEventListener('click', e => {
    const x = e.target.closest('.vp .eg-lead[data-kind="decision"]');
    if (x) { e.preventDefault(); ctx.go('pending', x.dataset.about); }
  });
}
