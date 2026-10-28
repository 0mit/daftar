// The financial reports, each for the period and currency chosen:
// - the trial balance;
// - an account's ledger with its running balance (for one person too);
// - the persons' accounts;
// - the analytic report by centre and month;
// - the card's reconciliation with the bank;
// - the checks: what still has to be made clear.
// Every figure is shown exactly as the books send it, and every sum taken here is exact.
import { h } from '/toolbox/safe.js';
import * as text from '/toolbox/text.js';
import * as exact from '/toolbox/exact.js';
import * as money from '/toolbox/money.js';
import * as choice from '/toolbox/choice.js';
import { me } from '/toolbox/settings.js';
import { badge, fact, count } from '../common.js';
import { state, load, accountLabel, centreLabel, person, beanTitle, amount, bare, day, owes, periodBar } from '../books.js';

const NAMES = {trial: 'تراز آزمایشی', ledger: 'دفتر حساب', people: 'حساب اشخاص', analytic: 'گزارش تحلیلی', card: 'تطبیق کارت', checks: 'بررسی‌ها'};
const nonzero = v => exact.sign(exact.of(v) || exact.ZERO) !== 0;
const places = unit => money.places(unit) ?? 2;
// a Gregorian month the books group by (2026-10), named in the reader's language: the books keep it, not the page
const gregorianMonth = key => new Intl.DateTimeFormat('fa-IR-u-ca-gregory', {month: 'long', year: 'numeric', timeZone: 'UTC'}).format(new Date(key + '-15T12:00:00Z'));

function trial(B) {
  const t = B.trial, u = B.unit;
  return h`<p>${t.balanced ? badge('دفتر تراز است', 'done') : badge('دفتر تراز نیست', 'late')}${t.undated ? h` ${badge(count(t.undated) + ' سند بی‌تاریخ بیرون از بازه')}` : ''}</p>
    <div class="table-scroll"><table class="w-table"><thead><tr><th>کد</th><th>حساب</th><th class="num">ماندهٔ ابتدا</th><th class="num">بدهکار</th><th class="num">بستانکار</th><th class="num">ماندهٔ پایان</th></tr></thead><tbody>
    ${t.rows.map(r => h`<tr class="level-${r.level}"><td class="code"><bdi dir="ltr">${r.code}</bdi></td><td>${r.level === 'subsidiary' ? h`<button class="text-button" data-action="bk-ledger" data-code="${r.code}">${r.name}</button>` : h`<b>${r.name}</b>`}</td>
      <td class="num">${bare(r.opening, u)}</td><td class="num">${bare(r.dr, u)}</td><td class="num">${bare(r.cr, u)}</td><td class="num">${bare(r.closing, u)}</td></tr>`)}
    <tr class="total"><td></td><td>جمع</td><td class="num">${bare(t.totals.opening, u)}</td><td class="num">${bare(t.totals.dr, u)}</td><td class="num">${bare(t.totals.cr, u)}</td><td class="num">${bare(t.totals.closing, u)}</td></tr></tbody></table></div>
    <p class="muted">مانده مثبت یعنی بدهکار (دارایی و هزینه)، منفی یعنی بستانکار (بدهی، سرمایه، درآمد). مبلغ‌ها به ${u}.</p>`;
}

