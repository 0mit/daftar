// THE SEVEN PAGES (2026-10-11): the handplace by the problems it solves, each solved once. Before, the twelve tabs, the
// board and the reports solved most of them two or three times: today's follow-ups on «نمای امروز», «پیگیری‌ها» and the
// calendar; the balances on «نمای امروز», «توافق‌ها» and the reports; a payment in three forms. Now a page answers one
// question, and is made of the sections that answered it before — each still the one renderer of its part, so nothing is
// drawn twice and nothing is lost:
//   امروز        what needs me now: decisions waiting, follow-ups due, today's sessions and payments, the balances
//   آدم‌ها        each client's case through its life, and the people
//   زمان         classes, events and every due day, on one time line
//   پول          who paid what for whom, and who owes whom; the card's lines, posted and categorised
//   حسابداری     the books: vouchers, reports, the chart of accounts
//   گزارش        the month, reported to the company
//   میان دفترها   what is shared with another garden
// The old pages stay routable by their own addresses, out of the navigation: a link to one opens the page that holds it,
// at its part. Arrows are chosen by meaning (/toolbox/direction.js, the release's view widget): in Persian, `next`
// points left and a flow runs from the start of the line to its end.
import { h } from '/toolbox/safe.js';
import * as money from '/toolbox/money.js';
import * as moment from '/toolbox/moment.js';
import * as text from '/toolbox/text.js';
import * as api from '/toolbox/api.js';
import { me, gardenerId } from '/toolbox/settings.js';
import { badge, count, openFollowups, bucket, sortDue, taskRow } from '../common.js';
import lead, { list as leadList } from './lead.js';
import cases from './cases.js';
import people from './people.js';
import followups from './followups.js';
import report from './report.js';
import accounts, { agreementsOnce } from './accounts.js';
import categorize from './categorize.js';
import exchange from './exchange.js';
import calendar, { dueItems } from './calendar.js';
import posting from './posting.js';
import vouchers from './vouchers.js';
import finance from './finance.js';
import chart from './chart.js';
import boardHome from './board/summary.js';
import boardPays from './board/pays.js';
import boardAgreements from './board/agreements.js';
import boardExchange from './board/exchange.js';

// an arrow by meaning, turned by the page's direction; without the module, the right-to-left page's own
export const glyph = m => (window.daftarDirection ? window.daftarDirection.glyph(m) : ({next: '←', previous: '→', later: '←', earlier: '→'})[m] || '');

// A PAGE MADE OF PARTS: each part an old page's renderer under its own name, its actions and its input handlers kept,
// each handler given only the events of its own part. A part marked `always` (a summary) stands above the others; of
// the rest ONE is shown at a time, chosen by the switch at the top (or by an old page's address, `part`), so a page
// never stacks a card statement's hundred lines under its agreements.
export function compose({id, nav, title, intro, parts}) {
  const inPart = (e, p) => e.target.closest?.('[data-part]')?.dataset.part === p.page.id;
  const visible = ctx => parts.filter(p => !p.when || p.when(ctx));
  const chosen = ctx => {
    const tabs = visible(ctx).filter(p => !p.always), want = ctx.params.get('part');
    return tabs.find(p => p.page.id === want) || tabs[0];
  };
  const shown = ctx => visible(ctx).filter(p => p.always || p === chosen(ctx));
  return {
    id, nav, title, parts: parts.map(p => p.page.id),
    headerActions: ctx => h`${shown(ctx).map(p => p.page.headerActions && !p.noHeader ? p.page.headerActions(ctx) : '')}`,
    actions: Object.assign({'part-tab': (el, c) => c.open(id, {part: el.dataset.tab})}, ...parts.map(p => p.page.actions || {})),
    input: (e, ctx) => { for (const p of shown(ctx)) if (p.page.input && inPart(e, p)) p.page.input(e, ctx); },
    change: (e, ctx) => { for (const p of shown(ctx)) if (p.page.change && inPart(e, p)) p.page.change(e, ctx); },
    async render(ctx) {
      const out = [], tabs = visible(ctx).filter(p => !p.always), cur = chosen(ctx);
      ctx.part = cur?.page.id;                      // the part shown, which a part's own action redraws in place
      if (intro) out.push(h`<p class="page-intro">${intro}</p>`);
      for (const p of visible(ctx).filter(p => p.always)) out.push(await part(ctx, p));
      if (tabs.length > 1) out.push(h`<div class="part-tabs" role="tablist">${tabs.map(p => h`<button type="button" role="tab" data-action="part-tab" data-tab="${p.page.id}" aria-selected="${p === cur ? 'true' : 'false'}"${p === cur ? h` class="active"` : ''}>${p.heading || p.page.nav || p.page.id}</button>`)}</div>`);
      if (cur) out.push(await part(ctx, cur, tabs.length > 1));
      return h`${out}`;
    },
  };
}
async function part(ctx, p, tabbed = false) {
  const body = await (p.render ? p.render(ctx) : p.page.render(ctx));
  return h`<section class="part" id="part-${p.page.id}" data-part="${p.page.id}"${tabbed ? h` role="tabpanel"` : ''}>${p.heading && !tabbed && !p.always ? h`<h2 class="part-h">${p.heading}</h2>` : ''}${body}</section>`;
}

