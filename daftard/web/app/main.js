// The handplace's shell: navigation from the pages' own declarations, the data (read when the garden changed, never
// polled), delegated actions, and every failure shown as a guided error. Pages are web/app/pages/*.js.
import { h, mount, Safe } from '/toolbox/safe.js';
import { configure, settings, me } from '/toolbox/settings.js';
import * as api from '/toolbox/api.js';
import * as moment from '/toolbox/moment.js';
import * as number from '/toolbox/number.js';
import { guidedError, bindGuided } from '/toolbox/guided.js';
import { bindSort } from '/toolbox/table.js';
import { isOpen } from '/toolbox/dialog.js';
import { pageSets, actions } from './pages/index.js';
import { viewPageSet, bindDecisions, readerWidgets } from './view.js';
import { log, timed, expose, debug } from '/toolbox/log.js';
import { configureLabels, adminFromUrl, isAdmin, L, Lt, offer, mine } from '/toolbox/labels.js';
import { table } from '/toolbox/table.js';
import { openDialog } from '/toolbox/dialog.js';
import { form, collect, showErrors } from '/toolbox/form.js';
import { askSitting } from '/toolbox/sitting.js';
import { T, setLang, onLang } from '/toolbox/say.js';

// ?static=1: no change events (a screenshot or a test waits for the page to go quiet, and a live stream never does)
const STATIC = new URLSearchParams(location.search).get('static') === '1';
configureLabels({}, {admin: adminFromUrl()});
// a write the garden takes only from a person sitting at the keyboard asks who sits here, and is made again (design §6)
api.whenSittingAsked(() => askSitting(api));

const $ = id => document.getElementById(id);
// the pages of this garden's kind (read with its data): a dashboard's, or a board's
let pages = pageSets.dashboard;
const offerAll = () => { for (const p of pages) { offer('nav.' + p.id, p.nav); offer('title.' + p.id, p.title); } };
const SYNC = () => ({current: T('همگام با مرکز', 'in step with the hub'), pulled: T('به‌روز شد از مرکز', 'brought up to date from the hub'),
  merged: T('با مرکز ادغام شد', 'merged with the hub'), pushed: T('به مرکز فرستاده شد', 'sent to the hub'),
  busy: T('همگام‌سازی پس از ذخیره', 'in step after the save'), dirty: T('همگام‌سازی پس از ذخیره', 'in step after the save'),
  error: T('مرکز در دسترس نیست؛ دوباره تلاش می‌شود', 'the hub is out of reach; trying again'),
  diverged: T('همگام‌سازی نیاز به بررسی دارد', 'the sync needs a look'), refused: T('همتایی چیزی آورد که پذیرفته نشد', 'a peer brought something refused'),
  waiting: T('همگام‌سازی به‌زودی', 'syncing soon')});
// THE SHELL'S FIXED WORDS (index.html), said again when the language changes
onLang(() => {
  const put = (id, fa, en) => { const e = $(id); if (e) e.textContent = T(fa, en); };
  put('footer-note', 'دفتر خصوصی شما', 'Your private garden');
  put('eyebrow', 'فضایی برای نظم روزانه', 'A space for everyday order');
  put('content-reading', 'در حال خواندن دفتر…', 'Reading the garden…');
  const note = $('aside-note');
  if (note) mount(note, h`${T('کارها، آدم‌ها و حساب‌ها', 'Work, people and accounts')}<br>${T('همه در یک جا', 'all in one place')}`);
  $('nav')?.setAttribute('aria-label', T('بخش‌ها', 'Sections'));
});
let loading = null;
// THE CLOCK (core 1.1): a save stamps only from a clock within half a minute of its time sources. Read once a page
// load; where it cannot stamp, the footer says so beside the sync, in the clock's own words on hover.
let clockNote = '';
api.get('/api/clock').then(c => {
  if (c && c.may === false) clockNote = h` · <span class="w-bad" title="${(c.lines || []).join('\n')}">${T('ساعت این رایانه درست نیست؛ ذخیره پذیرفته نمی‌شود', 'this machine\'s clock is not right; no save is taken')}</span>`;
}).catch(() => {});

