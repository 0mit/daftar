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
// ---- a repetition and a form's value, drawn by their entries (recurrence.js, form.js): the systems and the units of a
// length of time are the law's, as a host sends them; the reader's calendar, digits and words are theirs
const recurrence = await import(new URL('recurrence.js', lib));
const form = await import(new URL('form.js', lib));
const SYSTEMS = [{system: 'gregorian-civil', calendar: 'gregory', prefix: '', week: false, levels: ['year', 'month', 'day']},
  {system: 'iso-week', calendar: 'iso8601', prefix: '', week: true, levels: ['year', 'week', 'day']},
  {system: 'persian-calendar', calendar: 'persian', prefix: 'persian:', week: false, levels: ['year', 'month', 'day']}];
configure({systems: SYSTEMS, durations: [{unit: 'min', name: 'minute'}, {unit: 'h', name: 'hour'}, {unit: 'a_j', name: 'julian-year'}]});
const weekly = {of: 'time', in: 'iso-week', each: 'week', at: ['2', '7'], from: '2026-W40-7', lasts: {of: 'time', measure: {count: '150', unit: 'min'}}};
ok('recurrence: implements the values tree\'s recurrence, and says one in the reader\'s words, calendar and digits', () => {
  assert.equal(recurrence.implements, 'recurrence');
  const en = recurrence.text(weekly, {lang: 'en'}), fa = recurrence.text(weekly, {lang: 'fa'});
  assert.ok(/^each week on Tuesday and Sunday|^each week on Sunday and Tuesday/.test(en) && en.includes('150 minutes'), en);
  assert.ok(fa.startsWith('هر هفته') && fa.includes('۱۵۰') && !/[0-9]/.test(fa.replace(/\u2068|\u2069/g, '')), fa);
  assert.ok(recurrence.text({of: 'time', in: 'gregorian-civil', each: 'month', at: '1', times: '6'}, {lang: 'en'}).includes('6 times'));
});
ok('recurrence: taken back as the law writes it — untouched fields give the bean\'s own value, places in the system\'s order', () => {
  const back = recurrence.take({each: 'week', at: ['7', '2'], from: '2026-10-04', in: 'iso-week', 'lasts.count': '۱۵۰', 'lasts.unit': 'min',
    keep: JSON.stringify({of: 'time'})}, {lang: 'fa'});
  assert.deepEqual(back, {value: weekly});
  assert.deepEqual(recurrence.take({each: 'month', at: '۱۵', from: '۱۴۰۵/۰۷/۱۲'}, {lang: 'fa', calendar: 'persian'}),
    {value: {of: 'time', in: 'persian-calendar', each: 'month', at: '15', from: 'persian:1405-07-12'}});
  assert.equal(recurrence.dayOf('persian:1405-07-12', 'persian-calendar'), '2026-10-04');
  assert.equal(recurrence.written('2026-10-04', 'iso-week'), '2026-W40-7');
  assert.ok(recurrence.take({each: 'week', times: 'six'}, {lang: 'en'}).error);
  assert.ok(recurrence.take({each: 'week', 'lasts.count': '150'}, {lang: 'en'}).error, 'a length needs its unit');
  assert.deepEqual(recurrence.take({}, {lang: 'en'}), {value: ''});
});
ok('recurrence: a place with a time of day is shown with it, kept in its field as written, and taken back whole', () => {
  const office = {of: 'time', in: 'iso-week', each: 'week', at: ['1T08:30', '5T17:45']};
  const en = recurrence.text(office, {lang: 'en'});
  assert.ok(/Monday 08:30/.test(en) && /Friday 17:45/.test(en), en);
  const html = String(recurrence.edit('w', office, {lang: 'en'}));
  assert.ok(html.includes('value="1T08:30, 5T17:45"') && !html.includes('type="checkbox"'),
    'a day of the week with its time is no box to tick: the field holds it as written, so a save keeps it');
  assert.deepEqual(recurrence.take({each: 'week', at: '5T17:45, 1T08:30', in: 'iso-week', keep: JSON.stringify({of: 'time'})},
    {lang: 'en'}), {value: office});
  assert.ok(recurrence.take({each: 'week', at: '1T8:30', in: 'iso-week'}, {lang: 'en'}).error, 'a time of day is hh:mm');
});
ok('recurrence: offers only the units of a length of time a language names (CLDR\'s), never a deep-time unit', () => {
  assert.deepEqual(recurrence.durations({lang: 'fa'}).map(d => d.unit), ['min', 'h']);
});
ok('form: a clause drawn by its entries — a day, a repetition, a length, a state — and taken back as the law writes it', () => {
  const clause = {name: 'clause', attrs: {due: {value: 'moment'}, every: {value: 'recurrence'}, notice: {value: 'duration'},
    state: {value: 'choice', rows: ['in-force', 'met']}, when: {value: 'form', attrs: {said: {value: 'text'}}}}};
  const html = String(form.edit('c', {due: '2026-10-01'}, clause, {lang: 'en'}));
  assert.ok(html.includes('name="c.due"') && html.includes('<details class="w-form-more">'), 'what the value holds drawn, the rest under more');
  assert.deepEqual(form.take({due: '1405/07/09', 'every.each': 'month', 'every.at': '1', 'every.times': '6', state: 'met',
    'notice.count': '3', 'notice.unit': 'd'}, clause, {lang: 'fa', calendar: 'persian'}),
    {value: {due: '2026-10-01', every: {of: 'time', in: 'persian-calendar', each: 'month', at: '1', times: '6'},
             notice: {count: '3', unit: 'd'}, state: 'met'}});
  assert.deepEqual(form.take({keep: JSON.stringify({when: {said: 'kept as written'}})}, clause, {lang: 'en'}),
    {value: {when: {said: 'kept as written'}}}, 'what the form does not draw is kept, never dropped');
  assert.equal(form.take({state: 'gone'}, clause, {lang: 'en'}).at, 'state');
});
// DIRECTION, solved once (core/law/profiles.yaml `orientations`): direction.js is a classic script — the view's page and the
// site load it as one — so it is run here in a page of its own: a document whose <html dir> is ltr or rtl, with or without
// the law's rows in <script id="orientations">.
import vm from 'node:vm';
const dirSrc = readFileSync(new URL('direction.js', lib), 'utf8');
const page = (dir, rows) => {
  const doc = { documentElement: { getAttribute: k => (k === 'dir' ? dir : null) },
                getElementById: id => (id === 'orientations' && rows ? { textContent: JSON.stringify(rows) } : null) };
  const win = { document: doc };
  vm.runInNewContext(dirSrc, { window: win, document: doc });
  const D = win.daftarDirection, plain = f => (...a) => JSON.parse(JSON.stringify(f(...a)) ?? 'null');   // out of its own realm
  return Object.fromEntries(Object.entries(D).map(([k, v]) => [k, typeof v === 'function' ? plain(v) : v]));
};
const key = k => ({ key: k });
ok('direction: a sayable follows the reader\'s script, a body keeps its own frame', () => {
  const L = page('ltr'), R = page('rtl');
  assert.deepEqual([L.frame().dir, R.frame().dir], ['ltr', 'rtl']);
  assert.deepEqual(L.axis('time'), { axis: 'x', sign: 1, mirrored: false });
  assert.deepEqual(R.axis('time'), { axis: 'x', sign: -1, mirrored: true });
  assert.deepEqual([L.axis('ladder'), R.axis('ladder')], [{ axis: 'y', sign: -1, mirrored: false }, { axis: 'y', sign: -1, mirrored: false }]);
  assert.equal(R.axis('place').mirrored, false);
});
ok('direction: a key means a command by the page\'s direction — in Persian ArrowLeft is later and next; ArrowUp is always up', () => {
  const L = page('ltr'), R = page('rtl');
  assert.deepEqual([L.command(key('ArrowRight'), ['time']), L.command(key('ArrowLeft'), ['time'])], ['later', 'earlier']);
  assert.deepEqual([R.command(key('ArrowLeft'), ['time']), R.command(key('ArrowRight'), ['time'])], ['later', 'earlier']);
  assert.deepEqual([R.command(key('ArrowLeft'), ['flow']), L.command(key('ArrowRight'), ['ordinal'])], ['next', 'next']);
  for (const P of [L, R]) {
    assert.deepEqual([P.command(key('ArrowUp'), ['ladder']), P.command(key('ArrowDown'), ['ladder'])], ['up', 'down']);
    assert.deepEqual([P.command(key('Home'), ['time']), P.command(key('End'), ['time'])], ['first', 'last']);
    assert.equal(P.command(key('ArrowUp'), ['time']), null);
    assert.deepEqual([P.command(key('+'), ['depth']), P.command(key('-'), ['depth'])], ['in', 'out']);
  }
  assert.deepEqual([L.command(key('ArrowDown'), ['walk']), R.command(key('ArrowDown'), ['walk'])], ['next', 'next']);
});
ok('direction: a glyph is chosen by meaning and turned by the frame; up never turns', () => {
  const L = page('ltr'), R = page('rtl');
  assert.deepEqual(['next', 'previous', 'later', 'earlier', 'up', 'down'].map(m => L.glyph(m)), ['→', '←', '→', '←', '↑', '↓']);
  assert.deepEqual(['next', 'previous', 'later', 'earlier', 'up', 'down'].map(m => R.glyph(m)), ['←', '→', '←', '→', '↑', '↓']);
  assert.deepEqual([R.glyph('north'), R.glyph('east')], ['↑', '→']);
});
ok('direction: the law\'s rows, where the page carries them, decide — as the law writes them ("1", "true")', () => {
  const rows = [{ order: 'time', axis: 'inline', sense: '1', follows: 'false', commands: ['later', 'earlier'] },
                { order: 'ladder', axis: 'vertical', sense: '-1', follows: 'false', commands: ['up', 'down'] }];
  const R = page('rtl', rows);
  assert.deepEqual(R.axis('time'), { axis: 'x', sign: 1, mirrored: false });           // a row that keeps its frame
  assert.equal(R.command(key('ArrowRight'), ['time']), 'later');
  assert.equal(R.axis('flow'), null);                                                    // what the law does not name, nothing
});
// ---- a place (place.js): suggestions as typed, the garden's own first, the reader's position only when asked
const place = await import(new URL('place.js', lib));
ok('place: what a position says — a coordinate in its system, a map\'s element, a gazetteer\'s feature, a being', () => {
  assert.deepEqual(place.parse('EPSG:4326;35.6976,51.4023'), {is: 'coordinate', crs: 'EPSG:4326', a: '35.6976', b: '51.4023', c: '', epoch: ''});
  assert.deepEqual(place.parse('osm:way/42'), {is: 'osm', element: 'way/42'});
  assert.deepEqual(place.parse('geonames:112931'), {is: 'geonames', id: '112931'});
  assert.deepEqual(place.parse('cafe-1'), {is: 'other', text: 'cafe-1'});
  assert.equal(place.parse('osm:way/042').is, 'other');
});
ok('place: a lookup folds what a keyboard changes and a reader does not — the two yehs and kafs, a hamza, marks, case, digits, a joiner', () => {
  assert.deepEqual(place.fold('كاخ'), place.fold('کاخ'));                 // kaf, keheh
  assert.deepEqual(place.fold('علي'), place.fold('علی'));                 // two yehs
  assert.deepEqual(place.fold('آشپز'), place.fold('اشپز'));     // an alef with a madda
  assert.deepEqual(place.fold('Café Crème'), ['cafe', 'creme']);
  assert.deepEqual(place.fold('İstanbul'), ['istanbul']);
  assert.deepEqual(place.fold('منطقه ۶'), place.fold('منطقه 6'));   // the reader's digits
  assert.deepEqual(place.fold('\u0648\u0644\u06CC\u200C\u0639\u0635\u0631'), place.fold('\u0648\u0644\u06CC \u0639\u0635\u0631'));
});
const OWN = [{id: 'bookshop', title: 'کاخ کتاب', kind: 'org', point: [35.7001, 51.4012], osm: 'way/9001'},
             {id: 'kakh', title: 'کاخ', kind: 'org'}, {id: 'office', title: 'Head office', kind: 'org'}];
