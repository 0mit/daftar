// Today: the counts, the follow-ups due, the balances at a glance, and the cases.
import { h } from '/toolbox/safe.js';
import * as money from '/toolbox/money.js';
import { me } from '/toolbox/settings.js';
import { badge, count, openFollowups, bucket, sortDue, taskRow, clientTable } from '../common.js';
export default {
  id: 'home', nav: 'نمای امروز', title: 'روزت را از اینجا شروع کن',
  headerActions: () => h`<button class="primary" data-action="new-case">＋ پروندهٔ جدید</button>`,
  render(ctx) {
    const d = ctx.data, all = openFollowups(d), due = sortDue(all.filter(f => ['late', 'today'].includes(bucket(f, d.asOf))));
    const active = d.cases.filter(c => c.status !== 'عدم تبدیل').length;
    const stats = [['پرونده‌های فعال', active, 'از ' + count(d.cases.length) + ' پروندهٔ ثبت‌شده'], ['پیگیری‌های باز', all.length, count(all.filter(f => !f.due).length) + ' مورد بدون موعد'],
      ['نیازمند پیگیری امروز', due.length, 'امروز و موعدهای گذشته'], ['توافق‌های مالی', d.agreements.filter(a => !a.ledger).length, 'مانده‌ها به تفکیک ارز']];
    const totals = Object.entries(d.accounting.totals);
    return h`<div class="stats">${stats.map(([l, n, sub]) => h`<div class="stat"><span>${l}</span><b>${count(n)}</b><small>${sub}</small></div>`)}</div>
      <div class="grid"><section class="panel"><div class="panel-head"><div><h2>اولویت‌های امروز</h2><p>هر پیگیری را با نتیجهٔ آن ببند.</p></div><button class="text-button" data-nav="followups">همهٔ پیگیری‌ها ←</button></div>
        ${due.length ? due.map(f => taskRow(f, d.asOf)) : h`<div class="empty">پیگیری سررسیدشده‌ای ثبت نشده است.<br><small>پیگیری‌های بدون موعد را هم مرور کن.</small></div>`}</section>
      <section class="panel"><div class="panel-head"><div><h2>نگاه به حساب‌ها</h2><p>ماندهٔ ثبت‌شدهٔ همهٔ دوره‌ها</p></div></div>
        ${totals.length ? totals.map(([u, n]) => h`<div class="row"><div><span class="amount">${money.show(n, u)}</span><small>${money.negative(n) ? 'خالص بدهی ' : 'خالص طلب '}${me()}</small>${money.uneven(n, u) ? h`<small>${money.UNEVEN}</small>` : ''}</div>${badge('ثبت‌شده')}</div>`) : h`<p class="muted">مانده‌ای ثبت نشده است.</p>`}
        <p class="muted">پیشنهاد شهریه و تعهد ماهانه، پرداخت محسوب نمی‌شوند.</p><button class="secondary" data-nav="accounts">بررسی حساب‌ها</button></section></div>
      <section class="panel"><div class="panel-head"><div><h2>پرونده‌ها در یک نگاه</h2><p>وضعیت فعلی و قدم بعدی هر کلاینت</p></div><button class="text-button" data-nav="clients">همهٔ پرونده‌ها ←</button></div>${clientTable(d.cases, d.asOf)}</section>`;
  },
};