export const ctx = {
  data: null, page: null, params: new URLSearchParams(), cache: new Map(), stale: false, version: '',
  // read the dashboard again (and drop what was read beside it); a newer code version reloads the page itself
  reload(quiet = true) {
    if (loading) return loading;
    loading = (async () => {
      try {
        const d = await api.get('/api/dashboard');
        if (this.version && d.version && d.version !== this.version) { location.reload(); return; }
        this.version = d.version; this.data = d; this.stale = false; this.cache.clear();
        configure(d); api.setSession(d); configureLabels(d);
        setLang(d.garden?.lang);              // the garden's language, until a page gives the reader's own (daftar:reader)
        // a garden whose handplace is its page beans (daftard.json `handplace: "view"`) has those pages; another, the
        // pages of its kind (web/app/pages, until its gardener moves it)
        pages = d.garden?.handplace === 'view' ? viewPageSet(d) : pageSets[d.garden?.kind] || pageSets.dashboard;
        offerAll();
        log('data', 'read: ', d.cases?.length, 'cases,', d.agreements?.length, 'agreements; head', String(d.head || '').slice(0, 12));
        await render();
        if (!quiet) this.notice(T('اطلاعات تازه شد.', 'Read again.'));
      } catch (e) {
        this.stale = true;
        if (this.data) this.notice(e);
        else {                // nothing read yet: said where the page said it was reading, never «در حال خواندن» for ever
          mount($('content'), h`<section class="panel">${guidedError(e)}</section>`);
          $('content').setAttribute('aria-busy', 'false');
          mount($('sync'), h`${T('خواندن دفتر ممکن نشد', 'The garden could not be read')}`);
        }
      } finally { loading = null; }
    })();
    return loading;
  },
  books(query = '') {
    const key = 'books?' + query;
    if (!this.cache.has(key)) this.cache.set(key, api.get('/api/books' + (query ? '?' + query : '')).catch(e => { this.cache.delete(key); throw e; }));
    return this.cache.get(key);
  },
  calendar(from, to) {
    const key = `calendar?${from}&${to}`;
    if (!this.cache.has(key)) this.cache.set(key, api.get(`/api/calendar?from=${from}&to=${to}`).catch(e => { this.cache.delete(key); throw e; }));
    return this.cache.get(key);
  },
  // a page of the handplace (#id?params); from a landing address, the handplace's own address again
  open(id, params = {}) {
    const host = holder(id);
    if (host) { params = {...params, part: id}; id = host.id; }
    const q = new URLSearchParams(params).toString(), hash = '#' + id + (q ? '?' + q : '');
    if (location.pathname === '/') { location.hash = hash; return; }
    const g = this.data?.garden?.name;
    history.pushState(null, '', '/' + (g ? '?g=' + encodeURIComponent(g) : '') + hash);
    render();
  },
  // a landing address: /go/<garden>[/<kind>[/<id>]], the address a notification would open
  go(kind = '', id = '') {
    const g = this.data?.garden?.name || api.gardenName() || '';
    history.pushState(null, '', `/go/${encodeURIComponent(g)}${kind ? '/' + kind : ''}${kind && id ? '/' + encodeURIComponent(id) : ''}`);
    render();
  },
  // save one change; the garden is read again after it (the change event would bring it a moment later anyway)
  async save(kind, bean, values, opts = {}) {
    if (this.stale) throw new Error(T('اطلاعات قدیمی است؛ ابتدا «به‌روزرسانی» را بزنید.', 'What is shown is old: press Refresh first.'));
    const r = await api.save(kind, bean, values, {head: this.data.head, ...opts});
    this.notice(T('در دفتر ذخیره شد.', 'Saved in the garden.'));
    await this.reload();
    return r;
  },
  notice(m) {
    const n = $('notice');
    if (!m) { n.className = ''; mount(n, h``); return; }
    if (typeof m === 'string') { n.className = 'notice'; mount(n, h`${m}`); setTimeout(() => n.textContent === m && this.notice(''), 4000); return; }
    n.className = 'notice error'; mount(n, guidedError(m));
  },
  rerender: () => render(),
};

// /go/<garden>/<kind>/<id>: what the landing address names (the server let only these through)
const GO = /^\/go\/[^/]+(?:\/(pending|proposal|error|case|sync|session|action)(?:\/([A-Za-z0-9][A-Za-z0-9._-]*))?)?\/?$/;
function route() {
  const m = !location.hash && GO.exec(location.pathname);
  if (m) {
    ctx.page = pages.find(p => p.id === 'lead');
    ctx.params = new URLSearchParams({kind: m[1] || '', id: m[2] ? decodeURIComponent(m[2]) : ''});
    return;
  }
  const [id, q] = location.hash.slice(1).split('?');
  const host = holder(id);
  ctx.page = host || pages.find(p => p.id === id) || pages[0];
  ctx.part = null;
  ctx.params = new URLSearchParams(q || '');
  if (host) ctx.params.set('part', id);
}