// ---------------------------------------------------------------- امروز: what waits on me now
const todayISO = d => d.asOf;
async function nowRender(ctx) {
  const d = ctx.data, all = openFollowups(d), due = sortDue(all.filter(f => ['late', 'today'].includes(bucket(f, d.asOf))));
  const active = (d.cases || []).filter(c => c.status !== 'عدم تبدیل').length;
  let waiting = null, decisions = h``;
  try { waiting = ((await api.get('/api/leads')).leads || []).length; decisions = await leadList(ctx); }
  catch (e) { decisions = h`<section class="panel"><p class="muted">فهرست تصمیم‌ها خوانده نشد.</p></section>`; }
  const t = todayISO(d);
  let today = [];
  try {
    const cal = await ctx.calendar(t, t);
    today = (cal.series || []).flatMap(s => (s.sessions || []).filter(x => x.day === t).map(x => ({...x, title: s.title, place: s.place})))
      .sort((a, b) => String(a.start).localeCompare(String(b.start)));
  } catch (e) { /* the calendar says it on its own page */ }
  const dueToday = dueItems(d, t, t);
  const stats = [['منتظر تصمیم تو', waiting, 'تنها تو می‌توانی بگیری'], ['پیگیری امروز', due.length, 'امروز و موعدهای گذشته'],
    ['پرونده‌های فعال', active, 'از ' + count((d.cases || []).length) + ' پرونده'], ['پیگیری‌های باز', all.length, count(all.filter(f => !f.due).length) + ' مورد بدون موعد']];
  return h`<div class="stats">${stats.map(([l, n, sub]) => h`<div class="stat"><span>${l}</span><b>${n == null ? '—' : count(n)}</b><small>${sub}</small></div>`)}</div>
    <div class="grid">
      <section class="panel"><div class="panel-head"><div><h2>پیگیری‌های امروز</h2><p>هر پیگیری را با نتیجهٔ آن ببند.</p></div><button class="text-button" data-nav="followups">همهٔ موعدها ${glyph('next')}</button></div>
        ${due.length ? due.map(f => taskRow(f, d.asOf)) : h`<div class="empty">پیگیری سررسیدشده‌ای نیست.</div>`}</section>
      <section class="panel"><div class="panel-head"><div><h2>امروز در تقویم</h2><p>کلاس‌ها، رویدادها و موعدهای پرداخت</p></div><button class="text-button" data-nav="calendar">تقویم ${glyph('next')}</button></div>
        ${today.length || dueToday.length ? h`${today.map(x => h`<div class="row"><div><b>${text.show(x.title)}</b><small>${moment.showTime(x.start)}–${moment.showTime(x.end)}${x.place ? ' · ' + x.place : ''}</small></div>${x.cancelled ? badge('لغو', 'late') : ''}</div>`)}${dueToday.map(x => h`<div class="row"><div><b>${x.label}</b><small>${x.detail}</small></div></div>`)}`
          : h`<p class="muted">امروز چیزی در تقویم نیست.</p>`}</section>
    </div>
    ${decisions}
    ${owesPanel(ctx, {compact: true})}`;
}