function ledger(B) {
  const codes = Object.keys(B.ledgers), u = B.unit;
  const code = codes.includes(state.ledger.code) ? state.ledger.code : codes[0];
  if (!code) return h`<div class="empty">هنوز سندی نیست.</div>`;
  const lg = B.ledgers[code], who = state.ledger.person;
  const persons = [...new Set(lg.rows.map(r => r.person).filter(Boolean))];
  let run = who ? exact.ZERO : exact.of(lg.opening) || exact.ZERO;
  const rows = lg.rows.filter(r => !who || r.person === who).map(r => {
    run = exact.sub(exact.add(run, exact.of(r.dr) || exact.ZERO), exact.of(r.cr) || exact.ZERO);
    return {...r, running: exact.text(run, places(u))};
  });
  return h`<div class="filters"><label class="w-field"><span class="w-label">حساب</span>${choice.edit('lg-code', code, codes.map(c => ({value: c, label: accountLabel(c)})), {required: true})}</label>
    ${persons.length ? h`<label class="w-field"><span class="w-label">شخص</span>${choice.edit('lg-person', who, persons.map(p => ({value: p, label: person(p)})), {none: 'همهٔ اشخاص'})}</label>` : ''}</div>
    ${who ? '' : h`<p>ماندهٔ ابتدای بازه: <b>${amount(lg.opening, u)}</b></p>`}
    <div class="table-scroll"><table class="w-table"><thead><tr><th>سند</th><th>تاریخ</th><th>شرح</th><th>تفصیلی</th><th class="num">بدهکار</th><th class="num">بستانکار</th><th class="num">مانده</th></tr></thead><tbody>${rows.map(r =>
      h`<tr><td><button class="text-button" data-action="bk-goto-voucher" data-ref="${r.ref}">${count(r.number)}</button></td><td>${r.date ? day(r.date) : '—'}</td><td>${text.show(r.memo)}</td>
        <td>${r.person ? person(r.person) : ''}${r.contract ? h`<small>${text.show(beanTitle(r.contract))}</small>` : ''}</td>
        <td class="num">${nonzero(r.dr) ? bare(r.dr, u) : ''}</td><td class="num">${nonzero(r.cr) ? bare(r.cr, u) : ''}</td><td class="num">${bare(r.running, u)}</td></tr>`)}</tbody></table></div>`;
}

function people(B) {
  if (!B.people.length) return h`<div class="empty">هنوز حساب شخصی باز نشده است.</div>`;
  return h`<div class="table-scroll"><table class="w-table"><thead><tr><th>شخص</th><th>توافق</th><th class="num">مانده</th><th>یعنی</th></tr></thead><tbody>${B.people.map(p => h`
    ${p.contracts.map(c => h`<tr><td>${p.title}</td><td>${text.show(c.title)}</td><td class="num">${amount(c.balance, p.unit)}</td><td>${owes(c.balance)}</td></tr>`)}
    <tr class="total"><td>${p.title}</td><td>جمع</td><td class="num">${amount(p.balance, p.unit)}</td><td>${owes(p.balance)}</td></tr>`)}</tbody></table></div>
    <p class="muted">از حساب جاری اشخاص (۱۳۰۱)، با هر پرداخت، سهم و سند دستی‌ای که به آن شخص خورده است.</p>`;
}

function analytic(B) {
  const u = state.period.unit, own = B.analytic.own.filter(r => r.unit === u);
  const months = [...new Set(own.map(r => r.month))].sort();
  const groups = {};
  for (const r of own) {
    const a = ((groups[r.analytic] ||= {})[r.account] ||= {name: r.accountName, by: {}});
    a.by[r.month] = exact.add(a.by[r.month] || exact.ZERO, exact.of(r.amount) || exact.ZERO);
  }
  const gross = Object.fromEntries(B.analytic.gross.filter(r => r.unit === u).map(r => [r.analytic, r.amount]));
  const centre = an => an ? centreLabel(an) : 'بدون مرکز هزینه';
  if (!Object.keys(groups).length) return h`<div class="empty">هنوز هزینه‌ای به مرکز هزینه‌ای ثبت نشده است.</div>`;
  return h`<div class="table-scroll"><table class="w-table"><thead><tr><th>مرکز هزینه</th><th>حساب</th>${months.map(m => h`<th class="num">${gregorianMonth(m)}</th>`)}<th class="num">جمع سهم ${me()}</th></tr></thead><tbody>
    ${Object.entries(groups).sort(([a], [b]) => a.localeCompare(b)).map(([an, accounts]) => {
      let groupTotal = exact.ZERO;
      const rows = Object.entries(accounts).map(([code, a]) => {
        const t = months.reduce((n, m) => exact.add(n, a.by[m] || exact.ZERO), exact.ZERO);
        groupTotal = exact.add(groupTotal, t);
        return h`<tr><td>${centre(an)}</td><td><bdi dir="ltr">${code}</bdi> — ${a.name}</td>${months.map(m => h`<td class="num">${a.by[m] ? bare(exact.text(a.by[m], places(u)), u) : ''}</td>`)}<td class="num">${bare(exact.text(t, places(u)), u)}</td></tr>`;
      });
      return h`${rows}<tr class="total"><td>${centre(an)}</td><td>جمع${gross[an] ? h` <small>کل خریدهای این مرکز با سهم دیگران: ${amount(gross[an], u)}</small>` : ''}</td>${months.map(() => h`<td></td>`)}<td class="num">${bare(exact.text(groupTotal, places(u)), u)}</td></tr>`;
    })}</tbody></table></div>
    <p class="muted">سهم خود ${me()} از هزینه‌ها و درآمدها؛ «کل خریدها» تمام مبلغ پرداخت‌های همان مرکز است، هر کس که سهمش را بدهد. مبلغ‌ها به ${u}.</p>`;
}