// THE SEVEN PAGES HOLD THE OLD ONES (pages/seven.js): the page whose parts include an id, where that id is not itself in
// the navigation — an old address (#accounts, a button that names #posting) opens the page that holds it, at its part
function holder(id) {
  if (!id || pages.some(p => p.id === id && p.nav)) return null;
  return pages.find(p => p.nav && (p.parts || []).includes(id)) || null;
}

// THE CHROME'S OWN DAYS — today, and when the garden was last read — in the reader's own way of reading where the
// garden's pages are its page beans: drawn by the release's widgets once a page has given them the reader's settings
// (view.js `readerWidgets`), as every day on the page is, and drawn again then; before that, and in a garden of
// daftard's own pages, by the toolbox's, in the garden's calendar
function chromeDays(d) {
  const W = d.garden?.handplace === 'view' ? readerWidgets() : null;
  // the release's widgets build their HTML with the release's own Safe, which this toolbox's h`` does not know and
  // would escape into text: taken here as the Safe HTML it is, and anything else as text
  const theirs = x => W.safe && W.safe.isSafe(x) ? new Safe(x.html) : x;
  const day = (v, o) => W ? theirs(W.moment.show(v, o)) : moment.show(v, o);
  mount($('today'), h`${T(me() + '، خوش آمدی', 'Welcome, ' + me())} · ${day(d.asOf, {style: 'weekday'})}`);
  const s = d.sync || {}, at = !d.generatedAt ? d.asOf : W ? d.generatedAt : d.generatedAt.slice(0, 16).replace('T', ' ');
  mount($('sync'), h`${T('آخرین خواندن', 'Last read')}: ${day(at)}${s.state && s.state !== 'off' ? h` · ${SYNC()[s.state] || s.state}` : ''}${clockNote}`);
}
// the reader's own way of reading, given by a page: the chrome in its language, its days in its calendar
document.addEventListener('daftar:reader', () => {
  const was = document.documentElement.lang;
  setLang(was);
  if (ctx.data) { chromeDays(ctx.data); mount($('header-actions'), headerActions(ctx.page)); }
});
const headerActions = page => h`${isAdmin() ? h`<button class="secondary" data-action="my-labels">${T('برچسب‌های من', 'My labels')}</button>` : ''}<button class="secondary" data-action="refresh">${T('به‌روزرسانی', 'Refresh')}</button>${page && page.headerActions ? page.headerActions(ctx) : ''}`;

async function render() {
  const d = ctx.data;
  if (!d) return;
  route();
  const page = ctx.page;
  document.title = Lt('garden.title', settings.title);
  document.body.classList.toggle('w-admin', isAdmin());
  $('brand').firstChild.textContent = (me() || 'د').slice(0, 1);
  mount($('brand').querySelector('span'), h`${L('garden.title', settings.title)}`);
  mount($('page-title'), h`${L('title.' + page.id, page.title)}`);
  chromeDays(d);
  mount($('nav'), h`${pages.filter(p => p.nav).map((p, i) => h`<button data-nav="${p.id}"${p === page ? h` class="active" aria-current="page"` : ''}>${L('nav.' + p.id, p.nav)} <span>${number.plain(String(i + 1).padStart(2, '0'), {group: false})}</span></button>`)}`);
  mount($('header-actions'), headerActions(page));
  const content = $('content');
  content.setAttribute('aria-busy', 'true');
  try {
    mount(content, await timed('render ' + page.id, () => page.render(ctx)));
    if (page.mounted) page.mounted(ctx, content);   // a page drawn into what was mounted (a view page's drawings)
  }
  catch (e) { mount(content, h`<section class="panel">${guidedError(e)}</section>`); }
  content.setAttribute('aria-busy', 'false');
  const part = ctx.params.get('part');
  if (part) document.getElementById('part-' + part)?.scrollIntoView({block: 'start'});
}

