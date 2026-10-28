'use strict';
// The gardener's books (accounting/book.py, read through /api/books): card lines posted to accounts, the payments of her
// contracts, vouchers and their reversals, her general journal, her chart of accounts, and the reports. Every figure
// arrives already rounded by the server; this page only shows it and sends what the gardener chose.
let books = null, booksLoading = false, booksError = '';
const period = {from: '', to: '', unit: 'TRY'};
const postFilter = {statement: '', state: 'unposted', month: '', kind: '', search: ''};
const voucherFilter = {search: '', kind: '', account: ''};
const selectedLines = new Set();
const openVouchers = new Set();
let reportTab = 'trial', ledgerChoice = {code: '1301', person: ''}, chartScheme = 'account';
const BOOK_KINDS = new Set(['post-card', 'post-pay', 'edit-pay', 'delete-doc', 'dispute-pay', 'edit-entry', 'reverse', 'journal', 'chart-account']);
const histories = {};
const kindNames = {purchase: 'خرید / قسط', refund: 'برگشت وجه', payment: 'واریز به کارت', discount: 'تخفیف بانکی', fee: 'کارمزد و سود'};
const voucherKinds = {pay: 'پرداخت', journal: 'سند دستی', reversal: 'سند معکوس'};
const levelNames = {group: 'گروه', general: 'کل', subsidiary: 'معین', plan: 'طرح', account: 'حساب تحلیلی'};
const typeNames = {asset: 'دارایی', liability: 'بدهی', equity: 'سرمایه', income: 'درآمد', expense: 'هزینه'};

const money = v => v === null || v === undefined || v === '' ? '—' : W.number.show(v);   // the server sends it at its currency's places, or exact
const cents = v => { const [i, f = ''] = String(v || '0').replace('-', '').split('.'); const n = BigInt(i || '0') * 100n + BigInt((f + '00').slice(0, 2)); return String(v).startsWith('-') ? -n : n; };
// EXACT SUMS of the books' amounts as the server sends them (decimal digits, or n/d when an amount does not come out
// even in the currency's places): a fraction of two BigInts, never a float and never cut to cents. `cents` stays for
// what the gardener types and the bank's statement lines, which are always in cents.
const qgcd = (a, b) => { a = a < 0n ? -a : a; b = b < 0n ? -b : b; while (b) [a, b] = [b, a % b]; return a || 1n; };
const qnorm = (n, d) => { const g = qgcd(n, d); return [n / g, d / g]; };
const Q0 = [0n, 1n];
function q(v) {
  const s = String(v ?? '').trim(), f = s.match(/^(-?\d+)\/(\d+)$/), m = s.match(/^(-?)(\d*)(?:\.(\d*))?$/);
  if (f) return qnorm(BigInt(f[1]), BigInt(f[2]));
  if (!m || !(m[2] || m[3])) return Q0;
  const frac = m[3] || '';
  return qnorm(BigInt((m[2] || '0') + frac) * (m[1] ? -1n : 1n), 10n ** BigInt(frac.length));
}
const qadd = (a, b) => qnorm(a[0] * b[1] + b[0] * a[1], a[1] * b[1]);
const qsub = (a, b) => qadd(a, [-b[0], b[1]]);
const qsign = a => (a[0] > 0n) - (a[0] < 0n);
function qtext([n, d], places = 2) {
  const scale = 10n ** BigInt(places);
  if ((n * scale) % d) return `${n}/${d}`;
  const c = n * scale / d, a = (c < 0n ? -c : c).toString().padStart(places + 1, '0');
  return (c < 0n ? '-' : '') + a.slice(0, a.length - places) + (places ? '.' + a.slice(-places) : '');
}
const fromCents = n => { const s = n < 0n ? '-' : ''; const a = n < 0n ? -n : n; return s + (a / 100n) + '.' + String(a % 100n).padStart(2, '0'); };
const account = code => books?.chart.accounts.find(a => a.code === code);
const accountLabel = code => { const a = account(code); return a ? `${code} — ${a.name}` : code || '—'; };
const centre = code => books?.chart.analytic.find(a => a.code === code);
const centreLabel = code => centre(code)?.name || code;
const person = id => books?.persons.find(p => p.id === id)?.title || (id === 'unknown' ? 'نامعلوم' : id);
const beanTitle = id => books?.beans.find(b => b.id === id)?.title || id;

async function loadBooks() {
  booksLoading = true;
  try {
    const q = new URLSearchParams({unit: period.unit}); if (period.from) q.set('from', period.from); if (period.to) q.set('to', period.to);
    const response = await fetch('/api/books?' + q, {cache: 'no-store'});
    const result = await response.json();
    if (!response.ok) throw Error(result.error || 'خواندن دفتر حساب‌ها ممکن نشد.');
    books = result; booksError = '';
  } catch (e) { booksError = e.message; } finally { booksLoading = false; }
  if (extraTabs[tab]) render();
}
function booksReady() {
  if (books && books.head === data.head && !booksError) return true;
  if (!booksLoading && (!books || books.head !== data.head)) loadBooks();
  return false;
}
function waiting() { return `<section class="panel empty">${booksError ? esc(booksError) + ' <button class="secondary" data-bk="reload">دوباره</button>' : 'در حال خواندن دفتر حساب‌ها…'}</section>`; }

function accountOptions(value, {postableOnly = true, empty = 'انتخاب حساب'} = {}) {
  const rows = books.chart.accounts.filter(a => !postableOnly || (a.postable && a.active) || a.code === value);
  return `<option value="">${empty}</option>` + rows.map(a => `<option value="${esc(a.code)}"${a.code === value ? ' selected' : ''}${a.postable ? '' : ' disabled'}>${' '.repeat((a.path.length - 1) * 3)}${esc(a.code)} — ${esc(a.name)}</option>`).join('');
}
function centreOptions(value, empty = 'بدون مرکز هزینه') {
  return `<option value="">${empty}</option>` + books.chart.analytic.filter(a => a.postable && (a.active || a.code === value)).map(a => `<option value="${esc(a.code)}"${a.code === value ? ' selected' : ''}>${esc(a.name)}</option>`).join('');
}
function periodBar(id) {
  return `<div class="filters"><label>از <input type="date" id="${id}-from" value="${esc(period.from)}"></label><label>تا <input type="date" id="${id}-to" value="${esc(period.to)}"></label><select id="${id}-unit" aria-label="ارز">${books.units.map(u => `<option${u === period.unit ? ' selected' : ''}>${esc(u)}</option>`).join('')}</select><button class="secondary" data-bk="period">اعمال بازه</button>${period.from || period.to ? '<button class="text-button" data-bk="period-clear">همهٔ دوره‌ها</button>' : ''}</div>`;
}
function postingSummary(p) {
  if (!p) return '';
  const shares = Object.entries(p.bears || {});
  return `<small>${p.accounts.map(accountLabel).map(esc).join('، ')}${p.analytic.length ? ' · ' + p.analytic.map(centreLabel).map(esc).join('، ') : ''}${shares.length ? ' · سهم: ' + shares.map(([w, s]) => esc(person(w)) + ' ' + fa(s)).join('، ') : ''}${p.contract ? ' · ' + esc(beanTitle(p.contract)) : ''} · سند ${fa(p.number)}</small>`;
}