function card(B) {
  const row = B.trial.rows.find(r => r.code === '2101');
  return h`${B.statements.map(s => {
    const unit = s.lines[0]?.unit || 'TRY', p = places(unit);
    const calc = exact.add(exact.of(s.opening) || exact.ZERO, exact.of(s.net) || exact.ZERO), meets = exact.eq(calc, exact.of(s.closing) || exact.ZERO);
    return h`<div class="report-note"><b>${text.show(s.title)}</b><div class="facts">${fact('بدهی ابتدای دوره (بانک)', amount(s.opening, unit))}${fact('خالص ردیف‌ها', amount(s.net, unit))}
      ${fact('ابتدا + ردیف‌ها', amount(exact.text(calc, p), unit))}${fact('بدهی پایان دوره (بانک)', amount(s.closing, unit))}${fact('ثبت‌شده در دفتر', amount(s.posted, unit))}${fact('ثبت‌نشده', amount(s.unposted, unit))}</div>
      <p>${meets ? badge('ردیف‌های صورتحساب با جمع بانک می‌خواند', 'done') : badge('جمع ردیف‌ها با بانک نمی‌خواند', 'late')} ${s.counts.unposted ? badge(count(s.counts.unposted) + ' ردیف ثبت‌نشده', 'late') : badge('همهٔ ردیف‌ها ثبت شده‌اند', 'done')}</p></div>`;
  })}<p>ماندهٔ حساب ۲۱۰۱ در دفتر: <b>${amount(row ? exact.text(exact.neg(exact.of(row.closing) || exact.ZERO), places(B.unit)) : '0', B.unit)}</b> بدهی. ${row ? '' : 'هنوز سندی به کارت نخورده است.'}</p>`;
}

function checks(B) {
  if (!B.checks.length) return h`<div class="empty">موردی برای بررسی نیست.</div>`;
  return h`<div class="table-scroll"><table class="w-table"><thead><tr><th>سند</th><th>چه باید روشن شود</th></tr></thead><tbody>${B.checks.map(c =>
    h`<tr><td>${c.number ? h`<button class="text-button" data-action="bk-goto-voucher" data-ref="${c.ref}">${count(c.number)}</button>` : h`<bdi dir="ltr">${c.ref}</bdi>`}</td><td>${text.show(c.what)}</td></tr>`)}</tbody></table></div>`;
}

const REPORTS = {trial, ledger, people, analytic, card, checks};
export default {
  id: 'finance', nav: 'گزارش‌های مالی', title: 'گزارش‌های مالی',
  async render(ctx) {
    const B = await load(ctx), r = state.report, p = state.period;
    return h`<section class="panel"><div class="sub-tabs" role="tablist">${Object.entries(NAMES).map(([k, n]) =>
      h`<button role="tab" aria-selected="${k === r}" class="${k === r ? 'primary' : 'secondary'}" data-action="bk-report" data-report="${k}">${n}${k === 'checks' && B.checks.length ? ' ' + count(B.checks.length) : ''}</button>`)}</div>
      ${['trial', 'ledger', 'analytic'].includes(r) ? periodBar() : ''}
      <h2 class="print-heading">${NAMES[r]} — ${p.from ? day(p.from) : 'آغاز'} تا ${p.to ? day(p.to) : 'امروز'} · ${p.unit}</h2>
      ${REPORTS[r](B)}<p><button class="secondary" data-action="bk-print">چاپ / PDF</button></p></section>`;
  },
  actions: {
    'bk-report': (el, ctx) => { state.report = el.dataset.report; return ctx.rerender(); },
    'bk-print': () => window.print(),
  },
  change(e, ctx) {
    if (e.target.name === 'lg-code') { state.ledger = {code: e.target.value, person: ''}; return ctx.rerender(); }
    if (e.target.name === 'lg-person') { state.ledger.person = e.target.value; return ctx.rerender(); }
  },
};
