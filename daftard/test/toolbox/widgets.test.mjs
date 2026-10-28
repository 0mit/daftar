// node test/toolbox/widgets.test.mjs — every value widget: exact, isolated, escaped.
import assert from 'node:assert/strict';
import { h, Safe, escape, isolated, mount } from '../../web/toolbox/safe.js';
import { configure, settings, me } from '../../web/toolbox/settings.js';
import * as number from '../../web/toolbox/number.js';
import * as money from '../../web/toolbox/money.js';
import * as moment from '../../web/toolbox/moment.js';
import * as text from '../../web/toolbox/text.js';
import * as name from '../../web/toolbox/name.js';
import * as choice from '../../web/toolbox/choice.js';
import * as being from '../../web/toolbox/being.js';
import { table } from '../../web/toolbox/table.js';
import * as exact from '../../web/toolbox/exact.js';
import { form } from '../../web/toolbox/form.js';

configure({garden: {gardener: 'g1', me: 'من', title: 'دفتر', lang: 'fa'}, asOf: '2026-10-08',
           currencies: [{code: 'TRY', digits: '2'}, {code: 'JPY', digits: '0'}]});
const strip = s => String(s).replace(/<[^>]+>/g, '');
// safe templates
assert.equal(String(h`<b>${'<i>x</i> & "y"'}</b>`), '<b>&lt;i&gt;x&lt;/i&gt; &amp; &quot;y&quot;</b>');
assert.equal(String(h`<p>${[h`<i>a</i>`, 'b<']}</p>`), '<p><i>a</i>b&lt;</p>');
assert.equal(String(h`<p>${null}${undefined}${false}</p>`), '<p></p>');
assert.equal(isolated('a'), '\u2068a\u2069');
// settings
assert.equal(me(), 'من'); assert.equal(settings.calendar, 'persian'); assert.equal(settings.places.TRY, 2);
// number
assert.equal(strip(number.show('-1950')), '−۱٬۹۵۰');
assert.equal(strip(number.show('167797/6')), '۲۷٬۹۶۶ ۱⁄۶');
assert.equal(strip(number.show('1/4', {places: 2})), '۰٫۲۵');
assert.equal(strip(number.show('1234567.89', {digits: 'latn'})), '1,234,567.89');
assert.equal(number.plain('9650/3'), '۳٬۲۱۶ ۲/۳');
assert.equal(String(number.show('<x>')), '<bdi class="w-num w-bad">&lt;x&gt;</bdi>');
assert.deepEqual(number.take('۱٬۲۵۰٫۵'), {value: '1250.5'});
assert.ok(number.take('12,50').error && number.take('0012').error && number.take('1/3').error);
// money
assert.equal(strip(money.show('260.5', 'TRY')), '۲۶۰٫۵۰ TRY');
assert.equal(strip(money.show('1500', 'JPY')), '۱٬۵۰۰ JPY');
assert.ok(String(money.show('9650/3', 'TRY')).includes('w-uneven'));
assert.ok(money.uneven('9650/3', 'TRY') && money.negative('-2/3') && money.sign('0.00') === 0 && money.sign('-1') === -1);
assert.ok(money.take('100.255', 'TRY').error);
// moment: the reader's calendar, written as the garden writes a day
assert.equal(strip(moment.show('2026-10-08')), '۱۴۰۵/۰۷/۱۶');
assert.equal(strip(moment.show('2026-10-08', {relative: true})), 'امروز');
assert.equal(strip(moment.show('2026-10-08', {calendar: 'gregory', lang: 'en'})), '2026-10-08');
assert.ok(String(moment.show('2026-10-08')).includes('datetime="2026-10-08"'));
assert.ok(strip(moment.show('2026-10-08', {style: 'long'})).includes('مهر'));
assert.equal(strip(moment.show('2026-10-08 14:30+03:00')), '۱۴۰۵/۰۷/۱۶ ۱۴:۳۰');
assert.deepEqual(moment.take('۱۴۰۵/۰۷/۱۶'), {value: '2026-10-08'});
assert.deepEqual(moment.take('2026-10-08'), {value: '2026-10-08'});
assert.ok(moment.take('1404/12/30').error && moment.take('2026-02-30').error && moment.take('x').error);
assert.deepEqual(moment.takeTime('۸:۳۰'), {value: '08:30'});
// text: isolated, escaped, hidden controls revealed on request
assert.equal(String(text.show('a<b')), '<bdi dir="auto" class="w-text">a&lt;b</bdi>');
assert.equal(strip(text.show('ab\u202Ecd', {inspect: true})), 'ab⟨RLO⟩cd');
assert.equal(strip(text.show('')), '—');
// suggestions: offered, escaped, and anything else may still be written
assert.equal(String(text.edit('category', 'خانه', {suggest: ['خانه', 'a"<b']})), '<input class="w-input w-text-input" name="category" dir="auto" maxlength="500" value="خانه" list="w-suggest-category"><datalist id="w-suggest-category"><option value="خانه"></option><option value="a&quot;&lt;b"></option></datalist>');
assert.equal(String(text.edit('what', '')), '<input class="w-input w-text-input" name="what" dir="auto" maxlength="500" value="">');
assert.deepEqual(text.take(' سایر چیز '), {value: 'سایر چیز'});
// mount sets a computed grid position through the CSSOM (no style attribute), and only a grid-line expression
{
  const cell = {dataset: {gc: '3', gr: '5 / span 4'}, style: {}}, bad = {dataset: {gr: 'red; background:url(x)'}, style: {}};
  const grid = {dataset: {rows: 'auto auto repeat(68,11px)'}, style: {}};
  const root = {innerHTML: '', querySelectorAll: () => [cell, bad, grid]};
  mount(root, h`<div data-gc="3"></div>`);
  assert.equal(root.innerHTML, '<div data-gc="3"></div>');
  assert.deepEqual([cell.style.gridColumn, cell.style.gridRow, grid.style.gridTemplateRows, bad.style.gridRow], ['3', '5 / span 4', 'auto auto repeat(68,11px)', undefined]);
  assert.throws(() => mount(root, '<b>x</b>'), TypeError);
}
assert.equal(String(text.show('Upstream <b>\nnext', {block: true, lines: true})), '<div dir="auto" class="w-text w-lines w-block">Upstream &lt;b&gt;\nnext</div>');
assert.deepEqual(text.take('  x  \n y \n', {lines: true}), {value: 'x\n y'});
// name: left to right, digits as written
assert.ok(String(name.show('+90 532 123 45 67', {kind: 'phone'})).startsWith('<bdi dir="ltr"'));
assert.deepEqual(name.take('۰۵۳۲ ۱۲۳ ۴۵ ۶۷', {kind: 'phone'}), {value: '0532 123 45 67'});
assert.ok(name.take('a@b', {kind: 'email'}).error);
// choice and being
assert.equal(strip(choice.show('yoga', {yoga: 'یوگا', work: 'کار'})), 'یوگا');
assert.ok(choice.take('x', {a: 'A'}).error); assert.deepEqual(choice.take('a', {a: 'A'}), {value: 'a'});
assert.ok(String(choice.edit('c', 'a', {a: 'A', b: 'B'})).includes('<option value="a" selected>A</option>'));
assert.ok(String(being.show('p-1', 'Sara', {action: 'open'})).includes('data-id="p-1"'));
// table: cells are widgets, sortable columns carry their key
const t = String(table({columns: [{title: 'مبلغ', cell: r => money.show(r.a, 'TRY'), sort: r => r.a, align: 'num'}], rows: [{a: '5'}, {a: '<x>'}]}));
assert.ok(t.includes('data-sort-col="0"') && t.includes('data-v="&lt;x&gt;"') && t.includes('w-money'));
// choice: a disabled row (a heading) is shown and never taken; a placeholder asks even when the choice is required
const accounts = [{value: '6', label: 'هزینه‌ها', disabled: true}, {value: '6201', label: 'پوشاک'}];
const sel = String(choice.edit('account', '', accounts, {required: true, placeholder: 'انتخاب حساب'}));
assert.ok(sel.includes('<option value="">انتخاب حساب</option>') && sel.includes('<option value="6" disabled>'));
assert.ok(!String(choice.edit('account', '', accounts, {required: true})).includes('<option value="">'));
assert.ok(choice.take('6', accounts).error); assert.deepEqual(choice.take('6201', accounts), {value: '6201'});
assert.ok(choice.take('', accounts, {required: true}).error);
assert.ok(String(form([{name: 'a', label: 'حساب', type: 'choice', options: accounts, required: true, placeholder: 'انتخاب'}])).includes('<option value="">انتخاب</option>'));
// moment.edit: an empty field may say what its emptiness means
assert.ok(String(moment.edit('from', '', {placeholder: 'آغاز'})).includes('placeholder="آغاز"'));
// exact: sums of written amounts, never a float, n/d where they do not end
assert.equal(exact.text(exact.sum(['146.67', '0.33', '-47'])), '100.00');
assert.equal(exact.text(exact.sum(['9650/3', '19300/3'])), '9650.00');
assert.equal(exact.text(exact.sum(['0.1', '0.2'])), '0.30');
assert.equal(exact.text(exact.add(exact.of('10'), exact.of('1/3'))), '31/3');
assert.equal(exact.text(exact.sub(exact.ZERO, exact.of('88970/3'))), '-88970/3');
assert.equal(exact.text(exact.of('-0.5'), 0), '-1/2');
assert.equal(exact.text(exact.of('1234.5'), 2), '1234.50');
assert.equal(exact.of('abc'), null); assert.equal(exact.of('1/0'), null); assert.deepEqual(exact.of('−3'), [-3n, 1n]); assert.equal(exact.sign(exact.of('−3')), -1);
assert.ok(exact.eq(exact.of('2/4'), exact.of('0.5'))); assert.equal(exact.sign(exact.ZERO), 0);
console.log('PASS: toolbox widgets — safe templates, settings, number, money, moment, text, name, choice, being, table, exact.');
