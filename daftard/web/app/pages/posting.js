// Posting the card: each line of a card statement is a payment from the card, posted to an account, a centre and, if
// shared, an agreement's parties; one line or several at once, or each with the account the books suggest. Below,
// the payments made outside the card (an agreement's, or the gardener's own), each given its account here.
import { h, mount } from '/toolbox/safe.js';
import * as text from '/toolbox/text.js';
import * as number from '/toolbox/number.js';
import { me } from '/toolbox/settings.js';
import { badge, fact, count } from '../common.js';
import { state, load, books, KINDS, accountLabel, centreLabel, person, amount, day, monthOf, monthName, postingSummary,
  openPostCard, openPostPay, openJournal } from '../books.js';

const STATES = [['unposted', 'ثبت‌نشده'], ['posted', 'ثبت‌شده'], ['mismatch', 'ناهمخوان'], ['all', 'همه']];
const key = l => l.statement + '|' + l.line;
const cardLines = B => B.statements.flatMap(s => s.lines.map(l => ({...l, statement: s.id, statementTitle: s.title})));
function scope(B) {
  const f = state.posting, q = f.search.toLocaleLowerCase();
  return cardLines(B).filter(l => (!f.statement || l.statement === f.statement) && (!f.month || (l.day && monthOf(l.day) === f.month))
    && (!f.kind || l.kind === f.kind) && (f.state === 'all' || l.state === f.state)
    && (!q || [l.what, l.category, l.posting?.accounts.map(accountLabel).join(' ')].some(v => String(v || '').toLocaleLowerCase().includes(q))));
}
const chosen = () => [...state.selected].map(k => k.split('|'));

function statementCard(B, s) {
  const unit = s.lines[0]?.unit || 'TRY';
  const opened = B.vouchers.some(v => v.kind === 'journal' && v.lines.some(l => l.account === '2101') && v.memo.includes(s.id) && !v.reversedBy);
  return h`<div class="report-note"><b>${text.show(s.title)}</b><div class="facts">${fact('بدهی ابتدای دوره (بانک)', amount(s.opening, unit))}${fact('بدهی پایان دوره (بانک)', amount(s.closing, unit))}
    ${fact('خالص ردیف‌ها', amount(s.net, unit))}${fact('ثبت‌شده در دفتر', amount(s.posted, unit))}${fact('ثبت‌نشده', amount(s.unposted, unit))}
    ${fact('ردیف‌ها', count(s.counts.posted) + ' ثبت‌شده از ' + count(s.lines.length))}</div>
    ${opened ? '' : h`<button class="secondary" data-action="bk-opening" data-statement="${s.id}">ثبت سند ماندهٔ ابتدای دوره</button> <small class="muted">بدهی ابتدای دورهٔ کارت را به حساب ۲۱۰۱ می‌آورد تا ماندهٔ دفتر با بانک تطبیق شود.</small>`}</div>`;
}

function lineRow(l) {
  const st = l.state === 'posted' ? badge('ثبت‌شده', 'done') : l.state === 'mismatch' ? badge('ناهمخوان', 'late') : badge('ثبت‌نشده');
  const inst = l.installment ? h`<small>قسط ${count(l.installment.number)} از ${count(l.installment.total)} · کل خرید ${amount(l.installment.purchase_total?.count, l.unit)}</small>` : '';
  const sugg = l.state !== 'posted' && l.suggested ? h`<small>پیشنهاد: ${accountLabel(l.suggested)}${l.categoryInferred ? h` ${badge('حدسی')}` : ''}</small>` : '';
  return h`<tr><td><input type="checkbox" data-line="${key(l)}" aria-label="انتخاب ردیف"${state.selected.has(key(l)) ? h` checked` : ''}></td><td>${day(l.day)}</td>
    <td>${text.show(l.what)}<small>${KINDS[l.kind] || l.kind}</small>${inst}</td><td class="num">${amount(l.amount, l.unit)}</td>
    <td>${st}${postingSummary(l.posting)}${sugg}</td>
    <td class="actions"><button class="secondary" data-action="bk-post-one" data-line="${key(l)}">${l.state === 'posted' ? 'تغییر' : 'ثبت'}</button>${l.posting ? h`<button class="text-button" data-action="bk-reverse" data-ref="${l.posting.ref}">برگشت</button>` : ''}</td></tr>`;
}