// ---------------------------------------------------------------------------------------------- posting card lines
function cardLines() {
  return books.statements.flatMap(s => s.lines.map(l => ({...l, statement: s.id, statementTitle: s.title})));
}
function lineScope() {
  const f = postFilter;
  return cardLines().filter(l => (!f.statement || l.statement === f.statement) && (!f.month || String(l.day || '').startsWith(f.month)) && (!f.kind || l.kind === f.kind) && (f.state === 'all' || l.state === f.state) && (!f.search || [l.what, l.category, l.posting?.accounts.map(accountLabel).join(' ')].some(v => String(v || '').toLocaleLowerCase().includes(f.search.toLocaleLowerCase()))));
}
function renderPosting() {
  if (!booksReady()) return waiting();
  const scope = lineScope();
  const statements = books.statements.map(s => {
    const opened = books.vouchers.some(v => v.kind === 'journal' && v.lines.some(l => l.account === '2101') && v.memo.includes(s.id) && !v.reversedBy);
    return `<div class="report-note"><b>${esc(s.title)}</b><div class="facts">${fact('بدهی ابتدای دوره (بانک)', money(s.opening))}${fact('بدهی پایان دوره (بانک)', money(s.closing))}${fact('خالص ردیف‌ها', money(s.net))}${fact('ثبت‌شده در دفتر', money(s.posted))}${fact('ثبت‌نشده', money(s.unposted))}${fact('ردیف‌ها', fa(s.counts.posted) + ' ثبت‌شده از ' + fa(s.lines.length))}</div>${opened ? '' : `<button class="secondary" data-bk="opening" data-statement="${esc(s.id)}">ثبت سند ماندهٔ ابتدای دوره</button> <small class="muted">بدهی ابتدای دورهٔ کارت را به حساب ۲۱۰۱ می‌آورد تا ماندهٔ دفتر با بانک تطبیق شود.</small>`}</div>`;
  }).join('');
  const all = scope.length && scope.every(l => selectedLines.has(l.statement + '|' + l.line));
  const chosen = [...selectedLines].map(k => k.split('|'));
  const rows = scope.map(l => {
    const key = l.statement + '|' + l.line;
    const state = l.state === 'posted' ? badge('ثبت‌شده', 'done') : l.state === 'mismatch' ? badge('ناهمخوان', 'late') : badge('ثبت‌نشده');
    const inst = l.installment ? `<small>قسط ${fa(l.installment.number)} از ${fa(l.installment.total)} · کل خرید ${money(l.installment.purchase_total?.count)}</small>` : '';
    const suggestion = l.state !== 'posted' && l.suggested ? `<small>پیشنهاد: ${esc(accountLabel(l.suggested))}${l.categoryInferred ? ' ' + badge('حدسی') : ''}</small>` : '';
    return `<tr><td><input type="checkbox" data-line="${esc(key)}" aria-label="انتخاب ردیف"${selectedLines.has(key) ? ' checked' : ''}></td><td>${esc(l.day || 'نامعلوم')}</td><td>${esc(l.what)}<small>${esc(kindNames[l.kind] || l.kind)}</small>${inst}</td><td class="num" dir="ltr">${money(l.amount)} ${esc(l.unit)}</td><td>${state}${postingSummary(l.posting)}${suggestion}</td><td class="actions"><button class="secondary" data-bk="post-one" data-line="${esc(key)}">${l.state === 'posted' ? 'تغییر' : 'ثبت'}</button>${l.posting ? `<button class="text-button" data-bk="reverse" data-ref="${esc(l.posting.ref)}">برگشت</button>` : ''}</td></tr>`;
  }).join('');
  const months = [...new Set(cardLines().map(l => String(l.day || '').slice(0, 7)).filter(Boolean))].sort();
  return `<section class="panel"><div class="panel-head"><div><h2>خریدهای کارت را به حساب‌ها ببر</h2><p>هر ردیف صورتحساب یک پرداخت از کارت است: حساب معین، مرکز هزینه و سهم افراد را تعیین کن. تغییر یک ردیف ثبت‌شده همان سند را اصلاح می‌کند؛ نسخهٔ قبلی در تاریخچه می‌ماند.</p></div></div>${statements}
  <div class="filters"><select id="pf-statement" aria-label="صورتحساب"><option value="">همهٔ صورتحساب‌ها</option>${books.statements.map(s => `<option value="${esc(s.id)}"${s.id === postFilter.statement ? ' selected' : ''}>${esc(s.title)}</option>`).join('')}</select><select id="pf-state" aria-label="وضعیت">${[['unposted', 'ثبت‌نشده'], ['posted', 'ثبت‌شده'], ['mismatch', 'ناهمخوان'], ['all', 'همه']].map(([k, n]) => `<option value="${k}"${k === postFilter.state ? ' selected' : ''}>${n}</option>`).join('')}</select><select id="pf-kind" aria-label="نوع ردیف"><option value="">همهٔ انواع</option>${Object.entries(kindNames).map(([k, n]) => `<option value="${k}"${k === postFilter.kind ? ' selected' : ''}>${n}</option>`).join('')}</select><select id="pf-month" aria-label="ماه"><option value="">همهٔ ماه‌ها</option>${months.map(m => `<option${m === postFilter.month ? ' selected' : ''}>${m}</option>`).join('')}</select><input type="search" id="pf-search" placeholder="جستجوی شرح یا حساب…" value="${esc(postFilter.search)}"></div>
  <div class="batch"><span>${fa(selectedLines.size)} ردیف انتخاب شده</span><button class="primary" data-bk="post-selected"${selectedLines.size ? '' : ' disabled'}>ثبت ردیف‌های انتخاب‌شده</button><button class="secondary" data-bk="accept-suggested"${chosen.some(([s, k]) => cardLines().find(l => l.statement === s && l.line === k && l.suggested && l.state === 'unposted')) ? '' : ' disabled'}>ثبت با حساب پیشنهادی هر ردیف</button>${selectedLines.size ? '<button class="text-button" data-bk="clear-selection">پاک کردن انتخاب</button>' : ''}</div>
  ${scope.length ? `<div class="table-scroll"><table><thead><tr><th><input type="checkbox" data-bk-all="1" aria-label="انتخاب همه"${all ? ' checked' : ''}></th><th>تاریخ</th><th>شرح</th><th>مبلغ</th><th>ثبت در دفتر</th><th></th></tr></thead><tbody>${rows}</tbody></table></div>` : '<div class="empty">ردیفی با این فیلتر نیست.</div>'}</section>
  ${renderContractPays()}`;
}
let showReversed = false;
function payState(p) {
  if (p.kind === 'reversal') return badge('سند معکوس', 'late');
  if (p.reversedBy) return badge('برگشت‌خورده', 'late');
  return p.accounts.length ? badge('ثبت‌شده', 'done') : badge('بدون حساب', 'late');
}
function renderContractPays() {
  const all = books.pays.slice().sort((a, b) => (a.date || '9999').localeCompare(b.date || '9999'));
  const open = all.filter(p => p.kind === 'pay' && !p.reversedBy);
  const pays = showReversed ? all : open;
  const waitingOnes = open.filter(p => !p.accounts.length);
  return `<section class="panel"><div class="panel-head"><div><h2>پرداخت‌های بیرون از کارت</h2><p>پرداخت‌های توافق‌ها (مثل حساب خانه) و پرداخت‌هایی که ${esc(me())} خودش ثبت کرده. ${fa(waitingOnes.length)} پرداخت هنوز حساب ندارد و در حساب ۱۹۰۲ منتظر است. <b>اگر پرداختی اشتباه ثبت شده</b> (توافق، پرداخت‌کننده، سهم‌ها، مبلغ یا تاریخ)، «اصلاح» همان سند را درست می‌کند و تاریخچه نسخهٔ قبلی را نگه می‌دارد؛ اگر اصلاً نباید ثبت می‌شد، در «اسناد حسابداری» «حذف» بزن.</p></div><label class="toggle"><input type="checkbox" data-bk-toggle="reversed"${showReversed ? ' checked' : ''}> نمایش برگشت‌خورده‌ها (${fa(all.length - open.length)})</label></div>${pays.length ? `<div class="table-scroll"><table><thead><tr><th>سند</th><th>تاریخ</th><th>توافق</th><th>شرح</th><th>پرداخت‌کننده</th><th>سهم‌ها</th><th>مبلغ</th><th>حساب</th><th></th></tr></thead><tbody>${pays.map(p => `<tr${p.kind === 'reversal' || p.reversedBy ? ' class="muted"' : ''}><td>${fa(p.number)}</td><td>${esc(p.date || 'نامعلوم')}</td><td>${esc(p.beanTitle)}</td><td>${esc(p.memo)}${p.warnings.length && !p.reversedBy && p.kind === 'pay' ? `<small>${p.warnings.map(esc).join('؛ ')}</small>` : ''}</td><td>${esc(person(p.by))}</td><td>${Object.keys(p.bears).length ? Object.entries(p.bears).map(([w, s]) => esc(person(w)) + ' ' + fa(s)).join('، ') : esc(person(p.by)) + ' به‌تنهایی'}</td><td class="num" dir="ltr">${money(p.amount)} ${esc(p.unit)}</td><td>${payState(p)}${p.accounts.length ? `<small>${esc(p.accounts.map(accountLabel).join('، '))}${p.analytic.length ? ' · ' + esc(p.analytic.map(centreLabel).join('، ')) : ''}</small>` : p.suggested && p.kind === 'pay' && !p.reversedBy ? `<small>پیشنهاد: ${esc(accountLabel(p.suggested))}</small>` : ''}</td><td class="actions">${p.kind === 'pay' && !p.reversedBy ? `<button class="secondary" data-bk="post-pay" data-ref="${esc(p.ref)}">حساب</button><button class="secondary" data-bk="correct" data-ref="${esc(p.ref)}">اصلاح</button><button class="text-button" data-bk="reverse" data-ref="${esc(p.ref)}">برگشت</button>` : `<button class="text-button" data-bk="goto-voucher" data-ref="${esc(p.ref)}">سند</button>`}</td></tr>`).join('')}</tbody></table></div>` : '<div class="empty">پرداختی بیرون از کارت ثبت نشده است.</div>'}</section>`;
}
// ---------------------------------------------------------------------------------------------- forms of the books
function openBooksForm(kind, bean, title, html, note = '') {
  if (stale) { notice('اطلاعات قدیمی است؛ ابتدا صفحه را به‌روزرسانی کنید.', true); return; }
  edit = {kind, bean, entry: '', head: data.head, request: crypto.randomUUID()};
  $('form-title').textContent = title;
  $('fields').innerHTML = html + `<p class="wide muted">${note || 'ذخیره از دروازهٔ دفتر می‌گذرد؛ اگر همین پرونده در همین دقیقه ذخیره شده باشد، تا یک دقیقه طول می‌کشد.'}</p>`;
  $('form-error').textContent = ''; $('save').disabled = false; if (!$('editor').open) $('editor').showModal();
}
function sharesEditor(contract, shares) {
  const c = books.contracts.find(x => x.id === contract);
  const parties = c ? c.parties : [books.me];
  return `<div class="wide shares" id="shares-box"><small>سهم هر نفر (نسبت؛ مثلاً ۱ و ۱ یعنی نصف‌نصف)</small>${parties.map(p => `<label>${esc(person(p))}<input type="text" inputmode="decimal" data-share="${esc(p)}" value="${esc(shares?.[p] ?? '1')}"></label>`).join('')}</div>`;
}
function openPostCard(keys, {accountCode = '', suggested = false} = {}) {
  const lines = keys.map(([s, k]) => cardLines().find(l => l.statement === s && l.line === k)).filter(Boolean);
  if (!lines.length) return;
  const statement = lines[0].statement;
  if (lines.some(l => l.statement !== statement)) { notice('ردیف‌های یک صورتحساب را با هم ثبت کن.', true); return; }
  const first = lines[0].posting;
  const sugg = [...new Set(lines.map(l => l.suggested).filter(Boolean))];
  const total = lines.reduce((n, l) => n + cents(l.amount), 0n);
  const shared = first && Object.keys(first.bears || {}).length > 0;
  const html = `<div class="wide facts">${fact('ردیف‌ها', fa(lines.length))}${fact('جمع مبلغ', W.money.show(fromCents(total), lines[0].unit))}${lines.length === 1 ? fact('شرح', lines[0].what) + fact('تاریخ', lines[0].day) : ''}</div>
  ${suggested ? `<p class="wide report-note">هر ردیف با حساب پیشنهادی خودش ثبت می‌شود (${sugg.map(accountLabel).map(esc).join('، ')}). ردیف‌های بدون پیشنهاد کنار گذاشته می‌شوند.</p><input type="hidden" id="post-suggested" value="1">` : `<label>حساب معین *<select id="post-account" required>${accountOptions(accountCode || first?.accounts[0] || (sugg.length === 1 ? sugg[0] : ''))}</select></label>`}
  <label>مرکز هزینه<select name="analytic">${centreOptions(first?.analytic[0] || '')}</select></label>
  <label>چه کسی هزینه را می‌دهد؟<select id="post-sharing"><option value="">فقط ${esc(me())}</option>${books.contracts.map(c => `<option value="${esc(c.id)}"${first?.contract === c.id && shared ? ' selected' : ''}>تقسیم در توافق: ${esc(c.title)}</option>`).join('')}</select></label>
  <div class="wide" id="shares-slot">${shared ? sharesEditor(first.contract, first.bears) : ''}</div>
  <label class="wide">توضیح<textarea name="note" maxlength="500"></textarea></label>
  ${lines.length === 1 ? replacesField(lines[0]) : '<input type="hidden" name="replaces" value="">'}
  <input type="hidden" name="contract" id="post-contract" value="${shared ? esc(first.contract) : ''}">`;
  postingKeys = lines.map(l => suggested ? {line: l.line, account: l.suggested} : l.line).filter(k => typeof k === 'string' || k.account);
  openBooksForm('post-card', statement, lines.some(l => l.state === 'posted') ? 'تغییر ثبت ردیف‌ها' : 'ثبت ردیف‌های کارت در دفتر', html,
    lines.some(l => l.state === 'posted') ? 'ثبت این ردیف در جای خودش اصلاح می‌شود: گفتهٔ قبلی برداشته و گفتهٔ تازه نوشته می‌شود؛ روزنامه تغییر را می‌نویسد و نسخهٔ قبلی در تاریخچه می‌ماند.' : '');
}
let postingKeys = [], journalLines = [];
function replacesField(line) {
  const same = books.pays.filter(p => p.kind === 'pay' && !p.reversedBy && p.by === books.me && p.unit === line.unit && cents(p.amount) === cents(line.amount));
  return `<label class="wide">این خرید قبلاً به‌صورت پرداخت ثبت شده؟<select name="replaces" id="post-replaces"><option value="">نه، ثبت تازه است</option>${same.map(p => `<option value="${esc(p.ref)}">بله: ${esc(p.date || 'بی‌تاریخ')} · ${esc(p.memo)} · ${esc(p.beanTitle)} (سند ${fa(p.number)})</option>`).join('')}</select><small>${same.length ? 'پرداخت قبلی با سند معکوس برمی‌گردد تا خرید دوبار شمرده نشود؛ توافق، سهم‌ها و حسابش اینجا پیش‌فرض می‌شوند.' : 'پرداختی با همین مبلغ پیدا نشد.'}</small></label>`;
}
function openPostPay(ref) {
  const p = books.pays.find(x => x.ref === ref); if (!p) return;
  const html = `<div class="wide facts">${fact('توافق', p.beanTitle)}${fact('شرح', p.memo)}${fact('مبلغ', W.money.show(p.amount, p.unit))}${fact('پرداخت‌کننده', person(p.by))}</div>
  <input type="hidden" name="pay" value="${esc(p.id)}">
  <label>حساب معین سهم ${esc(me())} *<select name="account" required>${accountOptions(p.accounts[0] || p.suggested || '')}</select></label>
  <label>مرکز هزینه<select name="analytic">${centreOptions(p.analytic[0] || '')}</select></label>
  ${p.by === books.me ? `<label>${esc(me())} از کجا پرداخت کرد؟<select name="from_account">${accountOptions(p.fromAccount || '', {empty: 'نامعلوم (حساب ۱۹۰۱)'})}</select></label>` : '<input type="hidden" name="from_account" value="">'}
  <input type="hidden" name="shares" value="">`;
  openBooksForm('post-pay', p.bean, p.accounts.length ? 'تغییر حساب پرداخت' : 'تعیین حساب پرداخت', html,
    p.accounts.length ? 'تغییر، پرداخت قبلی را با سند معکوس برگشت می‌زند و پرداخت تازه با حساب جدید ثبت می‌کند.' : '');
}
async function openEdit(ref) {
  const v = books.vouchers.find(x => x.ref === ref);
  if (v && v.source) { openPostCard([[v.source.bean, v.source.line]]); return; }        // a card line: its posting
  if (v && v.kind === 'journal') { openEntryEdit(v); return; }
  const p = books.pays.find(x => x.ref === ref); if (!p) { notice('این سند از این صفحه ویرایش نمی‌شود.', true); return; }
  if (p.reversedBy) { notice('این پرداخت در یک برگشت رسمی آمده است؛ سند برگشت را حذف کنید، نه خود پرداخت را.', true); return; }
  const w = (await fetchHistory(ref)).whose;
  const shared = !!p.contract;
  const html = `<div class="wide facts">${fact('سند', fa(p.number))}${fact('ثبت فعلی', p.beanTitle)}${fact('مبلغ', W.money.show(p.amount, p.unit))}${fact('پرداخت‌کننده', person(p.by))}</div>
  ${w && !w.mine ? `<p class="wide warn">این سند ${esc(w.why)} است. اگر اصلاحش کنی، نسخهٔ تازه گفتهٔ خود توست و نسخهٔ قبلی به نام گوینده‌اش در تاریخچه می‌ماند. اگر فقط با آن مخالفی، به‌جای اصلاح «اعتراض» بزن.</p>` : ''}
  <input type="hidden" name="pay" value="${esc(p.id)}">
  <label class="wide">شرح<input name="what" maxlength="500" value="${esc(p.note || '')}"></label>
  <label>تاریخ واقعی پرداخت<input type="date" name="day" value="${esc(p.date || '')}"></label>
  <label>مبلغ کل *<input name="count" inputmode="decimal" required value="${esc(p.amount)}"></label>
  <label>ارز *<select name="unit">${(data.currencies || []).map(c => `<option${c.code === p.unit ? ' selected' : ''}>${esc(c.code)}</option>`).join('')}</select></label>
  <label>چه کسی پرداخت کرد؟ *<select name="payer">${books.persons.filter(x => x.known).map(x => `<option value="${esc(x.id)}"${x.id === p.by ? ' selected' : ''}>${esc(x.title)}</option>`).join('')}</select></label>
  <label class="wide">در کدام توافق و چه کسی هزینه را می‌دهد؟<select id="post-sharing"><option value="">فقط ${esc(me())} — بیرون از توافق‌ها (دفتر روزنامهٔ ${esc(me())})</option>${books.contracts.map(c => `<option value="${esc(c.id)}"${p.contract === c.id ? ' selected' : ''}>در توافق: ${esc(c.title)}</option>`).join('')}</select></label>
  <div class="wide" id="shares-slot">${shared ? sharesEditor(p.contract, Object.keys(p.bears).length ? p.bears : {[p.by]: '1'}) : ''}</div>
  <input type="hidden" name="contract" id="post-contract" value="${esc(p.contract || '')}">
  <label>حساب معین سهم ${esc(me())}<select name="account">${accountOptions(p.accounts[0] || p.suggested || '', {empty: 'بعداً (حساب ۱۹۰۲)'})}</select></label>
  <label>مرکز هزینه<select name="analytic">${centreOptions(p.analytic[0] || '')}</select></label>
  <label>${esc(me())} از کجا پرداخت کرد؟<select name="from_account">${accountOptions(p.fromAccount || '', {empty: 'نامعلوم یا دیگری پرداخته (۱۹۰۱)'})}</select></label>
  <label class="wide">علت اصلاح *<textarea name="reason" required maxlength="500" placeholder="مثلاً: به‌اشتباه در توافق گیلاس ثبت شده بود"></textarea></label>`;
  openBooksForm('edit-pay', p.bean, 'اصلاح سند ' + fa(p.number), html, 'روش دفتر: گفتهٔ قبلی برداشته و گفتهٔ درست نوشته می‌شود؛ روزنامه هر تغییر و علتش را می‌نویسد و نسخهٔ قبلی در تاریخچه (گیت) می‌ماند. مانده‌ها، تراز و گزارش تحلیلی همه از همین گفته‌ها خوانده می‌شوند.');
}
function openEntryEdit(v) {
  const e = v.lines.map(l => ({account: l.account, person: l.person || '', analytic: l.analytic[0] || '', debit: qsign(q(l.dr)) ? l.dr : '', credit: qsign(q(l.cr)) ? l.cr : '', memo: l.memo || ''}));
  openJournal({date: v.date, memo: v.memo, unit: v.unit, lines: e});
  edit.kind = 'edit-entry';
  $('form-title').textContent = 'اصلاح سند ' + fa(v.number);
  $('fields').insertAdjacentHTML('beforeend', `<input type="hidden" name="voucher" value="${esc(v.ref)}"><label class="wide">علت اصلاح *<textarea name="reason" required maxlength="500"></textarea></label>`);
}
function openDelete(ref) {
  const v = books.vouchers.find(x => x.ref === ref); if (!v) return;
  openBooksForm('delete-doc', v.kind === 'journal' ? gardenerId() : v.bean, 'حذف سند ' + fa(v.number), `<div class="wide facts">${fact('تاریخ', v.date)}${fact('شرح', v.memo)}${fact('مبلغ', W.money.show(v.total, v.unit))}${fact('در', v.beanTitle)}</div>
  <input type="hidden" name="voucher" value="${esc(v.ref)}"><label class="wide">علت حذف *<textarea name="reason" required maxlength="500" placeholder="مثلاً: تکراری ثبت شده بود"></textarea></label>`,
  'فقط برای سندی که اصلاً نباید ثبت می‌شد. سند و همهٔ ردیف‌هایش برداشته می‌شوند؛ روزنامه آن را با علتش نام می‌برد و نسخه‌اش در تاریخچه (گیت) می‌ماند. اگر از ردیف کارت آمده باشد، آن ردیف دوباره ثبت‌نشده می‌شود.');
}
function openDispute(ref) {
  const v = books.vouchers.find(x => x.ref === ref); if (!v) return;
  openBooksForm('dispute-pay', v.bean, 'اعتراض به سند ' + fa(v.number), `<div class="wide facts">${fact('شرح', v.memo)}${fact('مبلغ', W.money.show(v.total, v.unit))}${fact('در', v.beanTitle)}</div>
  <input type="hidden" name="voucher" value="${esc(v.ref)}"><label class="wide">علت اعتراض *<textarea name="reason" required maxlength="500"></textarea></label>`,
  'وقتی سند گفتهٔ کس دیگری است (مثلاً طرف دیگر یک توافق) و نمی‌خواهی جای او حرف بزنی: نظر تو کنار گفتهٔ او ثبت می‌شود و هر دو می‌مانند تا با هم روشنش کنید.');
}
async function fetchHistory(ref) {
  if (!histories[ref] || histories[ref].head !== data.head) {
    try { const r = await fetch('/api/history?ref=' + encodeURIComponent(ref), {cache: 'no-store'}); histories[ref] = {...await r.json(), head: data.head}; }
    catch { histories[ref] = {history: [], whose: null, head: data.head}; }
  }
  return histories[ref];
}
function historyHTML(ref) {
  const h = histories[ref];
  if (!h) return '<p class="muted">در حال خواندن تاریخچه…</p>';
  return `<div class="history"><b>تاریخچهٔ این سند</b>${h.whose ? `<small>${esc(h.whose.why)}</small>` : ''}${(h.history || []).map(c => `<details><summary>${esc(new Date(c.when).toLocaleString('fa-IR'))} · ${esc(c.subject)} <small dir="ltr">${esc(c.commit)}</small></summary>${c.journal.length ? `<ul>${c.journal.map(l => `<li>${esc(l)}</li>`).join('')}</ul>` : ''}${c.changes.length ? `<pre dir="ltr">${c.changes.map(esc).join('\n')}</pre>` : ''}</details>`).join('') || '<p class="muted">تاریخچه‌ای پیدا نشد.</p>'}</div>`;
}
function openReverse(ref) {
  const v = books.vouchers.find(x => x.ref === ref); if (!v) return;
  if (v.reversedBy) { notice('این سند پیش‌تر برگشت خورده است.', true); return; }
  const html = `<div class="wide facts">${fact('سند', fa(v.number))}${fact('تاریخ', v.date)}${fact('شرح', v.memo)}${fact('مبلغ', W.money.show(v.total, v.unit))}</div>
  <input type="hidden" name="voucher" value="${esc(v.ref)}">
  <label>تاریخ سند معکوس<input type="date" name="date" value="${esc(data.asOf)}"></label>
  <label class="wide">علت برگشت *<textarea name="reason" required maxlength="500"></textarea></label>`;
  openBooksForm('reverse', v.kind === 'journal' ? gardenerId() : v.bean, 'سند معکوس', html, 'سند اصلی در دفتر می‌ماند و سند معکوس اثر آن را خنثی می‌کند. اگر سند از ردیف کارت آمده باشد، ردیف دوباره ثبت‌نشده می‌شود.');
}
function journalRowHTML(l, n) {
  const a = account(l.account);
  return `<tr><td><select data-jl="${n}" data-f="account">${accountOptions(l.account || '', {empty: 'حساب'})}</select></td><td><select data-jl="${n}" data-f="person"${a?.detail === 'person' ? '' : ' disabled'}><option value="">—</option>${books.persons.filter(p => p.known).map(p => `<option value="${esc(p.id)}"${p.id === l.person ? ' selected' : ''}>${esc(p.title)}</option>`).join('')}</select></td><td><select data-jl="${n}" data-f="analytic">${centreOptions(l.analytic || '', '—')}</select></td><td><input data-jl="${n}" data-f="debit" inputmode="decimal" value="${esc(l.debit || '')}" aria-label="بدهکار"></td><td><input data-jl="${n}" data-f="credit" inputmode="decimal" value="${esc(l.credit || '')}" aria-label="بستانکار"></td><td><input data-jl="${n}" data-f="memo" value="${esc(l.memo || '')}" aria-label="شرح ردیف"></td><td><button type="button" class="text-button" data-bk="jl-remove" data-n="${n}" aria-label="حذف ردیف">×</button></td></tr>`;
}
function journalTotals() {
  const sum = f => journalLines.reduce((n, l) => n + cents(normalizeAmount(l[f] || '0')), 0n);
  const d = sum('debit'), c = sum('credit');
  return `جمع بدهکار ${money(fromCents(d))} · جمع بستانکار ${money(fromCents(c))} ${d === c && d ? badge('تراز', 'done') : badge('تراز نیست', 'late')}`;
}
function normalizeAmount(v) { return String(v).replace(/[۰-۹]/g, d => '۰۱۲۳۴۵۶۷۸۹'.indexOf(d)).replace(/[٠-٩]/g, d => '٠١٢٣٤٥٦٧٨٩'.indexOf(d)).replace('٫', '.').replace(/[,٬]/g, '') || '0'; }
function openJournal(prefill) {
  journalLines = prefill?.lines || [{account: '', debit: ''}, {account: '', credit: ''}];
  const html = `<label>تاریخ سند *<input type="date" name="date" required value="${esc(prefill?.date || data.asOf)}"></label>
  <label>ارز *<select name="unit">${(data.currencies || []).map(c => `<option value="${esc(c.code)}"${c.code === (prefill?.unit || 'TRY') ? ' selected' : ''}>${esc(c.code)}</option>`).join('')}</select></label>
  <label class="wide">شرح سند *<input name="memo" required maxlength="500" value="${esc(prefill?.memo || '')}"></label>
  <div class="wide table-scroll"><table class="journal-lines"><thead><tr><th>حساب</th><th>شخص</th><th>مرکز هزینه</th><th>بدهکار</th><th>بستانکار</th><th>شرح</th><th></th></tr></thead><tbody id="jl-body">${journalLines.map(journalRowHTML).join('')}</tbody></table></div>
  <p class="wide" id="jl-totals">${journalTotals()}</p><p class="wide"><button type="button" class="secondary" data-bk="jl-add">＋ ردیف</button></p>`;
  openBooksForm('journal', gardenerId(), 'سند دستی تازه', html, 'برای مانده‌های افتتاحیه، جابه‌جایی بین حساب‌های خود ' + me() + ' یا اصلاحی که هیچ پرداختی نمی‌گوید. هر ردیف یا بدهکار است یا بستانکار.');
}
function openChartRow(scheme, code = '', parent = '') {
  const rows = scheme === 'account' ? books.chart.accounts : books.chart.analytic;
  const r = rows.find(x => x.code === code);
  const levels = scheme === 'account' ? ['group', 'general', 'subsidiary'] : ['plan', 'account'];
  const p = rows.find(x => x.code === (r ? r.parent : parent));
  const level = r ? r.level : p ? levels[levels.indexOf(p.level) + 1] : levels[0];
  const linkable = books.beans.filter(b => b.kind !== 'document' || b.id.startsWith('card'));
  const html = `<input type="hidden" name="scheme" value="${scheme}"><input type="hidden" name="original" value="${esc(code)}"><input type="hidden" name="level" value="${esc(level)}"><input type="hidden" name="parent" value="${esc(r ? r.parent || '' : parent)}">
  <div class="wide facts">${fact('سطح', levelNames[level])}${fact('زیرِ', p ? p.code + ' — ' + p.name : 'بالاترین سطح')}</div>
  <label>کد *<input name="code" required value="${esc(code || '')}" ${code ? 'readonly' : ''} dir="ltr" placeholder="${scheme === 'account' ? (p ? p.code + '01' : '7') : 'travel'}"></label>
  <label>نام *<input name="name" required maxlength="120" value="${esc(r?.name || '')}"></label>
  ${scheme === 'account' && level === 'group' ? `<label>نوع *<select name="type">${Object.entries(typeNames).map(([k, n]) => `<option value="${k}"${r?.type === k ? ' selected' : ''}>${n}</option>`).join('')}</select></label>` : '<input type="hidden" name="type" value="">'}
  ${scheme === 'account' ? `<label>حساب تفصیلی<select name="detail"><option value="">ندارد</option><option value="person"${r?.detail === 'person' ? ' selected' : ''}>شخص لازم است</option></select></label>` : ''}
  <label>وضعیت<select name="status"><option value="">فعال</option><option value="closed"${r?.status === 'closed' ? ' selected' : ''}>بسته</option></select></label>
  <fieldset class="wide links"><legend>پیوند به توافق‌ها، کارت‌ها و اشخاص</legend>${linkable.map(b => `<label><input type="checkbox" data-link="${esc(b.id)}"${r?.links?.includes(b.id) ? ' checked' : ''}> ${esc(b.title)}</label>`).join('')}</fieldset>
  <input type="hidden" name="links" id="chart-links" value="${esc((r?.links || []).join(' '))}">`;
  openBooksForm('chart-account', gardenerId(), code ? 'ویرایش حساب' : 'حساب تازه', html, code && r?.used ? 'این حساب در اسناد به کار رفته است: نامش را می‌توان عوض کرد یا بست، ولی جابه‌جا نمی‌شود.' : '');
}

