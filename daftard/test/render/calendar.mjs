// calendar — the calendar page clicked through in headless Chromium: its three views and their steps, and every form
// (a series made, refused first by the page and then by the garden, a session noted, moved and called off, an extra
// session, a package, a series edited). It WRITES to the garden it is pointed at, so it runs against a FRESH scratch copy (its series would overlap the last run's, which the gate refuses):
//
//   DAFTAR_URL=http://127.0.0.1:8792 DAFTAR_KEY=<key> DAFTAR_GARDEN=<garden> node test/render/calendar.mjs
import assert from 'node:assert/strict';
import { browser } from './cdp.mjs';

const BASE = process.env.DAFTAR_URL, KEY = process.env.DAFTAR_KEY, GARDEN = process.env.DAFTAR_GARDEN;
if (!BASE || !KEY || !GARDEN) { console.error('DAFTAR_URL, DAFTAR_KEY and DAFTAR_GARDEN are needed'); process.exit(2); }
const b = await browser({base: BASE, key: KEY});
const {evaluate, until, click, fill, page} = b;
const step = name => console.log('·', name);
const SAVE = 240000;                       // a save waits for the next minute when the same bean was saved this one
const dialog = sel => `dialog[open] ${sel}`;
const q = sel => `document.querySelector(${JSON.stringify(sel)})`;
const saved = what => until(`!document.querySelector('dialog[open]') && document.getElementById('content').getAttribute('aria-busy') === 'false'`, what, SAVE);
const TITLE = 'شنای آزمون ' + String(Date.now()).slice(-5);           // its own on each run

