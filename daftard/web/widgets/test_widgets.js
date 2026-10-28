// node dashboard/widgets/test_widgets.js — the number and money widgets (widgets.js): exact, escaped, isolated.
const assert = require('assert');
const W = require('./widgets.js');
W.configure({currencies: [{code: 'TRY', digits: '2'}, {code: 'IRR', digits: '2'}, {code: 'JPY', digits: '0'}]});
const strip = s => String(s).replace(/<[^>]+>/g, '');
const n = (v, o) => strip(W.number.show(v, o));
// digits, grouping, sign: exact, as written
assert.strictEqual(n('26439'), '۲۶٬۴۳۹');
assert.strictEqual(n('-1950'), '−۱٬۹۵۰');
assert.strictEqual(n('260.5'), '۲۶۰٫۵');
assert.strictEqual(n('260.5', {places: 2}), '۲۶۰٫۵۰');
assert.strictEqual(n('1234567.89', {digits: 'latn'}), '1,234,567.89');
assert.strictEqual(n('0.12345'), '۰٫۱۲۳۴۵');                          // a share as written, never cut to 3 places
// fractions: the whole part, then numerator over denominator (the hidden slash keeps a copy readable)
assert.strictEqual(n('167797/6'), '۲۷٬۹۶۶ ۱⁄۶');
assert.strictEqual(n('9650/3'), '۳٬۲۱۶ ۲⁄۳');
assert.strictEqual(n('-2/3'), '−۲⁄۳');
assert.strictEqual(n('6/3'), '۲');
// a fraction that ends at the currency's places is those decimals: 3497/40 lira is not, 2/8 is
assert.strictEqual(n('1/4', {places: 2}), '۰٫۲۵');
assert.strictEqual(n('3497/40', {places: 2}), '۸۷ ۱۷⁄۴۰');
// the isolate: left to right, only number characters, labelled for a screen reader
const html = String(W.number.show('167797/6'));
assert.ok(html.startsWith('<bdi dir="ltr" class="w-num"'), html);
assert.ok(!/[؀-ۯۺ-ۿ]/.test(strip(html).replace(/[٫٬]/g, '')), 'no Persian letter inside a number');
assert.ok(html.includes('aria-label="۲۷٬۹۶۶ ۱/۶"'), html);
// money: the number widget at the currency's places, the label outside the isolate, an uneven amount flagged
const m = String(W.money.show('9650/3', 'TRY'));
assert.ok(m.includes('</bdi><span class="w-uneven"') && m.endsWith('<span class="w-unit">TRY</span></span>'), m);
assert.strictEqual(strip(W.money.show('260.5', 'TRY')), '۲۶۰٫۵۰ TRY');
assert.strictEqual(strip(W.money.show('-1950', 'TRY', {abs: true})), '۱٬۹۵۰٫۰۰ TRY');   // money at its currency's places, as accounts are kept
assert.strictEqual(strip(W.money.show('1500', 'JPY')), '۱٬۵۰۰ JPY');
assert.ok(W.money.uneven('9650/3', 'TRY') && !W.money.uneven('1/4', 'TRY') && W.money.negative('-2/3') && !W.money.negative('0'));
// escaping: a value is text, never markup; a widget's output is not escaped twice
assert.strictEqual(String(W.h`<b>${'<i>x</i> & "y"'}</b>`), '<b>&lt;i&gt;x&lt;/i&gt; &amp; &quot;y&quot;</b>');
assert.strictEqual(String(W.h`<p>${W.number.show('5')}</p>`).includes('&lt;bdi'), false);
assert.strictEqual(String(W.number.show('<script>')), '<bdi class="w-num w-bad">&lt;script&gt;</bdi>');
// a count for running text: its characters alone
assert.strictEqual(W.number.plain(10), '۱۰');
assert.strictEqual(W.number.plain('9650/3'), '۳٬۲۱۶\u202f۲/۳');
assert.strictEqual(W.number.plain('x'), null);
// plain text: isolated, so it cannot reorder the sentence it goes into
assert.strictEqual(W.number.text('-1950'), '\u2066−۱٬۹۵۰\u2069');
assert.strictEqual(W.money.text('9650/3', 'TRY'), '\u2066۳٬۲۱۶ ۲/۳\u2069 TRY');
assert.strictEqual(W.isolated('abc\u202Edef'), '\u2068abc\u202Edef\u2069');
// taking in what a person typed: exactly, or a refusal
const take = (s, o) => W.number.take(s, o);
assert.deepStrictEqual(take('۱٬۲۵۰٫۵'), {value: '1250.5'});
assert.deepStrictEqual(take('1,250.50', {places: 2}), {value: '1250.50'});
assert.deepStrictEqual(take('−۵۰'), {value: '-50'});
assert.ok(take('12,50').error && take('1/3').error && take('0012').error && take('1.234', {places: 2}).error);
assert.ok(take('\u202E5').value === '5', 'a bidi control typed or pasted is not part of a number');
assert.deepStrictEqual(W.money.take('100.255', 'TRY').error !== undefined, true);
console.log('PASS: number and money widgets — exact digits, fractions, isolation, escaping, plain text, input.');