// The form's own fields are named; the shares, the lines and the links are gathered here as the form is read.
$('entry-form').addEventListener('formdata', e => {
  if (!edit || !BOOK_KINDS.has(edit.kind)) return;
  const fd = e.formData;
  if (edit.kind === 'post-card') {
    const box = $('shares-box');
    fd.set('shares', box && $('post-contract').value ? JSON.stringify(Object.fromEntries([...box.querySelectorAll('[data-share]')].map(i => [i.dataset.share, normalizeAmount(i.value)]))) : '');
    fd.set('lines', JSON.stringify(postingKeys));
    fd.set('account', $('post-suggested') ? '' : $('post-account')?.value || '');
    if (!fd.has('contract')) fd.set('contract', '');
  }
  if (edit.kind === 'edit-pay') {
    const box = $('shares-box');
    fd.set('shares', box && $('post-contract').value ? JSON.stringify(Object.fromEntries([...box.querySelectorAll('[data-share]')].map(i => [i.dataset.share, normalizeAmount(i.value)]))) : '');
    fd.set('count', normalizeAmount(String(fd.get('count') || '').trim()));
  }
  if (edit.kind === 'journal' || edit.kind === 'edit-entry') fd.set('lines', JSON.stringify(journalLines.filter(l => l.account || l.debit || l.credit).map(l => ({...l, debit: l.debit ? normalizeAmount(l.debit) : '', credit: l.credit ? normalizeAmount(l.credit) : ''}))));
  if (edit.kind === 'chart-account') {
    fd.set('links', [...document.querySelectorAll('[data-link]:checked')].map(i => i.dataset.link).join(' '));
    if (!fd.has('detail')) fd.set('detail', '');
  }
});

