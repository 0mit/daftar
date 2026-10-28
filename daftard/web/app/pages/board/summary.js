// A board's first page: what each person owes the gardener or is owed, per currency, and the latest payments.
import { h } from '/toolbox/safe.js';
import * as money from '/toolbox/money.js';
import * as text from '/toolbox/text.js';
import { allPays, payTable, owesText } from './board.js';

export default {
  id: 'home', nav: 'خلاصه', title: 'خلاصه',
  render(ctx) {
    const d = ctx.data;
    const cards = d.balances.map(b => h`<div class="stat"><span>${text.show(b.title)}</span><b class="amount">${money.show(String(b.amount).replace(/^-/, ''), b.unit)}</b><small>${owesText(b)}${money.uneven(String(b.amount).replace(/^-/, ''), b.unit) ? h` — ${money.UNEVEN}` : ''}</small></div>`);
    return h`<div class="stats">${cards.length ? cards : h`<div class="stat"><span>حساب با دیگران</span><b>۰</b><small>همه چیز تسویه است</small></div>`}</div>
      <section class="panel"><div class="panel-head"><div><h2>آخرین پرداخت‌ها</h2><p>از همهٔ توافق‌ها، و آنچه از دفترهای دیگر رسیده است.</p></div>
      <button class="text-button" data-nav="pays">همهٔ پرداخت‌ها ←</button></div>${payTable(d, allPays(d).slice(0, 12))}</section>`;
  },
};
