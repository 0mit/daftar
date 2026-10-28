// The exchange with the other gardens (exchange/exchange.py): for each agreement with someone who keeps a garden of
// their own, the gardener's standing consent to send and take its payments without a further word, the shared ledger
// they are written in, what the last round sent and took, and what was set aside for a person to decide (each opens
// on its landing page, where it is read and decided).
import { h } from '/toolbox/safe.js';
import * as moment from '/toolbox/moment.js';
import * as text from '/toolbox/text.js';
import * as number from '/toolbox/number.js';
import * as api from '/toolbox/api.js';
import { openDialog } from '/toolbox/dialog.js';
import { table } from '/toolbox/table.js';
import { badge, fact } from '../common.js';

const when = s => s ? moment.show(String(s).slice(0, 16).replace('T', ' ')) : '';

function openConsent(ctx, agreement, peer, on) {
  const r = (ctx.data.exchange?.rows || []).find(x => x.agreement === agreement && x.peer === peer);
  if (!r) return;
  const head = ctx.data.head, request = api.newRequest(), turnOn = on === '1';
  openDialog({title: turnOn ? 'روشن کردن تبادل خودکار' : 'خاموش کردن تبادل خودکار',
    body: h`<div class="wide facts">${fact('توافق', r.title)}${fact('با دفترِ', r.ownerTitle)}</div>
      <p class="wide report-note">${turnOn
        ? h`با ذخیره، رضایت همیشگی تو در همین توافق ثبت می‌شود: پرداخت‌های آن بی‌پرسش دوباره با دفتر ${r.ownerTitle} مبادله می‌شوند. ${r.ledger ? '' : 'یک «دفتر مشترک» هم کنار این توافق ساخته می‌شود؛ پرداخت‌های خانه را از این به بعد در آن ثبت کن تا برای او فرستاده شوند. '}تا ${r.ownerTitle} هم رضایت ندهد، چیزی گرفته یا فرستاده نمی‌شود.`
        : 'با ذخیره، رضایت همیشگی برداشته می‌شود و دیگر چیزی فرستاده یا گرفته نمی‌شود؛ آنچه تا امروز مبادله شده می‌ماند.'}</p>
      <p class="wide muted">ذخیره از دروازهٔ دفتر می‌گذرد؛ اگر همین پرونده در همین دقیقه ذخیره شده باشد، تا یک دقیقه طول می‌کشد.</p>`,
    onSubmit: async () => { await ctx.save('exchange-consent', agreement, {agreement, peer, on}, {head, request}); return true; }});
}

export const actions = {
  'exchange-consent': (el, ctx) => openConsent(ctx, el.dataset.agreement, el.dataset.peer, el.dataset.on),
  'exchange-now': async (el, ctx) => {
    el.disabled = true;
    try { await api.post('/api/sync'); ctx.notice('تبادل و همگام‌سازی آغاز شد؛ چند لحظه بعد صفحه دوباره خوانده می‌شود.'); }
    finally { el.disabled = false; }
  },
  'exchange-held': (el, ctx) => ctx.go('proposal', el.dataset.id),
};

export default {
  id: 'exchange', nav: 'تبادل با دفترها', title: 'تبادل با دفترها', actions,
  render(ctx) {
    const x = ctx.data.exchange || {rows: []}, last = x.last;
    const rows = table({rows: x.rows || [], empty: 'توافقی با کسی که دفتر خودش را دارد پیدا نشد.', columns: [
      {title: 'توافق', cell: r => h`<b>${text.show(r.title)}</b>${r.ledger ? h`<small>دفتر مشترک: ${text.show(r.ledgerTitle || r.ledger)}</small>` : ''}`},
      {title: 'با دفترِ', cell: r => h`${text.show(r.ownerTitle)}<small><bdi dir="ltr">${r.peer}</bdi></small>`},
      {title: 'تبادل خودکار', cell: r => r.on ? badge('روشن', 'done') : badge('خاموش')},
      {title: '', cls: 'actions', cell: r => h`<button class="${r.on ? 'secondary' : 'primary'}" data-action="exchange-consent" data-on="${r.on ? '0' : '1'}" data-agreement="${r.agreement}" data-peer="${r.peer}">${r.on ? 'خاموش کردن' : 'روشن کردن تبادل خودکار'}</button>`},
    ]});
    const lastPart = last ? h`<div class="facts">${fact('آخرین دور', when(last.at))}
      ${fact('گرفته شد', (last.taken || []).map(t => t.beans.join('، ') + ' از ' + t.from).join(' · ') || 'هیچ')}
      ${fact('فرستاده شد', (last.sent || []).map(s => s.bean + ' به ' + s.to).join(' · ') || 'هیچ')}
      ${(last.waiting || []).length ? fact('در انتظار', last.waiting.join('\n')) : ''}</div>` : h`<p class="muted">هنوز دوری اجرا نشده است.</p>`;
    const held = (x.held || []).map(f => h`<div class="report-note"><div class="panel-head"><b><bdi dir="ltr">${f.file}</bdi></b>
      <button class="secondary" data-action="exchange-held" data-id="${String(f.file).replace(/\.md$/, '')}">بررسی و تصمیم</button></div><pre dir="ltr">${f.why}</pre></div>`);
    return h`<section class="panel"><div class="panel-head"><div><h2>تبادل خودکار با دفترهای دیگر</h2><p>توافقی که طرف دیگرش دفتر خودش را دارد با رضایت هر دو نفر خودکار مبادله می‌شود: پرداخت‌هایی که در «دفتر مشترک» آن توافق ثبت می‌کنی به دفتر او فرستاده می‌شوند، و پرداخت‌هایی که او ثبت می‌کند، پس از گذشتن از دروازهٔ دفتر، اینجا گرفته می‌شوند. هر گرفتن و فرستادن در دفتر روزانه ثبت می‌شود و قابل اصلاح یا اعتراض است.</p></div></div>
        ${x.configured ? '' : h`<p class="notice error">پوشهٔ تبادل روی این دستگاه تنظیم نشده است؛ تبادل اجرا نمی‌شود.</p>`}${x.error ? h`<p class="notice error">${x.error}</p>` : ''}${rows}</section>
      <section class="panel"><div class="panel-head"><h2>آخرین دور تبادل</h2><button class="secondary" data-action="exchange-now">همین حالا</button></div>${lastPart}
        ${(x.inbox || []).length ? h`<p class="muted">در صف: ${number.plain(String(x.inbox.length))} پیشنهاد</p>` : ''}</section>
      ${held.length ? h`<section class="panel"><div class="panel-head"><div><h2>کنار گذاشته شده</h2><p>این پیشنهادها از دروازه نگذشتند یا با ثبت‌های اینجا ناسازگارند؛ باید یک نفر تصمیم بگیرد.</p></div></div>${held}</section>` : ''}`;
  },
};