// ---------------------------------------------------------------------------------------------- vouchers
function renderVouchers() {
  if (!booksReady()) return waiting();
  const f = voucherFilter;
  const rows = books.vouchers.filter(v => (!f.kind || v.kind === f.kind) && (!f.account || v.lines.some(l => l.account === f.account)) && (!period.from || (v.date && v.date >= period.from)) && (!period.to || (v.date && v.date <= period.to)) && (!f.search || [v.memo, v.ref, String(v.number)].some(x => String(x || '').toLocaleLowerCase().includes(f.search.toLocaleLowerCase())))).slice().reverse();
  return `<section class="panel"><div class="panel-head"><div><h2>اسناد حسابداری</h2><p>هر پرداخت یک سند است و هر سند دستی ${esc(me())} هم. سند اشتباه را «اصلاح» یا «حذف» کن (روش دفتر: گفتهٔ قبلی برداشته و گفتهٔ درست نوشته می‌شود؛ تاریخچه همه را نگه می‌دارد). «سند معکوس» فقط برای برگشت واقعی است، مثل پس‌دادن پول.</p></div><button class="primary" data-bk="journal">＋ سند دستی</button></div>${periodBar('vp')}
  <div class="filters"><input type="search" id="vf-search" placeholder="جستجوی شرح یا شمارهٔ سند…" value="${esc(f.search)}"><select id="vf-kind" aria-label="نوع سند"><option value="">همهٔ اسناد</option>${Object.entries(voucherKinds).map(([k, n]) => `<option value="${k}"${k === f.kind ? ' selected' : ''}>${n}</option>`).join('')}</select><select id="vf-account" aria-label="حساب">${accountOptions(f.account, {postableOnly: false, empty: 'همهٔ حساب‌ها'})}</select></div>
  ${rows.length ? rows.map(voucherCard).join('') : '<div class="empty">سندی با این فیلتر نیست.</div>'}</section>`;
}
function voucherCard(v) {
  const open = openVouchers.has(v.ref);
  const reversedBy = v.reversedBy && books.vouchers.find(x => x.ref === v.reversedBy);
  const reverses = v.reverses && books.vouchers.find(x => x.ref === v.reverses);
  return `<div class="voucher${v.reversedBy ? ' reversed' : ''}"><button class="voucher-head" data-bk="toggle" data-ref="${esc(v.ref)}" aria-expanded="${open}"><b>سند ${fa(v.number)}</b><span>${esc(v.date || 'بدون تاریخ')}</span><span>${esc(v.memo || '—')}</span><span>${badge(voucherKinds[v.kind] || v.kind, v.kind === 'reversal' ? 'late' : '')}${reversedBy ? badge('برگشت‌خورده با سند ' + fa(reversedBy.number), 'late') : ''}${reverses ? badge('برگشتِ سند ' + fa(reverses.number)) : ''}${v.warnings.length ? badge('⚠ ' + fa(v.warnings.length)) : ''}</span><span class="num" dir="ltr">${money(v.total)} ${esc(v.unit)}</span></button>
  ${open ? `<div class="voucher-body"><small>${esc(v.beanTitle)} · <span dir="ltr">${esc(v.ref)}</span></small>${v.warnings.length ? `<p class="warn">${v.warnings.map(esc).join('<br>')}</p>` : ''}<div class="table-scroll"><table><thead><tr><th>حساب</th><th>تفصیلی</th><th>مرکز هزینه</th><th>بدهکار</th><th>بستانکار</th></tr></thead><tbody>${v.lines.map(l => `<tr><td>${esc(l.account)} — ${esc(l.accountName)}${l.memo ? `<small>${esc(l.memo)}</small>` : ''}</td><td>${l.person ? esc(person(l.person)) : ''}${l.contract ? `<small>${esc(beanTitle(l.contract))}</small>` : ''}</td><td>${l.analytic.map(centreLabel).map(esc).join('، ')}</td><td class="num" dir="ltr">${qsign(q(l.dr)) ? money(l.dr) : ''}</td><td class="num" dir="ltr">${qsign(q(l.cr)) ? money(l.cr) : ''}</td></tr>`).join('')}</tbody></table></div><div class="voucher-actions"><button class="secondary" data-bk="correct" data-ref="${esc(v.ref)}">اصلاح</button><button class="secondary" data-bk="delete" data-ref="${esc(v.ref)}">حذف</button>${v.kind !== 'journal' ? `<button class="text-button" data-bk="dispute" data-ref="${esc(v.ref)}">اعتراض</button>` : ''}<button class="text-button" data-bk="history" data-ref="${esc(v.ref)}">تاریخچه</button>${!v.reverses && !v.reversedBy ? `<button class="text-button" data-bk="reverse" data-ref="${esc(v.ref)}">سند معکوس (رویداد واقعی)</button>` : ''}</div>${histories[v.ref] && histories[v.ref].shown ? historyHTML(v.ref) : ''}</div>` : ''}</div>`;
}

