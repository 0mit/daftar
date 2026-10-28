// The vouchers: every payment is one, and so is every manual voucher of the gardener's. A wrong one is corrected or
// deleted (the earlier saying taken out and the right one written; the history keeps both); a reversing voucher is
// only for a real reversal, like money given back. Each opens to its lines, its actions and its history.
import { h, mount } from '/toolbox/safe.js';
import * as text from '/toolbox/text.js';
import * as exact from '/toolbox/exact.js';
import * as choice from '/toolbox/choice.js';
import { me } from '/toolbox/settings.js';
import { badge, count } from '../common.js';
import { state, load, books, VOUCHER_KINDS, person, beanTitle, centreLabel, accountRows, amount, bare, day, periodBar, history, historyView } from '../books.js';

const nonzero = v => exact.sign(exact.of(v) || exact.ZERO) !== 0;
function rows(B) {
  const f = state.vouchers, p = state.period, q = f.search.toLocaleLowerCase();
  return B.vouchers.filter(v => (!f.kind || v.kind === f.kind) && (!f.account || v.lines.some(l => l.account === f.account))
    && (!p.from || (v.date && v.date >= p.from)) && (!p.to || (v.date && v.date <= p.to))
    && (!q || [v.memo, v.ref, String(v.number)].some(x => String(x || '').toLocaleLowerCase().includes(q)))).slice().reverse();
}
function card(B, v) {
  const open = state.open.has(v.ref);
  const reversedBy = v.reversedBy && B.vouchers.find(x => x.ref === v.reversedBy);
  const reverses = v.reverses && B.vouchers.find(x => x.ref === v.reverses);
  return h`<div class="voucher${v.reversedBy ? ' reversed' : ''}" id="voucher-${v.ref}"><button class="voucher-head" data-action="bk-toggle" data-ref="${v.ref}" aria-expanded="${open}">
    <b>سند ${count(v.number)}</b><span>${v.date ? day(v.date) : 'بدون تاریخ'}</span><span>${text.show(v.memo || '—')}</span>
    <span>${badge(VOUCHER_KINDS[v.kind] || v.kind, v.kind === 'reversal' ? 'late' : '')}${reversedBy ? badge('برگشت‌خورده با سند ' + count(reversedBy.number), 'late') : ''}${reverses ? badge('برگشتِ سند ' + count(reverses.number)) : ''}${v.warnings.length ? badge('⚠ ' + count(v.warnings.length)) : ''}</span>
    <span class="num">${amount(v.total, v.unit)}</span></button>
    ${open ? h`<div class="voucher-body"><small>${text.show(v.beanTitle)} · <bdi dir="ltr">${v.ref}</bdi></small>${v.warnings.length ? h`<p class="warn">${v.warnings.map((w, i) => h`${i ? h`<br>` : ''}${w}`)}</p>` : ''}
      <div class="table-scroll"><table class="w-table"><thead><tr><th>حساب</th><th>تفصیلی</th><th>مرکز هزینه</th><th class="num">بدهکار</th><th class="num">بستانکار</th></tr></thead><tbody>${v.lines.map(l =>
        h`<tr><td><bdi dir="ltr">${l.account}</bdi> — ${l.accountName}${l.memo ? h`<small>${text.show(l.memo)}</small>` : ''}</td><td>${l.person ? person(l.person) : ''}${l.contract ? h`<small>${text.show(beanTitle(l.contract))}</small>` : ''}</td>
          <td>${l.analytic.map(centreLabel).join('، ')}</td><td class="num">${nonzero(l.dr) ? bare(l.dr, v.unit) : ''}</td><td class="num">${nonzero(l.cr) ? bare(l.cr, v.unit) : ''}</td></tr>`)}</tbody></table></div>
      <div class="voucher-actions"><button class="secondary" data-action="bk-correct" data-ref="${v.ref}">اصلاح</button><button class="secondary" data-action="bk-delete" data-ref="${v.ref}">حذف</button>
        ${v.kind !== 'journal' ? h`<button class="text-button" data-action="bk-dispute" data-ref="${v.ref}">اعتراض</button>` : ''}<button class="text-button" data-action="bk-history" data-ref="${v.ref}">تاریخچه</button>
        ${!v.reverses && !v.reversedBy ? h`<button class="text-button" data-action="bk-reverse" data-ref="${v.ref}">سند معکوس (رویداد واقعی)</button>` : ''}</div>
      ${state.histories[v.ref]?.shown ? historyView(v.ref) : ''}</div>` : ''}</div>`;
}
const list = B => { const rs = rows(B); return rs.length ? h`${rs.map(v => card(B, v))}` : h`<div class="empty">سندی با این فیلتر نیست.</div>`; };
const redraw = () => { const B = books(), el = document.getElementById('voucher-list'); if (B && el) mount(el, list(B)); };

export default {
  id: 'vouchers', nav: 'اسناد حسابداری', title: 'اسناد حسابداری',
  async render(ctx) {
    const B = await load(ctx), f = state.vouchers;
    if (state.focus) {                    // sent here from a ledger, a check or a payment: shown, and scrolled to
      const ref = state.focus; state.focus = '';
      setTimeout(() => document.getElementById('voucher-' + ref)?.scrollIntoView({block: 'center'}));
    }
    return h`<section class="panel"><div class="panel-head"><div><h2>اسناد حسابداری</h2><p>هر پرداخت یک سند است و هر سند دستی ${me()} هم. سند اشتباه را «اصلاح» یا «حذف» کن (روش دفتر: گفتهٔ قبلی برداشته و گفتهٔ درست نوشته می‌شود؛ تاریخچه همه را نگه می‌دارد). «سند معکوس» فقط برای برگشت واقعی است، مثل پس‌دادن پول.</p></div>
      <button class="primary" data-action="bk-journal">＋ سند دستی</button></div>${periodBar()}
      <div class="filters"><input type="search" data-vf="search" placeholder="جستجوی شرح یا شمارهٔ سند…" aria-label="جستجو" value="${f.search}">
        <label class="w-field"><span class="w-label">نوع سند</span>${choice.edit('vf-kind', f.kind, VOUCHER_KINDS, {none: 'همهٔ اسناد'})}</label>
        <label class="w-field"><span class="w-label">حساب</span>${choice.edit('vf-account', f.account, accountRows({postableOnly: false}), {none: 'همهٔ حساب‌ها'})}</label></div>
      <div id="voucher-list">${list(B)}</div></section>`;
  },
  actions: {
    'bk-toggle': (el) => { const r = el.dataset.ref; state.open.has(r) ? state.open.delete(r) : state.open.add(r); redraw(); },
    'bk-history': async (el) => { const hs = await history(el.dataset.ref); hs.shown = !hs.shown; redraw(); },
  },
  input(e) { if (e.target.dataset.vf === 'search') { state.vouchers.search = e.target.value; redraw(); } },
  change(e) {
    const n = e.target.name;
    if (n === 'vf-kind' || n === 'vf-account') { state.vouchers[n.slice(3)] = e.target.value; redraw(); }
  },
};