ok('place: the garden\'s own places, matched by every word typed beginning a word of the title — what is typed first', () => {
  assert.deepEqual(place.own('كاخ', OWN).map(s => s.at[0]), ['kakh', 'bookshop']);   // typed with an Arabic kaf
  assert.deepEqual(place.own('head off', OWN).map(s => [s.at, s.read]), [[['office'], null]]);
  assert.deepEqual(place.own('', OWN), []);
});
const HERE = {places: [{code: 'zz-tehran-palestine', label: 'فلسطین', detail: 'تهران', kind: 'street', point: [35.6976, 51.4023], osm: 'way/42'},
                       {code: 'zz-bushehr', label: 'Bushehr Province', kind: 'province'}],
              sources: [{name: 'OpenStreetMap', licence: 'ODbL-1.0', attribution: '© OpenStreetMap contributors', url: 'https://www.openstreetmap.org/copyright'}]};
const FAR = {places: [{label: 'خیابان فلسطین', detail: 'تهران', point: [35.6976, 51.4023], osm: 'way/42'},
                      {label: 'Istanbul', detail: 'Türkiye', point: [41.0082, 28.9784], osm: 'relation/223474'}],
             sources: [{name: 'OpenStreetMap', licence: 'ODbL-1.0', attribution: '© OpenStreetMap contributors', url: 'https://www.openstreetmap.org/copyright'}], sent: true};