// ---------------------------------------------------------------- پول: who owes whom, as flows from the payer to the payee
// A recorded balance of an agreement (positive: owed to the gardener) is a flow between the gardener and the other party:
// drawn from the one who owes to the one owed, the arrowhead the glyph of `next` (a flow runs with the reader's line).
function owesPanel(ctx, {compact = false} = {}) {
  const d = ctx.data, g = gardenerId(), rows = (d.accounting?.rows || []).filter(r => r.kind === 'مانده ثبت‌شده');
  const byBean = Object.fromEntries((d.agreements || []).map(a => [a.id, a]));
  const flows = rows.map(r => {
    const a = byBean[r.bean] || {}, others = Object.entries(a.parties || {}).filter(([id]) => id !== g);
    const other = others.length ? others.map(([, name]) => name).join('، ') : (a.title || r.title);
    const owedToMe = !money.negative(r.amount);
    return {a, r, other, from: owedToMe ? other : me(), to: owedToMe ? me() : other, owedToMe};
  }).filter(f => money.sign(f.r.amount) !== 0);
  const totals = Object.entries(d.accounting?.totals || {});
  return h`<section class="panel owes"><div class="panel-head"><div><h2>چه کسی به چه کسی بدهکار است</h2><p>از آن که بدهکار است به آن که طلبکار است؛ ارزها با هم جمع نمی‌شوند.</p></div>${compact ? h`<button class="text-button" data-nav="accounts">پول ${glyph('next')}</button>` : ''}</div>
    ${flows.length ? h`<ul class="flows">${flows.map(f => h`<li class="flow ${f.owedToMe ? 'in' : 'out'}"><span class="who">${f.from}</span><span class="arrow" aria-hidden="true">${glyph('next')}</span><span class="who">${f.to}</span><span class="amount">${money.show(money.negative(f.r.amount) ? String(f.r.amount).replace(/^-/, '') : f.r.amount, f.r.currency)}</span><small class="on">${f.a.title || f.r.title}</small></li>`)}</ul>` : h`<p class="muted">مانده‌ای ثبت نشده است.</p>`}
    ${totals.length ? h`<div class="net">${totals.map(([u, n]) => h`<span><small>${money.negative(n) ? 'خالص بدهی ' : 'خالص طلب '}${me()}</small> <b class="amount">${money.show(n, u)}</b></span>`)}</div>` : ''}</section>`;
}

const hasBooks = ctx => !!ctx.data?.accounting;
const hasCases = ctx => (ctx.data?.cases || []).length > 0;

export const now = compose({id: 'now', nav: 'امروز', title: 'آنچه اکنون منتظر توست',
  parts: [{page: {id: 'now-today'}, render: nowRender}]});
export const peoplePage = compose({id: 'people-hub', nav: 'آدم‌ها و پرونده‌ها', title: 'هر کلاینت، از نخستین تماس تا ثبت‌نام',
  parts: [{page: cases, heading: 'پرونده‌ها'}, {page: people, heading: 'مخاطبان'}]});
export const time = compose({id: 'time', nav: 'زمان', title: 'کلاس‌ها، رویدادها و هر موعد',
  parts: [{page: calendar, heading: 'تقویم'}, {page: followups, heading: 'موعدهای پیگیری'}]});
export const moneyPage = compose({id: 'money', nav: 'پول', title: 'چه کسی چه پرداخت، و به حساب چه کسی',
  parts: [{page: {id: 'owes'}, always: true, render: ctx => owesPanel(ctx)}, {page: accounts, heading: 'توافق‌ها و پرداخت‌ها'},
    {page: posting, heading: 'خریدهای کارت', when: hasBooks}, {page: categorize, heading: 'دسته‌بندی خریدها', noHeader: true}]});
export const books = compose({id: 'books', nav: 'حسابداری', title: 'اسناد، گزارش‌های مالی و سرفصل حساب‌ها',
  parts: [{page: vouchers, heading: 'اسناد حسابداری'}, {page: finance, heading: 'گزارش‌های مالی'}, {page: chart, heading: 'سرفصل حساب‌ها'}]});
export const reportPage = compose({id: 'company', nav: 'گزارش شرکت', title: 'گزارش ماهانهٔ مشاوره',
  parts: [{page: report, heading: '', when: hasCases}]});
export const between = compose({id: 'between', nav: 'میان دفترها', title: 'آنچه با دفترهای دیگر شریک هستی',
  parts: [{page: exchange, heading: ''}]});

// a garden a board serves: the same problems, fewer of them
export const boardNow = compose({id: 'now', nav: 'امروز', title: 'آنچه اکنون منتظر توست',
  parts: [{page: {id: 'now-decisions'}, render: async ctx => { try { return await leadList(ctx); } catch (e) { return h`<p class="muted">فهرست تصمیم‌ها خوانده نشد.</p>`; } }}]});
export const boardMoney = compose({id: 'money', nav: 'پول', title: 'چه کسی چه پرداخت، و به حساب چه کسی',
  parts: [{page: boardHome, heading: 'خلاصه'}, {page: boardPays, heading: 'همهٔ پرداخت‌ها'}, {page: boardAgreements, heading: 'توافق‌ها'}]});
export const boardBetween = compose({id: 'between', nav: 'میان دفترها', title: 'آنچه با دفترهای دیگر شریک هستی',
  parts: [{page: boardExchange, heading: ''}]});

// the old pages, routable and out of the navigation
export const hidden = (...ps) => ps.map(p => ({...p, nav: undefined}));
export { lead };