// the batch bar and the lines: drawn again on a filter or a selection, the filters themselves left as they are
function lines(B) {
  const rows = scope(B), all = rows.length && rows.every(l => state.selected.has(key(l)));
  const canSuggest = chosen().some(([s, k]) => cardLines(B).find(l => l.statement === s && l.line === k && l.suggested && l.state === 'unposted'));
  return h`<div class="batch"><span>${count(state.selected.size)} ردیف انتخاب شده</span><button class="primary" data-action="bk-post-selected"${state.selected.size ? '' : h` disabled`}>ثبت ردیف‌های انتخاب‌شده</button>
    <button class="secondary" data-action="bk-accept-suggested"${canSuggest ? '' : h` disabled`}>ثبت با حساب پیشنهادی هر ردیف</button>${state.selected.size ? h`<button class="text-button" data-action="bk-clear-selection">پاک کردن انتخاب</button>` : ''}</div>
    ${rows.length ? h`<div class="table-scroll"><table class="w-table"><thead><tr><th><input type="checkbox" data-line-all="1" aria-label="انتخاب همه"${all ? h` checked` : ''}></th><th>تاریخ</th><th>شرح</th><th class="num">مبلغ</th><th>ثبت در دفتر</th><th></th></tr></thead>
      <tbody>${rows.map(lineRow)}</tbody></table></div>` : h`<div class="empty">ردیفی با این فیلتر نیست.</div>`}`;
}

function payState(p) {
  if (p.kind === 'reversal') return badge('سند معکوس', 'late');
  if (p.reversedBy) return badge('برگشت‌خورده', 'late');
  return p.accounts.length ? badge('ثبت‌شده', 'done') : badge('بدون حساب', 'late');
}
function pays(B) {
  const all = B.pays.slice().sort((a, b) => (a.date || '9999').localeCompare(b.date || '9999'));
  const open = all.filter(p => p.kind === 'pay' && !p.reversedBy), shown = state.showReversed ? all : open;
  const waiting = open.filter(p => !p.accounts.length);
  const shares = p => Object.keys(p.bears).length ? Object.entries(p.bears).map(([w, s], i) => h`${i ? '، ' : ''}${person(w)} ${number.show(s)}`) : person(p.by) + ' به‌تنهایی';
  return h`<section class="panel"><div class="panel-head"><div><h2>پرداخت‌های بیرون از کارت</h2><p>پرداخت‌های توافق‌ها (مثل حساب خانه) و پرداخت‌هایی که ${me()} خودش ثبت کرده. ${count(waiting.length)} پرداخت هنوز حساب ندارد و در حساب ۱۹۰۲ منتظر است.
    <b>اگر پرداختی اشتباه ثبت شده</b> (توافق، پرداخت‌کننده، سهم‌ها، مبلغ یا تاریخ)، «اصلاح» همان سند را درست می‌کند و تاریخچه نسخهٔ قبلی را نگه می‌دارد؛ اگر اصلاً نباید ثبت می‌شد، در «اسناد حسابداری» «حذف» بزن.</p></div>
    <label class="toggle"><input type="checkbox" data-toggle="reversed"${state.showReversed ? h` checked` : ''}> نمایش برگشت‌خورده‌ها (${count(all.length - open.length)})</label></div>
    ${shown.length ? h`<div class="table-scroll"><table class="w-table"><thead><tr><th>سند</th><th>تاریخ</th><th>توافق</th><th>شرح</th><th>پرداخت‌کننده</th><th>سهم‌ها</th><th class="num">مبلغ</th><th>حساب</th><th></th></tr></thead><tbody>${shown.map(p => {
      const live = p.kind === 'pay' && !p.reversedBy;
      return h`<tr${!live ? h` class="muted"` : ''}><td>${count(p.number)}</td><td>${day(p.date)}</td><td>${text.show(p.beanTitle)}</td>
        <td>${text.show(p.memo)}${p.warnings.length && live ? h`<small>${p.warnings.join('؛ ')}</small>` : ''}</td><td>${person(p.by)}</td><td>${shares(p)}</td>
        <td class="num">${amount(p.amount, p.unit)}</td>
        <td>${payState(p)}${p.accounts.length ? h`<small>${p.accounts.map(accountLabel).join('، ')}${p.analytic.length ? ' · ' + p.analytic.map(centreLabel).join('، ') : ''}</small>` : p.suggested && live ? h`<small>پیشنهاد: ${accountLabel(p.suggested)}</small>` : ''}</td>
        <td class="actions">${live ? h`<button class="secondary" data-action="bk-post-pay" data-ref="${p.ref}">حساب</button><button class="secondary" data-action="bk-correct" data-ref="${p.ref}">اصلاح</button><button class="text-button" data-action="bk-reverse" data-ref="${p.ref}">برگشت</button>`
          : h`<button class="text-button" data-action="bk-goto-voucher" data-ref="${p.ref}">سند</button>`}</td></tr>`;
    })}</tbody></table></div>` : h`<div class="empty">پرداختی بیرون از کارت ثبت نشده است.</div>`}</section>`;
}

