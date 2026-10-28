// THE FRONT PAGE OF A GARDEN OF THE CORE ALONE (daftard's `kind: core`), which carries no handplace of its own: its
// pages are to be its page beans, drawn by the view of the release it runs (`handplace: "view"`, V6). Until its gardener
// moves it there, the front page says what the garden offers on this machine, as its worker reads it — Odoo's own
// screens over the views it captured, and its register's records read live where it names one — and opens them. It
// draws no fact of the garden's.
import { h } from '/toolbox/safe.js';
import * as text from '/toolbox/text.js';

const door = (g, series) => `/odoo?g=${encodeURIComponent(g)}&series=${encodeURIComponent(series)}`;
const series = s => h`<code dir="ltr">${s}</code>`;

export default {
  id: 'core', nav: 'آنچه این دفتر دارد', title: 'آنچه این دفتر اینجا دارد',
  render(ctx) {
    const d = ctx.data, g = d.garden?.name || '', reg = d.register || null;
    const opened = (o, what) => o.opens
      ? h`<a class="primary" href="${door(g, o.series)}">باز کردن</a>`
      : h`<small>کارخواه اودوی این سری روی این رایانه گرفته نشده است (importers/odoo/client.py)؛ ${what} باز نمی‌شود.</small>`;
    const rows = [];
    if (reg) {
      rows.push(h`<div class="row core-screen" data-series="${reg.series}" data-register="1"><div><b>پرونده‌های ${text.show(reg.title || reg.bean)}</b>
        <small>در صفحه‌های اودوی سری ${series(reg.series)}، زنده از خود آن خوانده می‌شوند؛ چیزی از آن‌ها در دفتر یا این رایانه نگه داشته نمی‌شود.</small></div>
        <div>${reg.captured ? opened(reg, 'آن') : h`<small>نماهای اودوی این سری هنوز در دفتر گرفته نشده است (importers/odoo/views.py).</small>`}</div></div>`);
    }
    for (const o of d.odoo || []) {
      if (reg && o.series === reg.series) continue;
      rows.push(h`<div class="row core-screen" data-series="${o.series}"><div><b>صفحه‌های اودوی سری ${series(o.series)}</b>
        <small>پرونده‌های خود دفتر، با نماهایی که دفتر از اودو گرفته است.</small></div><div>${opened(o, 'این صفحه‌ها')}</div></div>`);
    }
    return h`<section class="panel core-front"><div class="panel-head"><div><h2>صفحه‌های این دفتر</h2>
      <p>این دفتر جز هستهٔ دفتر چیزی ندارد و صفحهٔ نخست خودش هنوز اینجا نیست؛ آنچه از آن روی این رایانه باز می‌شود این‌هاست.</p></div></div>
      ${rows.length ? rows : h`<div class="empty">این دفتر هنوز صفحه‌ای ندارد که اینجا باز شود.</div>`}</section>`;
  },
};