// ---------------------------------------------------------------------------------------------- the chart
function renderChart() {
  if (!booksReady()) return waiting();
  const scheme = chartScheme;
  if (scheme === 'details') return renderDetails();
  const rows = scheme === 'account' ? books.chart.accounts.slice().sort((a, b) => a.path.join('.').localeCompare(b.path.join('.'))) : books.chart.analytic.slice().sort((a, b) => (a.plan + (a.level === 'plan' ? '' : '.' + a.code)).localeCompare(b.plan + (b.level === 'plan' ? '' : '.' + b.code)));
  const closing = Object.fromEntries(books.trial.rows.map(r => [r.code, r.closing]));
  return `<section class="panel"><div class="panel-head"><div><h2>سرفصل حساب‌ها</h2><p>گروه ← کل ← معین؛ اسناد فقط به حساب معین می‌خورند. حساب‌های تفصیلی، خود اشخاص و توافق‌ها و مراکز هزینه‌اند. حسابِ به‌کاررفته را می‌توان بست، نه پاک کرد.</p></div><div class="header-actions"><button class="${scheme === 'account' ? 'primary' : 'secondary'}" data-bk="scheme" data-scheme="account">حساب‌های دفتر</button><button class="${scheme === 'analytic' ? 'primary' : 'secondary'}" data-bk="scheme" data-scheme="analytic">مراکز هزینه</button><button class="secondary" data-bk="scheme" data-scheme="details">اشخاص (تفصیلی)</button></div></div>
  <div class="table-scroll"><table><thead><tr><th>کد</th><th>نام</th><th>سطح</th>${scheme === 'account' ? '<th>نوع</th><th>مانده</th>' : ''}<th>پیوندها</th><th>وضعیت</th><th></th></tr></thead><tbody>${rows.map(r => `<tr class="level-${esc(r.level)}"><td dir="ltr">${esc(r.code)}</td><td data-pad="${scheme === 'account' ? (r.path.length - 1) * 18 + 8 : r.level === 'plan' ? 8 : 26}">${esc(r.name)}${r.detail === 'person' ? '<small>تفصیلی: شخص</small>' : ''}</td><td>${levelNames[r.level] || esc(r.level)}</td>${scheme === 'account' ? `<td>${typeNames[r.type] || ''}</td><td class="num" dir="ltr">${closing[r.code] ? money(closing[r.code]) : ''}</td>` : ''}<td>${(r.links || []).map(b => `<small>${esc(beanTitle(b))}</small>`).join('')}</td><td>${r.status === 'closed' ? badge('بسته', 'late') : r.used ? badge('به‌کاررفته', 'done') : ''}</td><td class="actions"><button class="text-button" data-bk="chart-edit" data-code="${esc(r.code)}">ویرایش</button>${r.postable ? '' : `<button class="text-button" data-bk="chart-add" data-parent="${esc(r.code)}">＋ زیرحساب</button>`}</td></tr>`).join('')}</tbody></table></div>
  <p><button class="secondary" data-bk="chart-add" data-parent="">＋ ${scheme === 'account' ? 'گروه حساب تازه' : 'طرح تحلیلی تازه'}</button></p></section>`;
}

