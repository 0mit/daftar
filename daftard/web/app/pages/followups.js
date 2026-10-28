// The follow-ups that are still open, by when they are due: late, today, the days ahead, and with no due day.
import { h } from '/toolbox/safe.js';
import { badge, count, openFollowups, bucket, sortDue, taskRow, BUCKETS } from '../common.js';
export default {
  id: 'followups', nav: 'پیگیری‌ها', title: 'قدم بعدی، روشن و مشخص',
  render(ctx) {
    const d = ctx.data, all = openFollowups(d);
    return h`${Object.entries(BUCKETS).map(([g, title]) => {
      const rows = sortDue(all.filter(f => bucket(f, d.asOf) === g));
      return h`<section class="panel"><div class="panel-head"><h2>${title} ${badge(count(rows.length), g === 'late' ? 'late' : '')}</h2></div>${rows.length ? rows.map(f => taskRow(f, d.asOf)) : h`<p class="muted">موردی ندارد.</p>`}</section>`;
    })}`;
  },
};
