// Every payment of a board's garden, the latest first.
import { h } from '/toolbox/safe.js';
import { allPays, payTable } from './board.js';

export default {
  id: 'pays', nav: 'پرداخت‌ها', title: 'پرداخت‌ها',
  render: ctx => h`<section class="panel"><div class="panel-head"><div><h2>همهٔ پرداخت‌ها</h2><p>پرداخت‌هایی که از دفتر دیگری آمده‌اند همان‌جا اصلاح می‌شوند.</p></div></div>${payTable(ctx.data, allPays(ctx.data))}</section>`,
};