ok('place: suggestions in their order — the garden\'s own, then the machine\'s, then from beyond; one element offered once; nowhere never', () => {
  const s = place.merge({own: place.own('کاخ', OWN), here: HERE.places, hereSources: HERE.sources, far: FAR.places, farSources: FAR.sources});
  assert.deepEqual(s.map(x => [x.source, x.label]), [['own', 'کاخ'], ['own', 'کاخ کتاب'],
    ['here', 'فلسطین'], ['far', 'Istanbul']]);   // the far «فلسطین» is way/42 again; Bushehr has no point
});
ok('place: what lands — the garden\'s own as the being it is; any other as a WGS 84 coordinate, latitude first, its element beside it, read from its source', () => {
  const [mine, here, far] = place.merge({own: [OWN[0]].map(p => place.own(p.title, [p])[0]), here: [HERE.places[0]], hereSources: HERE.sources,
    far: [FAR.places[1]], farSources: FAR.sources});
  assert.deepEqual(place.take(mine), {value: ['bookshop'], read: null});
  assert.deepEqual(place.take(here), {value: ['EPSG:4326;35.6976,51.4023', 'osm:way/42'], read: {
    from: {someone: 'org', at: 'uri:https://www.openstreetmap.org/copyright'},
    through: 'OpenStreetMap way/42, as this machine’s place search holds it (© OpenStreetMap contributors, ODbL-1.0)'}, area: true});
  assert.match(place.take(far).read.through, /^OpenStreetMap relation\/223474, as a place service beyond this machine found it/);
  const [tiny] = place.merge({here: [{code: 'x', label: 'x', point: [1e-7, -0.5]}], hereSources: HERE.sources});
  assert.deepEqual(tiny.at, ['EPSG:4326;0.0000001,-0.5']);                              // never an exponent
  assert.deepEqual(place.merge({here: [{code: 'y', label: 'y', point: [91, 0]}, {code: 'z', label: 'z', point: [NaN, 1]}]}), []);
  const [host] = place.merge({own: [{code: 'cafe-b', label: 'Cafe B', kind: 'org', point: [35.6976, 51.4023], osm: 'way/42'}]});
  assert.deepEqual([host.source, host.at, host.read, host.what], ['own', ['cafe-b'], null, 'org']);   // a host's read of the garden
  assert.ok(!JSON.stringify(place.take(far)).includes('"name"'), 'a map\'s id never lands as a name');
});
ok('place: an area — a country, a city, a street, as its source names what it is, or a way or a relation of the map, or a gazetteer\'s feature — is said to be one; a house at a node, a shop, and the garden\'s own beings are not', () => {
  const s = place.merge({own: place.own('کاخ', OWN), here: [HERE.places[0],
    {code: 'zz-tehran', label: 'تهران', kind: 'city', point: [35.6893, 51.3896], osm: 'node/29'},
    {code: 'zz-house', label: 'پلاک ۱۲', kind: 'house', point: [35.6977, 51.4024], osm: 'node/77'},
    {code: 'zz-bushehr-p', label: 'بوشهر', kind: 'province', point: [28.9, 51.0]},
    {code: 'zz-feature', label: 'Feature', kind: 'other', point: [35.7, 51.4], geonames: '112931'}], hereSources: HERE.sources,
    far: [FAR.places[1], {label: 'A shop', point: [41.01, 28.98], osm: 'node/8'}], farSources: FAR.sources});
  assert.deepEqual(s.map(x => [x.label, !!x.area]), [['کاخ', false], ['کاخ کتاب', false], ['فلسطین', true], ['تهران', true],
    ['پلاک ۱۲', false], ['بوشهر', true], ['Feature', true], ['Istanbul', true], ['A shop', false]]);   // the own café stands at a way, and is a being
  assert.equal(place.take(s[2]).area, true);
  assert.ok(!('area' in place.take(s[4])) && !('area' in place.take(s[0])));
  assert.ok(!('area' in place.take('osm:relation/6663864')), 'a position typed is the gate\'s to judge, not the widget\'s');
});
ok('place: a position typed with its system is taken as written, a bare coordinate never — in the reader\'s words, with its form', () => {
  assert.deepEqual(place.take('EPSG:4326;35.69,51.39'), {value: ['EPSG:4326;35.69,51.39'], read: null});
  assert.deepEqual(place.take('osm:node/7'), {value: ['osm:node/7'], read: null});
  assert.equal(place.take('35.69, 51.39', {lang: 'en'}).error, 'A coordinate is never bare: choose a place, or write it with its system, as EPSG:4326;35.69,51.39.');
  assert.ok(place.take('۳۵٫۶۹، ۵۱', {lang: 'fa'}).error.startsWith('مختصات'));
  assert.ok(place.take('somewhere', {lang: 'en'}).error.startsWith('Choose a place'));
  assert.deepEqual(place.take('rack-a', {free: true}), {value: ['rack-a'], read: null});        // a being, for the gate to judge
  assert.deepEqual(place.take('', {}), {value: []});
  assert.equal(place.take({at: []}, {lang: 'en'}).error, 'This place says no coordinate: choose another, or write its position.');
});
ok('place: shown in the reader\'s digits, left to right in its isolate, with the accuracy the law states for its system', () => {
  configure({crs: [{crs: 'EPSG:4326', accuracy: {count: '2', unit: 'length-meter'}}]});
  const en = strip(place.show(['EPSG:4326;35.6976,51.4023', 'osm:way/42'], {lang: 'en'}));
  assert.equal(en, '35.6976, 51.4023 EPSG:4326 ±2 m · OpenStreetMap way/42');
  const fa = String(place.show('EPSG:4326;35.6976,51.4023', {lang: 'fa'}));
  assert.ok(fa.includes('<bdi dir="ltr" class="w-place-coord">۳۵٫۶۹۷۶, ۵۱٫۴۰۲۳</bdi>'), fa);
  assert.equal(strip(place.show('cafe-1', {titleOf: id => '<b>Café</b>'})), '&lt;b&gt;Café&lt;/b&gt;');
  assert.equal(String(place.show([])), '<span class="w-none">—</span>');
});
ok('place: the field — its own direction, a list a keyboard moves through, a button for the reader\'s position, the value escaped', () => {
  const html = String(place.edit('s0.at', ['EPSG:4326;1,2'], {lang: 'en', sealed: true}));
  assert.ok(html.includes('role="combobox"') && html.includes('dir="auto"') && html.includes('role="listbox"') && html.includes('data-place-near'));
  assert.ok(html.includes('value="{&quot;at&quot;:[&quot;EPSG:4326;1,2&quot;],&quot;read&quot;:null}"'), html);
  assert.ok(html.includes('w-place-sealed') && html.includes('where a person will be is never sent'));
  assert.ok(!String(place.edit('x', [], {lang: 'en', label: '"><script>'})).includes('"><script>'));
});

