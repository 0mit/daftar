// A board's agreements: each with its parties and payments; a payment is recorded in one this garden made.
import { h } from '/toolbox/safe.js';
import * as text from '/toolbox/text.js';
import { who, payTable } from './board.js';

export default {
  id: 'agreements', nav: 'توافق‌ها', title: 'توافق‌ها',
  render(ctx) {
    const d = ctx.data;
    if (!d.agreements.length) return h`<section class="panel"><div class="empty">توافقی ثبت نشده است.</div></section>`;
    return h`${d.agreements.map(a => h`<section class="panel"><div class="panel-head"><div><h2>${text.show(a.title)}</h2>
      <p>طرف‌ها: ${a.parties.map(p => who(d, p)).join('، ') || '—'}${a.from ? h` · از ${text.show(a.fromTitle || a.from)} (فقط خواندنی)` : ''}</p></div>
      ${a.writable ? h`<button class="secondary" data-action="board-add" data-a="${a.id}">＋ پرداخت</button>` : ''}</div>
      ${payTable(d, a.pays.map(p => ({...p, agreement: a})))}</section>`)}`;
  },
};