const redraw = () => { const B = books(), el = document.getElementById('posting-lines'); if (B && el) mount(el, lines(B)); };

export default {
  id: 'posting', nav: 'ثبت خریدهای کارت', title: 'ثبت خریدهای کارت',
  async render(ctx) {
    const B = await load(ctx), f = state.posting;
    const months = [...new Set(cardLines(B).map(l => l.day && monthOf(l.day)).filter(Boolean))].sort();
    const opt = (v, label, cur) => h`<option value="${v}"${v === cur ? h` selected` : ''}>${label}</option>`;
    return h`<section class="panel"><div class="panel-head"><div><h2>خریدهای کارت را به حساب‌ها ببر</h2><p>هر ردیف صورتحساب یک پرداخت از کارت است: حساب معین، مرکز هزینه و سهم افراد را تعیین کن. تغییر یک ردیف ثبت‌شده همان سند را اصلاح می‌کند؛ نسخهٔ قبلی در تاریخچه می‌ماند.</p></div></div>
      ${B.statements.map(s => statementCard(B, s))}
      <div class="filters"><select data-pf="statement" aria-label="صورتحساب">${opt('', 'همهٔ صورتحساب‌ها', f.statement)}${B.statements.map(s => opt(s.id, s.title, f.statement))}</select>
        <select data-pf="state" aria-label="وضعیت">${STATES.map(([k, n]) => opt(k, n, f.state))}</select>
        <select data-pf="kind" aria-label="نوع ردیف">${opt('', 'همهٔ انواع', f.kind)}${Object.entries(KINDS).map(([k, n]) => opt(k, n, f.kind))}</select>
        <select data-pf="month" aria-label="ماه">${opt('', 'همهٔ ماه‌ها', f.month)}${months.map(m => opt(m, monthName(m), f.month))}</select>
        <input type="search" data-pf="search" placeholder="جستجوی شرح یا حساب…" aria-label="جستجو" value="${f.search}"></div>
      <div id="posting-lines">${lines(B)}</div></section>${pays(B)}`;
  },
  actions: {
    'bk-post-one': (el, ctx) => openPostCard(ctx, [el.dataset.line.split('|')]),
    'bk-post-selected': (el, ctx) => openPostCard(ctx, chosen()),
    'bk-accept-suggested': (el, ctx) => {
      const B = books();
      openPostCard(ctx, chosen().filter(([s, k]) => cardLines(B).find(l => l.statement === s && l.line === k && l.suggested && l.state === 'unposted')), {suggested: true});
    },
    'bk-clear-selection': () => { state.selected.clear(); redraw(); },
    'bk-post-pay': (el, ctx) => openPostPay(ctx, el.dataset.ref),
    // the card's opening debt as a manual voucher, so the books' balance meets the bank's
    'bk-opening': (el, ctx) => {
      const B = books(), s = B.statements.find(x => x.id === el.dataset.statement), unit = s.lines[0]?.unit || 'TRY';
      openJournal(ctx, {prefill: {date: '', memo: 'ماندهٔ بدهی ابتدای دورهٔ ' + s.title + ' (' + s.id + ')', unit,
        lines: [{account: '3101', debit: s.opening}, {account: '2101', credit: s.opening}]}});
    },
  },
  input(e) {
    if (e.target.dataset.pf !== 'search') return;
    state.posting.search = e.target.value;
    redraw();
  },
  change(e, ctx) {
    const t = e.target, B = books();
    if (t.dataset.pf && t.dataset.pf !== 'search') { state.posting[t.dataset.pf] = t.value; redraw(); }
    else if (t.dataset.line) { t.checked ? state.selected.add(t.dataset.line) : state.selected.delete(t.dataset.line); redraw(); }
    else if (t.dataset.lineAll) { for (const l of scope(B)) t.checked ? state.selected.add(key(l)) : state.selected.delete(key(l)); redraw(); }
    else if (t.dataset.toggle === 'reversed') { state.showReversed = t.checked; return ctx.rerender(); }
  },
};