// the lookup, driven as a person drives it: a page of the least it needs, and sources that count what they are asked
function fakeField(html) {
  const ev = {}, mk = (attrs = {}) => ({attrs, value: attrs.value || '', hidden: !!attrs.hidden, innerHTML: '', classList: {contains: c => (attrs.class || '').split(' ').includes(c)},
    setAttribute(k, v) { this.attrs[k] = String(v); }, getAttribute(k) { return this.attrs[k] ?? null; }, removeAttribute(k) { delete this.attrs[k]; },
    addEventListener(t, f) { (ev[t] = ev[t] || []).push(f); }, querySelectorAll() { return []; }});
  const attr = (re) => { const m = re.exec(html); return m ? m[1] : ''; };
  const input = mk({class: 'w-input w-place-input', value: attr(/class="w-input w-place-input"[^>]*value="([^"]*)"/)});
  const kept = mk({type: 'hidden', value: attr(/type="hidden" name="[^"]*" value="([^"]*)"/).replace(/&quot;/g, '"')});
  const list = mk({id: attr(/role="listbox" id="([^"]*)"/), hidden: true}), near = mk({});
  const box = {matches: s => s === '[data-place]', classList: {contains: () => html.includes('w-place-sealed')},
    querySelector: s => s === '.w-place-input' ? input : s === '.w-place-list' ? list : s === '[data-place-near]' ? near : s === 'input[type="hidden"]' ? kept : null};
  return {box, input, list, kept, near, ev};
}
const asked = {here: [], far: []};
const SOURCES = {own: OWN, here: async (q, o) => { asked.here.push([q, o]); return HERE; }, far: async (q, o) => { asked.far.push([q, o]); return FAR; }};
let lookups = 0;
await (async () => {
  const f = fakeField(String(place.edit('s0.at', [], {lang: 'en'})));
  const api = place.wire(f.box, SOURCES, {lang: 'en'});
  const got = await api.ask('کاخ');
  assert.deepEqual(got.map(s => s.source), ['own', 'own', 'here', 'far']);
  assert.deepEqual(asked.here, [['کاخ', {}]]);
  assert.deepEqual(asked.far, [['کاخ', {}]]);                     // no position: none was asked for
  assert.ok(f.list.innerHTML.indexOf('کاخ') < f.list.innerHTML.indexOf('فلسطین'));
  assert.ok(f.list.innerHTML.includes('© OpenStreetMap contributors'), 'whom the places are from is said');
  api.near('35.69760,51.40230');                                                 // the reader asked: now, and only now
  await api.ask('فلسطین');
  assert.deepEqual(asked.far[1], ['فلسطین', {near: '35.69760,51.40230'}]);
  const picked = api.pick(0);                                                    // the machine's «فلسطین»; the far one is the same element
  assert.equal(picked.osm, 'way/42');
  assert.deepEqual(place.take(place.collect(f.box)).value, ['EPSG:4326;35.6976,51.4023', 'osm:way/42']);
  assert.equal(place.take(place.collect(f.box)).area, true, 'a street picked is kept as an area');
  lookups++;
})();
await (async () => {      // A SEALED FIELD: where a person will be is looked up here alone — the place service is never asked
  const before = asked.far.length;
  const f = fakeField(String(place.edit('s1.at', [], {lang: 'en', sealed: true})));
  const api = place.wire(f.box, SOURCES, {lang: 'en', sealed: true});
  api.near('35.7,51.4');
  const got = await api.ask('فلسطین');
  assert.equal(asked.far.length, before, 'a sealed field asked beyond the machine');
  assert.deepEqual(got.map(s => s.source), ['here']);
  lookups++;
})();
await (async () => {      // OFFLINE: a host that does not answer leaves the garden's own standing
  const f = fakeField(String(place.edit('s2.at', [], {lang: 'en'})));
  const api = place.wire(f.box, {own: OWN, here: async () => { throw new Error('offline'); }, far: async () => { throw new Error('offline'); }}, {lang: 'en'});
  assert.deepEqual((await api.ask('کاخ')).map(s => s.at[0]), ['kakh', 'bookshop']);
  lookups++;
})();
ok('place: the lookup — own first, then the machine\'s, then beyond; the reader\'s position only once given; a sealed field never asks beyond the machine; offline, the garden\'s own', () => {
  assert.equal(lookups, 3);
});
console.log(`PASS: widgets — ${n} groups of checks: safe, settings, locale, number, money, moment in ten calendars, text, name, choice, being, exact, a repetition and a form's value, direction, a place.`);