function renderDetails() {
  return `<section class="panel"><div class="panel-head"><div><h2>اشخاص — حساب‌های تفصیلی</h2><p>هر شخص حساب تفصیلی خودش را زیر «حساب جاری اشخاص» (۱۳۰۱) دارد: سهم‌هایی که بر عهده دارد و پرداخت‌هایی که کرده، به تفکیک توافق. شخص تازه از پرونده‌اش در دفتر ساخته می‌شود و با توافقی که در آن طرف است اینجا می‌آید.</p></div><div class="header-actions"><button class="secondary" data-bk="scheme" data-scheme="account">حساب‌های دفتر</button><button class="secondary" data-bk="scheme" data-scheme="analytic">مراکز هزینه</button><button class="primary" data-bk="scheme" data-scheme="details">اشخاص (تفصیلی)</button></div></div>
  <div class="table-scroll"><table><thead><tr><th>شخص</th><th>توافق‌ها</th><th>مانده</th><th></th></tr></thead><tbody>${books.details.map(d => `<tr><td><b>${esc(d.title)}</b>${d.known ? '' : '<small>هنوز در دفتر ثبت نشده</small>'}</td><td>${d.contracts.map(c => `<small>${esc(c.title)}</small>`).join('') || '—'}</td><td>${d.balances.map(b => `<span class="num" dir="ltr">${money(b.balance)} ${esc(b.unit)}</span><small>${qsign(q(b.balance)) > 0 ? 'به ' + esc(me()) + ' بدهکار است' : qsign(q(b.balance)) < 0 ? esc(me()) + ' به او بدهکار است' : 'تسویه'}</small>`).join('') || '—'}</td><td class="actions">${d.balances.length ? `<button class="text-button" data-bk="person-ledger" data-person="${esc(d.id)}">دفتر تفصیلی</button>` : ''}</td></tr>`).join('')}</tbody></table></div></section>`;
}

