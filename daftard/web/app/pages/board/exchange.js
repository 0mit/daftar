// A board's exchange with other gardens: the standing consents, the last round, what waits and what was set aside
// (each opens its landing page to be decided).
import { h } from '/toolbox/safe.js';
import * as moment from '/toolbox/moment.js';
import * as text from '/toolbox/text.js';
import { fact } from '../../common.js';

export default {
  id: 'exchange', nav: 'تبادل با دفترها', title: 'تبادل با دفترها',
  render(ctx) {
    const x = ctx.data.exchange || {};
    if (!x.configured) return h`<section class="panel"><div class="empty">تبادل با دفترهای دیگر روی این دستگاه تنظیم نشده است.</div></section>`;
    if (x.error) return h`<section class="panel"><p class="notice error">${text.show(x.error)}</p></section>`;
    const last = x.last;
    return h`<section class="panel"><div class="panel-head"><div><h2>تبادل خودکار</h2><p>پرداخت‌های توافق‌هایی که با رضایت هر دو طرف مبادله می‌شوند، هر ده دقیقه و کمی پس از هر ثبت فرستاده و گرفته می‌شوند.</p></div>
      <button class="secondary" data-action="board-exchange-now">همین حالا</button></div>
      <div class="facts">${fact('رضایت‌ها', (x.consents || []).map(c => c.agreement + ' ↔ ' + c.with).join('\n') || 'هنوز رضایتی ثبت نشده')}
      ${fact('آخرین دور', last ? h`${moment.show(String(last.at).slice(0, 16).replace('T', ' '))}<br>گرفته: ${(last.taken || []).map(t => t.beans.join('، ')).join(' · ') || '—'}<br>فرستاده: ${(last.sent || []).map(s => s.bean).join(' · ') || '—'}` : 'هنوز اجرا نشده')}
      ${(last?.waiting || []).length ? fact('در انتظار', last.waiting.join('\n')) : ''}</div></section>
      ${(x.held || []).length ? h`<section class="panel"><h2>کنار گذاشته شده</h2>${x.held.map(p => h`<div class="report-note"><b dir="ltr">${p.file}</b>
        <button class="text-button" data-action="go-lead" data-kind="proposal" data-id="${p.file.replace(/\.md$/, '')}">بررسی و تصمیم</button><pre dir="ltr">${p.why}</pre></div>`)}</section>` : ''}`;
  },
};
