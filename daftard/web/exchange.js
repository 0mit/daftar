'use strict';
// The exchange with the other gardens (exchange/exchange.py): for each agreement with someone who keeps a garden of
// their own, the gardener's standing consent to send and take its payments without a further word, the shared ledger she
// writes them in, what the last round sent and took, and what was set aside for her.
function renderExchange() {
  const x = data.exchange || {rows: []};
  const when = s => s ? new Date(s).toLocaleString('fa-IR', {dateStyle: 'medium', timeStyle: 'short'}) : '';
  const rows = x.rows.map(r => `<tr><td><b>${esc(r.title)}</b>${r.ledger ? `<small>دفتر مشترک: ${esc(r.ledgerTitle || r.ledger)}</small>` : ''}</td><td>${esc(r.ownerTitle)}<small dir="ltr">${esc(r.peer)}</small></td><td>${r.on ? badge('روشن', 'done') : badge('خاموش')}</td><td class="actions"><button class="${r.on ? 'secondary' : 'primary'}" data-exchange="${r.on ? '0' : '1'}" data-agreement="${esc(r.agreement)}" data-peer="${esc(r.peer)}">${r.on ? 'خاموش کردن' : 'روشن کردن تبادل خودکار'}</button></td></tr>`).join('');
  const last = x.last;
  const lastHTML = last ? `<div class="facts">${fact('آخرین دور', when(last.at))}${fact('گرفته شد', (last.taken || []).map(t => t.beans.join('، ') + ' از ' + t.from).join(' · ') || 'هیچ')}${fact('فرستاده شد', (last.sent || []).map(s => s.bean + ' به ' + s.to).join(' · ') || 'هیچ')}${(last.waiting || []).length ? fact('در انتظار', last.waiting.join('\n')) : ''}</div>` : '<p class="muted">هنوز دوری اجرا نشده است.</p>';
  const held = (x.held || []).map(h => `<div class="report-note"><b dir="ltr">${esc(h.file)}</b><pre dir="ltr">${esc(h.why)}</pre></div>`).join('');
  return `<section class="panel"><div class="panel-head"><div><h2>تبادل خودکار با دفترهای دیگر</h2><p>توافقی که طرف دیگرش دفتر خودش را دارد با رضایت هر دو نفر خودکار مبادله می‌شود: پرداخت‌هایی که در «دفتر مشترک» آن توافق ثبت می‌کنی به دفتر او فرستاده می‌شوند، و پرداخت‌هایی که او ثبت می‌کند، پس از گذشتن از دروازهٔ دفتر، اینجا گرفته می‌شوند. هر گرفتن و فرستادن در دفتر روزانه ثبت می‌شود و قابل اصلاح یا اعتراض است.</p></div></div>${x.configured ? '' : '<p class="notice error">پوشهٔ تبادل روی این دستگاه تنظیم نشده است؛ تبادل اجرا نمی‌شود.</p>'}${x.error ? `<p class="notice error">${esc(x.error)}</p>` : ''}${rows ? `<div class="table-scroll"><table><thead><tr><th>توافق</th><th>با دفترِ</th><th>تبادل خودکار</th><th></th></tr></thead><tbody>${rows}</tbody></table></div>` : '<div class="empty">توافقی با کسی که دفتر خودش را دارد پیدا نشد.</div>'}</section>
  <section class="panel"><div class="panel-head"><h2>آخرین دور تبادل</h2><button class="secondary" id="exchange-now">همین حالا</button></div>${lastHTML}${(x.inbox || []).length ? `<p class="muted">در صف: ${fa(x.inbox.length)} پیشنهاد</p>` : ''}</section>
  ${held ? `<section class="panel"><div class="panel-head"><div><h2>کنار گذاشته شده</h2><p>این پیشنهادها از دروازه نگذشتند یا با ثبت‌های اینجا ناسازگارند؛ باید یک نفر تصمیم بگیرد.</p></div></div>${held}</section>` : ''}`;
}
extraTabs.exchange = {title: 'تبادل با دفترها', render: renderExchange};

function openExchange(agreement, peer, on) {
  const r = (data.exchange?.rows || []).find(x => x.agreement === agreement && x.peer === peer); if (!r) return;
  const html = `<input type="hidden" name="agreement" value="${esc(agreement)}"><input type="hidden" name="peer" value="${esc(peer)}"><input type="hidden" name="on" value="${on}">
  <div class="wide facts">${fact('توافق', r.title)}${fact('با دفترِ', r.ownerTitle)}</div>
  <p class="wide report-note">${on === '1'
    ? `با ذخیره، رضایت همیشگی تو در همین توافق ثبت می‌شود: پرداخت‌های آن بی‌پرسش دوباره با دفتر ${esc(r.ownerTitle)} مبادله می‌شوند. ${r.ledger ? '' : 'یک «دفتر مشترک» هم کنار این توافق ساخته می‌شود؛ پرداخت‌های خانه را از این به بعد در آن ثبت کن تا برای او فرستاده شوند. '}تا ${esc(r.ownerTitle)} هم رضایت ندهد، چیزی گرفته یا فرستاده نمی‌شود.`
    : 'با ذخیره، رضایت همیشگی برداشته می‌شود و دیگر چیزی فرستاده یا گرفته نمی‌شود؛ آنچه تا امروز مبادله شده می‌ماند.'}</p>`;
  openBooksForm('exchange-consent', agreement, on === '1' ? 'روشن کردن تبادل خودکار' : 'خاموش کردن تبادل خودکار', html);
}
document.addEventListener('click', async e => {
  const b = e.target.closest('[data-exchange], #exchange-now'); if (!b || !data) return;
  if (b.id === 'exchange-now') {
    b.disabled = true;
    try { await fetch('/api/sync', {method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRF-Token': data.csrf}, body: '{}'}); notice('تبادل و همگام‌سازی آغاز شد؛ چند لحظه بعد صفحه را تازه کنید.'); }
    catch (err) { notice(err.message, true); } finally { b.disabled = false; }
    return;
  }
  openExchange(b.dataset.agreement, b.dataset.peer, b.dataset.exchange);
});
