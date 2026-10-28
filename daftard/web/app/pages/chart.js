// The chart: the books' accounts (group → general → subsidiary; vouchers post only to a subsidiary), the cost centres
// (plan → account), and the persons, whose detail accounts sit under 1301. An account that was used is closed, never
// removed.
import { h } from '/toolbox/safe.js';
import * as text from '/toolbox/text.js';
import { badge } from '../common.js';
import { state, load, LEVELS, TYPES, beanTitle, amount, bare, owes, openChartRow } from '../books.js';

const SCHEMES = [['account', 'حساب‌های دفتر'], ['analytic', 'مراکز هزینه'], ['details', 'اشخاص (تفصیلی)']];
const switcher = () => h`<div class="header-actions">${SCHEMES.map(([k, n]) => h`<button class="${state.scheme === k ? 'primary' : 'secondary'}" data-action="bk-scheme" data-scheme="${k}">${n}</button>`)}</div>`;
// the depth a row is drawn at, as a class (the page's policy refuses inline styles)
const depth = (scheme, r) => 'pad-' + Math.min(scheme === 'account' ? r.path.length - 1 : r.level === 'plan' ? 0 : 1, 5);

function rows(B, scheme) {
  const list = scheme === 'account'
    ? B.chart.accounts.slice().sort((a, b) => a.path.join('.').localeCompare(b.path.join('.')))
    : B.chart.analytic.slice().sort((a, b) => (a.plan + (a.level === 'plan' ? '' : '.' + a.code)).localeCompare(b.plan + (b.level === 'plan' ? '' : '.' + b.code)));
  const closing = Object.fromEntries(B.trial.rows.map(r => [r.code, r.closing]));
  return h`<section class="panel"><div class="panel-head"><div><h2>سرفصل حساب‌ها</h2><p>گروه ← کل ← معین؛ اسناد فقط به حساب معین می‌خورند. حساب‌های تفصیلی، خود اشخاص و توافق‌ها و مراکز هزینه‌اند. حسابِ به‌کاررفته را می‌توان بست، نه پاک کرد.</p></div>${switcher()}</div>
    <div class="table-scroll"><table class="w-table"><thead><tr><th>کد</th><th>نام</th><th>سطح</th>${scheme === 'account' ? h`<th>نوع</th><th class="num">مانده</th>` : ''}<th>پیوندها</th><th>وضعیت</th><th></th></tr></thead><tbody>
    ${list.map(r => h`<tr class="level-${r.level}"><td class="code"><bdi dir="ltr">${r.code}</bdi></td><td class="${depth(scheme, r)}">${r.name}${r.detail === 'person' ? h`<small>تفصیلی: شخص</small>` : ''}</td>
      <td>${LEVELS[r.level] || r.level}</td>${scheme === 'account' ? h`<td>${TYPES[r.type] || ''}</td><td class="num">${closing[r.code] ? bare(closing[r.code], B.unit) : ''}</td>` : ''}
      <td>${(r.links || []).map(b => h`<small>${text.show(beanTitle(b))}</small>`)}</td><td>${r.status === 'closed' ? badge('بسته', 'late') : r.used ? badge('به‌کاررفته', 'done') : ''}</td>
      <td class="actions"><button class="text-button" data-action="bk-chart-edit" data-code="${r.code}">ویرایش</button>${r.postable ? '' : h`<button class="text-button" data-action="bk-chart-add" data-parent="${r.code}">＋ زیرحساب</button>`}</td></tr>`)}</tbody></table></div>
    <p><button class="secondary" data-action="bk-chart-add" data-parent="">＋ ${scheme === 'account' ? 'گروه حساب تازه' : 'طرح تحلیلی تازه'}</button></p></section>`;
}

function details(B) {
  return h`<section class="panel"><div class="panel-head"><div><h2>اشخاص — حساب‌های تفصیلی</h2><p>هر شخص حساب تفصیلی خودش را زیر «حساب جاری اشخاص» (۱۳۰۱) دارد: سهم‌هایی که بر عهده دارد و پرداخت‌هایی که کرده، به تفکیک توافق. شخص تازه از پرونده‌اش در دفتر ساخته می‌شود و با توافقی که در آن طرف است اینجا می‌آید.</p></div>${switcher()}</div>
    <div class="table-scroll"><table class="w-table"><thead><tr><th>شخص</th><th>توافق‌ها</th><th>مانده</th><th></th></tr></thead><tbody>${B.details.map(d =>
      h`<tr><td><b>${d.title}</b>${d.known ? '' : h`<small>هنوز در دفتر ثبت نشده</small>`}</td><td>${d.contracts.length ? d.contracts.map(c => h`<small>${text.show(c.title)}</small>`) : '—'}</td>
        <td>${d.balances.length ? d.balances.map(b => h`<span class="num">${amount(b.balance, b.unit)}</span><small>${owes(b.balance)}</small>`) : '—'}</td>
        <td class="actions">${d.balances.length ? h`<button class="text-button" data-action="bk-person-ledger" data-person="${d.id}">دفتر تفصیلی</button>` : ''}</td></tr>`)}</tbody></table></div></section>`;
}

export default {
  id: 'chart', nav: 'سرفصل حساب‌ها', title: 'سرفصل حساب‌ها',
  async render(ctx) {
    const B = await load(ctx);
    return state.scheme === 'details' ? details(B) : rows(B, state.scheme);
  },
  actions: {
    'bk-scheme': (el, ctx) => { state.scheme = el.dataset.scheme; return ctx.rerender(); },
    'bk-chart-edit': (el, ctx) => openChartRow(ctx, state.scheme, el.dataset.code),
    'bk-chart-add': (el, ctx) => openChartRow(ctx, state.scheme, '', el.dataset.parent),
  },
};