// ---------------------------------------------------------------------------------------------- reports
const reportNames = {trial: 'تراز آزمایشی', ledger: 'دفتر حساب', people: 'حساب اشخاص', analytic: 'گزارش تحلیلی', card: 'تطبیق کارت', checks: 'بررسی‌ها'};
function renderFinance() {
  if (!booksReady()) return waiting();
  const body = {trial: trialReport, ledger: ledgerReport, people: peopleReport, analytic: analyticReport, card: cardReport, checks: checksReport}[reportTab]();
  return `<section class="panel"><div class="sub-tabs" role="tablist">${Object.entries(reportNames).map(([k, n]) => `<button role="tab" aria-selected="${k === reportTab}" class="${k === reportTab ? 'primary' : 'secondary'}" data-bk="report" data-report="${k}">${n}${k === 'checks' && books.checks.length ? ' ' + fa(books.checks.length) : ''}</button>`).join('')}</div>${['trial', 'ledger', 'analytic'].includes(reportTab) ? periodBar('rp') : ''}<h2 class="print-heading">${reportNames[reportTab]} — ${esc(period.from || 'آغاز')} تا ${esc(period.to || 'امروز')} · ${esc(period.unit)}</h2>${body}<p><button class="secondary" id="print">چاپ / PDF</button></p></section>`;
}
function trialReport() {
  const t = books.trial;
  return `<p>${t.balanced ? badge('دفتر تراز است', 'done') : badge('دفتر تراز نیست', 'late')}${t.undated ? ' ' + badge(fa(t.undated) + ' سند بی‌تاریخ بیرون از بازه') : ''}</p><div class="table-scroll"><table><thead><tr><th>کد</th><th>حساب</th><th>ماندهٔ ابتدا</th><th>بدهکار</th><th>بستانکار</th><th>ماندهٔ پایان</th></tr></thead><tbody>${t.rows.map(r => `<tr class="level-${esc(r.level)}"><td dir="ltr">${esc(r.code)}</td><td>${r.level === 'subsidiary' ? `<button class="text-button" data-bk="ledger" data-code="${esc(r.code)}">${esc(r.name)}</button>` : `<b>${esc(r.name)}</b>`}</td><td class="num" dir="ltr">${money(r.opening)}</td><td class="num" dir="ltr">${money(r.dr)}</td><td class="num" dir="ltr">${money(r.cr)}</td><td class="num" dir="ltr">${money(r.closing)}</td></tr>`).join('')}<tr class="total"><td></td><td>جمع</td><td class="num" dir="ltr">${money(t.totals.opening)}</td><td class="num" dir="ltr">${money(t.totals.dr)}</td><td class="num" dir="ltr">${money(t.totals.cr)}</td><td class="num" dir="ltr">${money(t.totals.closing)}</td></tr></tbody></table></div><p class="muted">مانده مثبت یعنی بدهکار (دارایی و هزینه)، منفی یعنی بستانکار (بدهی، سرمایه، درآمد).</p>`;
}
function ledgerReport() {
  const codes = Object.keys(books.ledgers);
  const code = codes.includes(ledgerChoice.code) ? ledgerChoice.code : codes[0];
  if (!code) return '<div class="empty">هنوز سندی نیست.</div>';
  const lg = books.ledgers[code];
  const persons = [...new Set(lg.rows.map(r => r.person).filter(Boolean))];
  let run = ledgerChoice.person ? Q0 : q(lg.opening);
  const rows = lg.rows.filter(r => !ledgerChoice.person || r.person === ledgerChoice.person).map(r => { run = qsub(qadd(run, q(r.dr)), q(r.cr)); return {...r, running: qtext(run)}; });
  return `<div class="filters"><select id="lg-code" aria-label="حساب">${codes.map(c => `<option value="${esc(c)}"${c === code ? ' selected' : ''}>${esc(accountLabel(c))}</option>`).join('')}</select>${persons.length ? `<select id="lg-person" aria-label="شخص"><option value="">همهٔ اشخاص</option>${persons.map(p => `<option value="${esc(p)}"${p === ledgerChoice.person ? ' selected' : ''}>${esc(person(p))}</option>`).join('')}</select>` : ''}</div>
  ${ledgerChoice.person ? '' : `<p>ماندهٔ ابتدای بازه: <b dir="ltr">${money(lg.opening)}</b></p>`}<div class="table-scroll"><table><thead><tr><th>سند</th><th>تاریخ</th><th>شرح</th><th>تفصیلی</th><th>بدهکار</th><th>بستانکار</th><th>مانده</th></tr></thead><tbody>${rows.map(r => `<tr><td><button class="text-button" data-bk="goto-voucher" data-ref="${esc(r.ref)}">${fa(r.number)}</button></td><td>${esc(r.date || '—')}</td><td>${esc(r.memo)}</td><td>${r.person ? esc(person(r.person)) : ''}${r.contract ? `<small>${esc(beanTitle(r.contract))}</small>` : ''}</td><td class="num" dir="ltr">${qsign(q(r.dr)) ? money(r.dr) : ''}</td><td class="num" dir="ltr">${qsign(q(r.cr)) ? money(r.cr) : ''}</td><td class="num" dir="ltr">${money(r.running)}</td></tr>`).join('')}</tbody></table></div>`;
}
function peopleReport() {
  return books.people.length ? `<div class="table-scroll"><table><thead><tr><th>شخص</th><th>توافق</th><th>مانده</th><th>یعنی</th></tr></thead><tbody>${books.people.flatMap(p => [...p.contracts.map(c => `<tr><td>${esc(p.title)}</td><td>${esc(c.title)}</td><td class="num" dir="ltr">${money(c.balance)} ${esc(p.unit)}</td><td>${qsign(q(c.balance)) > 0 ? 'به ' + esc(me()) + ' بدهکار است' : qsign(q(c.balance)) < 0 ? esc(me()) + ' به او بدهکار است' : 'تسویه'}</td></tr>`), `<tr class="total"><td>${esc(p.title)}</td><td>جمع</td><td class="num" dir="ltr">${money(p.balance)} ${esc(p.unit)}</td><td>${qsign(q(p.balance)) > 0 ? 'به ' + esc(me()) + ' بدهکار است' : qsign(q(p.balance)) < 0 ? esc(me()) + ' به او بدهکار است' : 'تسویه'}</td></tr>`]).join('')}</tbody></table></div><p class="muted">از حساب جاری اشخاص (۱۳۰۱)، با هر پرداخت، سهم و سند دستی‌ای که به آن شخص خورده است.</p>` : '<div class="empty">هنوز حساب شخصی باز نشده است.</div>';
}
function analyticReport() {
  const own = books.analytic.own.filter(r => r.unit === period.unit);
  const months = [...new Set(own.map(r => r.month))].sort();
  const groups = {};
  for (const r of own) { const g = groups[r.analytic] ||= {}; const a = g[r.account] ||= {name: r.accountName}; a[r.month] = qadd(a[r.month] || Q0, q(r.amount)); }
  const gross = Object.fromEntries(books.analytic.gross.filter(r => r.unit === period.unit).map(r => [r.analytic, r.amount]));
  return Object.keys(groups).length ? `<div class="table-scroll"><table><thead><tr><th>مرکز هزینه</th><th>حساب</th>${months.map(m => `<th dir="ltr">${esc(m)}</th>`).join('')}<th>جمع سهم ${esc(me())}</th></tr></thead><tbody>${Object.entries(groups).sort().map(([an, accounts]) => { let groupTotal = Q0; const rows = Object.entries(accounts).map(([code, a]) => { const t = months.reduce((n, m) => qadd(n, a[m] || Q0), Q0); groupTotal = qadd(groupTotal, t); return `<tr><td>${esc(an ? centreLabel(an) : 'بدون مرکز هزینه')}</td><td>${esc(code)} — ${esc(a.name)}</td>${months.map(m => `<td class="num" dir="ltr">${a[m] ? money(qtext(a[m])) : ''}</td>`).join('')}<td class="num" dir="ltr">${money(qtext(t))}</td></tr>`; }).join(''); return rows + `<tr class="total"><td>${esc(an ? centreLabel(an) : 'بدون مرکز هزینه')}</td><td>جمع${gross[an] ? ` <small>کل خریدهای این مرکز با سهم دیگران: ${money(gross[an])}</small>` : ''}</td>${months.map(() => '<td></td>').join('')}<td class="num" dir="ltr">${money(qtext(groupTotal))}</td></tr>`; }).join('')}</tbody></table></div><p class="muted">سهم خود ${esc(me())} از هزینه‌ها و درآمدها؛ «کل خریدها» تمام مبلغ پرداخت‌های همان مرکز است، هر کس که سهمش را بدهد.</p>` : '<div class="empty">هنوز هزینه‌ای به مرکز هزینه‌ای ثبت نشده است.</div>';
}
function cardReport() {
  const card = books.trial.rows.find(r => r.code === '2101');
  return books.statements.map(s => { const calc = cents(s.opening) + cents(s.net); return `<div class="report-note"><b>${esc(s.title)}</b><div class="facts">${fact('بدهی ابتدای دوره (بانک)', money(s.opening))}${fact('خالص ردیف‌ها', money(s.net))}${fact('ابتدا + ردیف‌ها', money(fromCents(calc)))}${fact('بدهی پایان دوره (بانک)', money(s.closing))}${fact('ثبت‌شده در دفتر', money(s.posted))}${fact('ثبت‌نشده', money(s.unposted))}</div><p>${calc === cents(s.closing) ? badge('ردیف‌های صورتحساب با جمع بانک می‌خواند', 'done') : badge('جمع ردیف‌ها با بانک نمی‌خواند', 'late')} ${s.counts.unposted ? badge(fa(s.counts.unposted) + ' ردیف ثبت‌نشده', 'late') : badge('همهٔ ردیف‌ها ثبت شده‌اند', 'done')}</p></div>`; }).join('') + `<p>ماندهٔ حساب ۲۱۰۱ در دفتر: <b dir="ltr">${money(card ? qtext(qsub(Q0, q(card.closing))) : '0.00')}</b> بدهی. ${card ? '' : 'هنوز سندی به کارت نخورده است.'}</p>`;
}
function checksReport() {
  return books.checks.length ? `<div class="table-scroll"><table><thead><tr><th>سند</th><th>چه باید روشن شود</th></tr></thead><tbody>${books.checks.map(c => `<tr><td>${c.number ? `<button class="text-button" data-bk="goto-voucher" data-ref="${esc(c.ref)}">${fa(c.number)}</button>` : `<span dir="ltr">${esc(c.ref)}</span>`}</td><td>${esc(c.what)}</td></tr>`).join('')}</tbody></table></div>` : '<div class="empty">موردی برای بررسی نیست.</div>';
}