document.addEventListener('click', async e => {
  const pen = e.target.closest('[data-action="edit-label"]'); // an edit mark may sit inside a menu's button
  if (pen) { e.preventDefault(); e.stopPropagation(); actions['edit-label'](pen, ctx); return; }
  const nav = e.target.closest('[data-nav]');
  if (nav) { ctx.open(nav.dataset.nav); return; }
  const a = e.target.closest('[data-action]');
  if (!a || !a.dataset.action || a.dataset.action.startsWith('guided-')) return;
  const fn = a.dataset.action === 'refresh' ? () => ctx.reload(false) : (ctx.page?.actions || {})[a.dataset.action] || actions[a.dataset.action];
  if (!fn) return;
  e.preventDefault();
  log('action', a.dataset.action, {...a.dataset});
  try { await fn(a, ctx, e); } catch (x) { ctx.notice(x); }
});
// a span that acts as a button (an edit mark) answers the keyboard as a button does
document.addEventListener('keydown', e => {
  if ((e.key === 'Enter' || e.key === ' ') && e.target.matches?.('[role="button"][data-action]')) { e.preventDefault(); e.target.click(); }
});
for (const type of ['input', 'change']) {
  document.addEventListener(type, e => {
    if (e.target.closest('dialog')) return;
    const fn = ctx.page?.[type];
    if (fn) try { fn(e, ctx); } catch (x) { ctx.notice(x); }
  });
}
window.addEventListener('hashchange', () => { route(); render(); });
window.addEventListener('popstate', () => render());
// ADMIN MODE (?admin=1): a label's edit mark opens its form. A label is the reader's own customisation of an interface
// word, kept for them alone and carried to their other machines through the hub it syncs with; a garden's names and data are
// not labels and are changed in their beans.
offerAll();
const pageKey = key => /^(nav|title)\./.test(key);
const setLabel = async (c, key, text, was) => { await api.post('/api/labels', {key, text: text === was ? '' : text, was}); await c.reload(); };
actions['edit-label'] = (el, c) => {
  const key = el.dataset.key, holder = el.closest('[data-label-key]'), fallback = holder?.dataset.labelDefault || '';
  const fields = [{name: 'text', label: T('برچسب', 'Label'), max: 200}];
  openDialog({title: T('ویرایش برچسب', 'Edit a label'), note: T(`کلید «${key}» · واژهٔ خود صفحه: ${fallback}. خالی بگذارید تا همان برگردد. این تغییر فقط برای خود شماست و نام‌ها و داده‌های دفتر را تغییر نمی‌دهد.`,
    `Key “${key}” · the page's own word: ${fallback}. Leave it empty to have that back. The change is yours alone and changes none of the garden's names or data.`),
    body: form(fields, {text: Lt(key, fallback)}), onSubmit: async f => {
      const {values, errors} = collect(f, fields);
      if (!showErrors(f, errors)) return false;
      await setLabel(c, key, values.text || '', fallback);
      return true;
    }});
};
const STATE = () => ({ok: T('به‌روز', 'up to date'), stale: T('واژهٔ صفحه تغییر کرده؛ دوباره ببینید', 'the page\'s word changed; look again'),
  gone: T('دیگر در هیچ صفحه‌ای نیست', 'on no page any more'), unseen: T('در این نشست دیده نشده', 'not seen this sitting')});
actions['my-labels'] = () => {
  const rows = mine(pageKey);
  openDialog({title: T('برچسب‌های من', 'My labels'), wide: true, note: T('واژه‌هایی که برای خودتان تغییر داده‌اید؛ روی همهٔ رایانه‌هایی که این دفتر را می‌خوانید یکی است.',
    'The words you changed for yourself; the same on every machine you read this garden on.'),
    body: table({columns: [
      {title: T('کلید', 'Key'), cell: r => h`<code dir="ltr">${r.key}</code>`},
      {title: T('برچسب شما', 'Your label'), cell: r => r.text},
      {title: T('واژهٔ صفحه', 'The page\'s word'), cell: r => r.now ?? r.was ?? ''},
      {title: T('وضعیت', 'State'), cell: r => STATE()[r.state]},
      {title: '', cell: r => h`<button type="button" class="secondary" data-action="reset-label" data-key="${r.key}" data-was="${r.now ?? r.was ?? ''}">${T('برگرداندن', 'Set back')}</button>`},
    ], rows, empty: T('هنوز برچسبی تغییر نداده‌اید.', 'You have changed no label yet.'), rowClass: r => r.state === 'stale' || r.state === 'gone' ? 'attention' : ''})});
};
actions['reset-label'] = async (el, c) => {
  await setLabel(c, el.dataset.key, '', el.dataset.was);
  el.closest('tr')?.remove();
};
bindGuided(document);
bindSort(document);
bindDecisions(ctx);
if (!STATIC) api.events(() => ctx.reload(), () => isOpen());
expose('ctx', ctx);
log('start', {debug, admin: isAdmin(), static: STATIC});
ctx.reload();