try {
  step('the three views, and stepping through them');
  await page('calendar?view=week&at=2026-10-08');
  await until(`document.querySelector('.timetable .tt-slot')`, 'a session on the week');
  assert.notEqual(await evaluate(`getComputedStyle(document.querySelector('.tt-slot')).gridRowStart`), 'auto', 'the session has no place on the grid');
  await click('[data-action="cal-view"][data-view="month"]');
  await until(`location.hash.includes('view=month') && document.querySelector('.month-grid .mg-day')`, 'the month');
  const label = await b.textOf('.cal-label');
  await click('[data-action="cal-step"][data-step="1"]');
  await until(`document.querySelector('.cal-label')?.textContent !== ${JSON.stringify(label)}`, 'the next month');
  await click('[data-action="cal-step"][data-step="-1"]');
  await until(`document.querySelector('.cal-label')?.textContent === ${JSON.stringify(label)}`, 'the month again');
  await click('[data-action="cal-view"][data-view="list"]');
  await until(`location.hash.includes('view=list') && document.querySelector('.cal-agenda')`, 'the list');
  await click('[data-action="cal-today"]');
  await until(`!location.hash.includes('at=') && document.querySelector('.cal-agenda')`, 'today');

  step('a new series: refused by the page, then by the garden, then saved');
  await page('calendar');
  await click('[data-action="cal-new"]');
  await until(q(dialog(`input[name="title"]`)), 'the series form');
  await fill(dialog(`input[name="title"]`), TITLE);
  await fill(dialog(`select[name="category"]`), 'health');
  await fill(dialog(`input[name="start"]`), '07:00');
  await fill(dialog(`input[name="end"]`), '06:00');
  await fill(dialog(`input[name="from"]`), '1405/07/18');            // 2026-10-10, a Saturday, in the reader's Persian calendar
  await click(dialog(`button[type="submit"]`));
  await until(`document.querySelector('${dialog('[data-field="end"].w-invalid')}') && document.querySelector('${dialog('[data-rec="weekdays"].w-invalid')}')`, 'the end and the week days refused');
  await fill(dialog(`input[name="end"]`), '08:00');
  await click(dialog(`input[name="wd"][value="6"]`));
  await click(dialog(`input[name="wd"][value="1"]`));
  await fill(dialog(`input[name="interval"]`), '2');
  await until(`!document.querySelector('${dialog('[data-rec="note"]')}').hidden`, 'the note for every few weeks');
  await click(dialog(`button[type="submit"]`));
  await until(q(dialog(`.w-dialog-error .w-guided`)), 'the garden to refuse two days every other week', SAVE);
  await fill(dialog(`input[name="interval"]`), '1');
  await fill(dialog(`select[name="ends"]`), 'times');
  await until(`!document.querySelector('${dialog('[data-field="times"]')}').hidden && document.querySelector('${dialog('[data-field="until"]')}').hidden`, 'the count of times');
  await fill(dialog(`input[name="times"]`), '6');
  await click(dialog(`button[type="submit"]`));
  await saved('the series saved');
  const id = await until(`[...document.querySelectorAll('.cal-series tr')].find(r => r.textContent.includes(${JSON.stringify(TITLE)}))?.querySelector('[data-action="cal-edit"]')?.dataset.series`, 'the series listed');

  step('a session noted');
  await page('calendar?view=week&at=2026-10-10');
  await click(`.session[data-series="${id}"][data-day="2026-10-10"]`);
  await until(q(dialog(`select[name="action"]`)), 'the session form');
  assert.equal(await evaluate(`document.querySelector('${dialog('[data-rec="move"]')}').hidden`), true, 'the move is shown before it is chosen');
  await fill(dialog(`textarea[name="note"]`), 'خوب بود');
  await click(dialog(`button[type="submit"]`));
  await saved('the session noted');
  await until(`document.querySelector('.session[data-series="${id}"][data-day="2026-10-10"] .badge.done')`, 'the session marked attended', SAVE);

  step('a session moved');
  await click(`.session[data-series="${id}"][data-day="2026-10-12"]`);
  await until(q(dialog(`select[name="action"]`)), 'the session form');
  await fill(dialog(`select[name="action"]`), 'move');
  await until(`!document.querySelector('${dialog('[data-rec="move"]')}').hidden`, 'the move fields');
  await fill(dialog(`input[name="to_day"]`), '2026-10-14');
  await fill(dialog(`input[name="start"]`), '09:00');
  await fill(dialog(`input[name="end"]`), '10:00');
  await click(dialog(`button[type="submit"]`));
  await saved('the session moved');
  await until(`document.querySelector('.session[data-series="${id}"][data-day="2026-10-14"]') && !document.querySelector('.session[data-series="${id}"][data-day="2026-10-12"]:not(.cancelled)')`, 'the session on its new day', SAVE);

  step('a session called off');
  await page('calendar?view=week&at=2026-10-17');
  await click(`.session[data-series="${id}"][data-day="2026-10-17"]`);
  await until(q(dialog(`select[name="action"]`)), 'the session form');
  await fill(dialog(`select[name="action"]`), 'cancel');
  await click(dialog(`button[type="submit"]`));
  await saved('the session called off');
  await until(`document.querySelector('.session.cancelled[data-series="${id}"][data-day="2026-10-17"]')`, 'the session shown called off', SAVE);

  step('an extra session');
  await page('calendar?view=week&at=2026-10-10');
  await click(`[data-action="cal-extra"][data-series="${id}"]`);
  await until(q(dialog(`input[name="day"]`)), 'the extra form');
  await fill(dialog(`input[name="day"]`), '2026-10-15');
  await fill(dialog(`input[name="start"]`), '18:00');
  await fill(dialog(`input[name="end"]`), '19:00');
  await click(dialog(`button[type="submit"]`));
  await saved('the extra session');
  await until(`document.querySelector('.session[data-series="${id}"][data-day="2026-10-15"]:not([data-extra=""])')`, 'the extra session on the week', SAVE);

  step('a package: a price past the currency\'s places refused, then saved');
  await click(`[data-action="cal-package"][data-series="${id}"]`);
  await until(q(dialog(`input[name="sessions"]`)), 'the package form');
  await fill(dialog(`input[name="sessions"]`), '10');
  await fill(dialog(`input[name="count"]`), '1500.505');
  await fill(dialog(`select[name="unit"]`), 'TRY');
  await click(dialog(`button[type="submit"]`));
  await until(q(dialog(`[data-field="count"].w-invalid`)), 'three places refused for TRY');
  await fill(dialog(`input[name="count"]`), '1500.5');
  await click(dialog(`button[type="submit"]`));
  await saved('the package');
  await until(`[...document.querySelectorAll('.cal-series tr')].find(r => r.textContent.includes(${JSON.stringify(TITLE)}))?.textContent.includes('۱۰ جلسه')`, 'the package listed', SAVE);
  assert.match(await evaluate(`[...document.querySelectorAll('.cal-series tr')].find(r => r.textContent.includes(${JSON.stringify(TITLE)})).textContent`), /۱٬۵۰۰٫۵۰ TRY/);

  step('the series edited, from one of its sessions');
  await click(`.session[data-series="${id}"][data-day="2026-10-10"]`);
  await until(q(dialog(`[data-action="cal-edit"]`)), 'the session form');
  await click(dialog(`[data-action="cal-edit"]`));
  await until(q(dialog(`input[name="title"]`)), 'the series form over it');
  assert.equal(await evaluate(`document.querySelector('${dialog('select[name="ends"]')}').value`), 'times');
  await fill(dialog(`input[name="title"]`), TITLE + ' دوم');
  await click(dialog(`button[type="submit"]`));
  await saved('the series edited');
  await until(`[...document.querySelectorAll('.cal-series tr')].some(r => r.textContent.includes(${JSON.stringify(TITLE + ' دوم')}))`, 'the new title', SAVE);

  step('no sideways scrolling at 390 wide');
  await b.viewport(390, 860);
  for (const view of ['week', 'month', 'list']) {
    await page('calendar?view=' + view);
    const [sw, iw] = await evaluate('[document.documentElement.scrollWidth, innerWidth]');
    assert.ok(sw <= iw, `${view}: the page scrolls sideways (${sw} > ${iw})`);
  }

  assert.deepEqual(b.exceptions, [], 'a page threw');
  console.log('PASS: calendar — three views, a series refused and saved, sessions noted, moved, called off, an extra, a package, an edit');
} catch (e) {
  console.error('FAIL:', e.message);
  if (b.exceptions.length) console.error('page exceptions:', b.exceptions);
  process.exitCode = 1;
} finally {
  await b.close();
}