// ---------------------------------------------------------------------------------------------- wiring
extraTabs.posting = {title: 'ثبت خریدهای کارت', render: renderPosting};
extraTabs.vouchers = {title: 'اسناد حسابداری', render: renderVouchers};
extraTabs.chart = {title: 'سرفصل حساب‌ها', render: renderChart};
extraTabs.finance = {title: 'گزارش‌های مالی', render: renderFinance};

document.addEventListener('click', e => {
  const b = e.target.closest('[data-bk]'); if (!b) return;
  if (!books || books.head !== data.head) {          // a payment corrected from the agreements page: read the books first
    if (b.dataset.bk === 'correct') { const ref = b.dataset.ref; loadBooks().then(() => books && openEdit(ref)); }
    if (!books) return;
  }
  const k = b.dataset.bk, lineKey = b.dataset.line && b.dataset.line.split('|');
  if (k === 'reload') { booksError = ''; loadBooks(); }
  else if (k === 'period') { for (const p of ['vp', 'rp']) if ($(p + '-from')) { period.from = $(p + '-from').value; period.to = $(p + '-to').value; period.unit = $(p + '-unit').value; } books.head = ''; render(); }
  else if (k === 'period-clear') { period.from = period.to = ''; books.head = ''; render(); }
  else if (k === 'post-one') openPostCard([lineKey]);
  else if (k === 'post-selected') openPostCard([...selectedLines].map(x => x.split('|')));
  else if (k === 'accept-suggested') openPostCard([...selectedLines].map(x => x.split('|')).filter(([s, l]) => cardLines().find(x => x.statement === s && x.line === l && x.suggested && x.state === 'unposted')), {suggested: true});
  else if (k === 'clear-selection') { selectedLines.clear(); render(); }
  else if (k === 'post-pay') openPostPay(b.dataset.ref);
  else if (k === 'correct') openEdit(b.dataset.ref);
  else if (k === 'delete') openDelete(b.dataset.ref);
  else if (k === 'dispute') openDispute(b.dataset.ref);
  else if (k === 'history') { const r = b.dataset.ref; fetchHistory(r).then(h => { h.shown = !h.shown; render(); }); }
  else if (k === 'reverse') openReverse(b.dataset.ref);
  else if (k === 'journal') openJournal();
  else if (k === 'opening') { const s = books.statements.find(x => x.id === b.dataset.statement); openJournal({date: '', memo: 'ماندهٔ بدهی ابتدای دورهٔ ' + s.title + ' (' + s.id + ')', unit: 'TRY', lines: [{account: '3101', debit: s.opening}, {account: '2101', credit: s.opening}]}); }
  else if (k === 'jl-add') { journalLines.push({}); $('jl-body').insertAdjacentHTML('beforeend', journalRowHTML({}, journalLines.length - 1)); }
  else if (k === 'jl-remove') { journalLines.splice(Number(b.dataset.n), 1); $('jl-body').innerHTML = journalLines.map(journalRowHTML).join(''); $('jl-totals').innerHTML = journalTotals(); }
  else if (k === 'toggle') { const r = b.dataset.ref; openVouchers.has(r) ? openVouchers.delete(r) : openVouchers.add(r); render(); }
  else if (k === 'goto-voucher') { tab = 'vouchers'; openVouchers.add(b.dataset.ref); voucherFilter.search = ''; render(); }
  else if (k === 'scheme') { chartScheme = b.dataset.scheme; render(); }
  else if (k === 'chart-edit') openChartRow(chartScheme, b.dataset.code);
  else if (k === 'chart-add') openChartRow(chartScheme, '', b.dataset.parent);
  else if (k === 'report') { reportTab = b.dataset.report; render(); }
  else if (k === 'ledger') { reportTab = 'ledger'; ledgerChoice = {code: b.dataset.code, person: ''}; render(); }
  else if (k === 'person-ledger') { tab = 'finance'; reportTab = 'ledger'; ledgerChoice = {code: '1301', person: b.dataset.person}; render(); }
});
document.addEventListener('change', e => {
  const t = e.target;
  if (t.dataset.line && t.type === 'checkbox') { t.checked ? selectedLines.add(t.dataset.line) : selectedLines.delete(t.dataset.line); render(); }
  else if (t.dataset.bkAll) { for (const l of lineScope()) { const key = l.statement + '|' + l.line; t.checked ? selectedLines.add(key) : selectedLines.delete(key); } render(); }
  else if (t.id && t.id.startsWith('pf-') && t.id !== 'pf-search') { postFilter[t.id.slice(3)] = t.value; render(); }
  else if (t.id && t.id.startsWith('vf-') && t.id !== 'vf-search') { voucherFilter[t.id.slice(3)] = t.value; render(); }
  else if (t.id === 'lg-code') { ledgerChoice = {code: t.value, person: ''}; render(); }
  else if (t.id === 'lg-person') { ledgerChoice.person = t.value; render(); }
  else if (t.id === 'post-sharing') { $('post-contract').value = t.value; $('shares-slot').innerHTML = t.value ? sharesEditor(t.value) : ''; }
  else if (t.dataset.bkToggle === 'reversed') { showReversed = t.checked; render(); }
  else if (t.id === 'post-replaces' && t.value) {
    const p = books.pays.find(x => x.ref === t.value); if (!p) return;
    if (p.accounts[0] && $('post-account')) $('post-account').value = p.accounts[0];
    const an = document.querySelector('#entry-form select[name=analytic]'); if (an && p.analytic[0]) an.value = p.analytic[0];
    $('post-sharing').value = p.contract || ''; $('post-contract').value = p.contract || '';
    $('shares-slot').innerHTML = p.contract ? sharesEditor(p.contract, Object.keys(p.bears).length ? p.bears : {[p.by]: '1'}) : '';
  }
  else if (t.dataset.jl !== undefined) { journalLines[Number(t.dataset.jl)][t.dataset.f] = t.value; if (t.dataset.f === 'account') { const sel = document.querySelector(`[data-jl="${t.dataset.jl}"][data-f="person"]`); sel.disabled = account(t.value)?.detail !== 'person'; if (sel.disabled) { sel.value = ''; journalLines[Number(t.dataset.jl)].person = ''; } } $('jl-totals').innerHTML = journalTotals(); }
});
document.addEventListener('input', e => {
  const t = e.target;
  if (t.id === 'pf-search') { postFilter.search = t.value; render(); const s = $('pf-search'); s.focus(); s.setSelectionRange(t.value.length, t.value.length); }
  else if (t.id === 'vf-search') { voucherFilter.search = t.value; render(); const s = $('vf-search'); s.focus(); s.setSelectionRange(t.value.length, t.value.length); }
  else if (t.dataset.jl !== undefined && ['debit', 'credit', 'memo'].includes(t.dataset.f)) { journalLines[Number(t.dataset.jl)][t.dataset.f] = t.value; $('jl-totals').innerHTML = journalTotals(); }
});

// The page's policy refuses inline `style` attributes; a layout that depends on the data is set here, through the DOM.
new MutationObserver(() => {
  for (const el of $('content').querySelectorAll('[data-gc],[data-gr],[data-rows],[data-pad]')) {
    if (el.dataset.gc) el.style.gridColumn = el.dataset.gc;
    if (el.dataset.gr) el.style.gridRow = el.dataset.gr;
    if (el.dataset.rows) el.style.gridTemplateRows = el.dataset.rows;
    if (el.dataset.pad) el.style.paddingInlineStart = el.dataset.pad + 'px';
  }
}).observe($('content'), {childList: true});
