// node test/widgets.test.mjs — the widgets (assets/view/lib/widgets): exact, isolated, escaped, and every language's own
// digits, separators, calendar and words from CLDR, none privileged. Run by test/widgets.py.
import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
const lib = new URL('../assets/view/lib/widgets/', import.meta.url);
const { h, escape, isolated, mount } = await import(new URL('safe.js', lib));
const { configure, settings, me } = await import(new URL('settings.js', lib));
const L = await import(new URL('locale.js', lib));
const number = await import(new URL('number.js', lib));
const money = await import(new URL('money.js', lib));
const moment = await import(new URL('moment.js', lib));
const text = await import(new URL('text.js', lib));
const name = await import(new URL('name.js', lib));
const choice = await import(new URL('choice.js', lib));
const being = await import(new URL('being.js', lib));
const exact = await import(new URL('exact.js', lib));
const strip = s => String(s).replace(/<[^>]+>/g, '');
let n = 0;
const ok = (what, f) => { f(); n++; };

ok('nothing assumed: no language, calendar, zone or name stands in for one not given', () => {
  assert.deepEqual([settings.lang, settings.calendar, settings.zone, settings.title, me()], ['', '', '', '', '']);
});
ok('no widget keeps a table of digits or a language\'s words: they are CLDR\'s, through Intl', () => {
  for (const f of readdirSync(lib).filter(f => f.endsWith('.js') && f !== 'locale.js')) {
    const src = readFileSync(new URL(f, lib), 'utf8');
    assert.ok(!/[۰-۹٠-٩]/.test(src), `${f} holds Arabic-script digits`);
    assert.ok(!/=== 'fa'|persian'/.test(src), `${f} names one language or calendar`);
  }
});
// safe templates
ok('h escapes every value but a widget\'s own', () => {
  assert.equal(String(h`<b>${'<i>x</i> & "y"'}</b>`), '<b>&lt;i&gt;x&lt;/i&gt; &amp; &quot;y&quot;</b>');
  assert.equal(String(h`<p>${[h`<i>a</i>`, 'b<']}</p>`), '<p><i>a</i>b&lt;</p>');
  assert.equal(String(h`<p>${null}${undefined}${false}</p>`), '<p></p>');
  assert.equal(isolated('a'), '\u2068a\u2069');
  assert.equal(escape("'"), '&#39;');
});
ok('mount sets a computed grid position through the CSSOM, and only a grid-line expression', () => {
  const cell = {dataset: {gc: '3', gr: '5 / span 4'}, style: {}}, bad = {dataset: {gr: 'red; background:url(x)'}, style: {}};
  const root = {innerHTML: '', querySelectorAll: () => [cell, bad]};
  mount(root, h`<div data-gc="3"></div>`);
  assert.deepEqual([root.innerHTML, cell.style.gridColumn, cell.style.gridRow, bad.style.gridRow], ['<div data-gc="3"></div>', '3', '5 / span 4', undefined]);
  assert.throws(() => mount(root, '<b>x</b>'), TypeError);
});

// ---- English: the law's written forms, Latin digits
ok('en: a number grouped, exact, a fraction as it is', () => {
  assert.equal(strip(number.show('-1950', {lang: 'en'})), '−1,950');
  assert.equal(strip(number.show('1234567.89', {lang: 'en'})), '1,234,567.89');
  assert.equal(number.plain('9650/3', {lang: 'en'}), '3,216 2/3');
  assert.equal(strip(number.show('1/4', {places: 2, lang: 'en'})), '0.25');
  assert.equal(String(number.show('<x>')), '<bdi class="w-num w-bad">&lt;x&gt;</bdi>');
});
ok('en: what is typed is taken exactly, or refused in English', () => {
  assert.deepEqual(number.take('1,250.5', {lang: 'en'}), {value: '1250.5'});
  assert.ok(number.take('12,50', {lang: 'en'}).error.includes('thousands'));
  assert.ok(number.take('0012', {lang: 'en'}).error && number.take('1/3', {lang: 'en'}).error);
  assert.equal(number.take('1.234', {lang: 'en', places: 2}).error, 'At most 2 decimal places.');
});
ok('en: a day in the Gregorian calendar is the written day itself', () => {
  assert.equal(strip(moment.show('2026-10-08', {lang: 'en'})), '2026-10-08');
  assert.equal(strip(moment.show('2026-10-08 14:30+03:00', {lang: 'en'})), '2026-10-08 14:30');
  assert.deepEqual(moment.take('2026-10-08', {lang: 'en'}), {value: '2026-10-08'});
  assert.ok(moment.take('2026-02-30', {lang: 'en'}).error);
});

// ---- Turkish and German: the separators the other way round
ok('tr, de: a dot groups and a comma is the decimal', () => {
  assert.equal(strip(number.show('1234567.5', {lang: 'tr'})), '1.234.567,5');
  assert.deepEqual(number.take('1.234,5', {lang: 'de'}), {value: '1234.5'});
  assert.deepEqual(number.take('2,5', {lang: 'tr'}), {value: '2.5'});
  assert.ok(number.take('1,234.5', {lang: 'de'}).error);
  assert.equal(strip(money.show('260.5', 'TRY', {lang: 'tr', places: 2})), '260,50 TRY');
});

// ---- Persian: CLDR's own digits, separators and calendar for `fa`
configure({garden: {gardener: 'g1', me: 'g1', lang: 'fa'}, asOf: '2026-10-08',
           currencies: [{code: 'TRY', digits: '2'}, {code: 'JPY', digits: '0'}]});
ok('fa: Persian digits and separators, from CLDR', () => {
  assert.equal(strip(number.show('-1950')), '−۱٬۹۵۰');
  assert.equal(number.plain('9650/3'), '۳٬۲۱۶ ۲/۳');
  assert.deepEqual(number.take('۱٬۲۵۰٫۵'), {value: '1250.5'});
  assert.equal(strip(number.show('1234567.89', {digits: 'latn'})), '1,234,567.89');   // CLDR's fa, in Latin digits
});
ok('fa: money at the currency\'s places, an uneven amount said in Persian', () => {
  assert.equal(strip(money.show('260.5', 'TRY')), '۲۶۰٫۵۰ TRY');
  assert.equal(strip(money.show('1500', 'JPY')), '۱٬۵۰۰ JPY');
  assert.ok(String(money.show('9650/3', 'TRY')).includes('w-uneven') && String(money.show('9650/3', 'TRY')).includes('بند'));
  assert.ok(money.uneven('9650/3', 'TRY') && money.negative('-2/3') && money.sign('0.00') === 0 && money.sign('-1') === -1);
  assert.ok(money.take('100.255', 'TRY').error);
});
ok('fa: the Persian calendar, CLDR\'s default for fa; today in Persian words', () => {
  assert.equal(strip(moment.show('2026-10-08')), '۱۴۰۵/۰۷/۱۶');
  assert.equal(strip(moment.show('2026-10-08', {relative: true})), 'امروز');
  assert.ok(String(moment.show('2026-10-08')).includes('datetime="2026-10-08"') && String(moment.show('2026-10-08')).includes('title="2026-10-08"'));
  assert.ok(strip(moment.show('2026-10-08', {style: 'long'})).includes('مهر'));
  assert.deepEqual(moment.take('۱۴۰۵/۰۷/۱۶'), {value: '2026-10-08'});
  assert.deepEqual(moment.take('2026-10-08'), {value: '2026-10-08'});
  assert.ok(moment.take('1404/12/30').error && moment.take('x').error);
  assert.deepEqual(moment.take('1403/12/30'), {value: '2025-03-20'});
  assert.deepEqual(moment.takeTime('۸:۳۰'), {value: '08:30'});
  assert.equal(moment.take('1404/12/30').error, 'چنین روزی در این تقویم نیست.');
});

// ---- the other calendars CLDR holds: a day there and back
ok('every calendar of CLDR in its current era: a day shown there is taken back as the same written day', () => {
  for (const cal of ['islamic-umalqura', 'islamic-civil', 'indian', 'buddhist', 'japanese', 'ethiopic', 'coptic', 'roc', 'persian']) {
    const p = moment.toCalendar('2026-10-08', cal);
    assert.equal(moment.fromCalendar(cal, p.y, p.m, p.d), '2026-10-08', cal);
  }
  assert.equal(moment.fromCalendar('islamic-umalqura', 1448, 13, 1), null);
  assert.ok(strip(moment.show('2026-10-08', {calendar: 'hebrew', lang: 'en', style: 'long'})).includes('5787'));
  assert.equal(moment.take('5787/1/27', {calendar: 'hebrew', lang: 'en'}).error,
               'In this calendar a day is taken as the law writes it: 2026-10-08.');
  assert.deepEqual(moment.take('2026-10-08', {calendar: 'hebrew', lang: 'en'}), {value: '2026-10-08'});
});
ok('a reader of Arabic, of Sorani, of Hebrew: CLDR\'s digits for each, and its direction', () => {
  assert.equal(L.digitsOf({lang: 'ckb'}), 'arab');
  assert.equal(strip(number.show('12', {lang: 'ckb'})), '١٢');
  assert.deepEqual(number.take('١٢', {lang: 'en'}), {value: '12'});
  assert.equal(L.dirOf('he'), 'rtl');
  assert.equal(L.dirOf('tr'), 'ltr');
});

// ---- text, name, choice, being, exact
ok('text: isolated, escaped, its controls revealed on request; required said in the reader\'s language', () => {
  assert.equal(String(text.show('a<b')), '<bdi dir="auto" class="w-text">a&lt;b</bdi>');
  assert.equal(strip(text.show('ab\u202Ecd', {inspect: true})), 'ab⟨RLO⟩cd');
  assert.equal(String(text.show('x', {lang: 'fa'})), '<bdi dir="rtl" class="w-text" lang="fa">x</bdi>');
  assert.deepEqual(text.take(' سایر '), {value: 'سایر'});
  assert.equal(text.take('', {required: true, lang: 'en'}).error, 'This is required.');
});
ok('name: left to right, digits taken as written in any script', () => {
  assert.ok(String(name.show('+90 532 123 45 67', {kind: 'phone'})).startsWith('<bdi dir="ltr"'));
  assert.deepEqual(name.take('۰۵۳۲ ۱۲۳ ۴۵ ۶۷', {kind: 'phone'}), {value: '0532 123 45 67'});
  assert.ok(name.take('a@b', {kind: 'email'}).error);
});
ok('choice and being', () => {
  assert.equal(strip(choice.show('yoga', {yoga: 'Yoga', work: 'Work'})), 'Yoga');
  assert.ok(choice.take('x', {a: 'A'}).error); assert.deepEqual(choice.take('a', {a: 'A'}), {value: 'a'});
  const accounts = [{value: '6', label: 'Expenses', disabled: true}, {value: '6201', label: 'Clothing'}];
  assert.ok(String(choice.edit('account', '', accounts, {required: true, placeholder: 'Choose'})).includes('<option value="6" disabled>'));
  assert.ok(choice.take('6', accounts).error); assert.deepEqual(choice.take('6201', accounts), {value: '6201'});
  assert.ok(String(being.show('p-1', 'Sara', {action: 'open'})).includes('data-id="p-1"'));
});
ok('exact: sums of written amounts, never a float, n/d where they do not end', () => {
  assert.equal(exact.text(exact.sum(['146.67', '0.33', '-47'])), '100.00');
  assert.equal(exact.text(exact.sum(['0.1', '0.2'])), '0.30');
  assert.equal(exact.text(exact.add(exact.of('10'), exact.of('1/3'))), '31/3');
  assert.equal(exact.text(exact.of('-0.5'), 0), '-1/2');
  assert.deepEqual(exact.of('−3'), [-3n, 1n]);
  assert.equal(exact.of('1/0'), null);
});
console.log(`PASS: widgets — ${n} groups of checks: safe, settings, locale, number, money, moment in ten calendars, text, name, choice, being, exact.`);
