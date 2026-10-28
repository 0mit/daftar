// seven — the handplace by its seven problems (web/app/pages/seven.js), clicked through in headless Chromium. It writes
// NOTHING, so it may be pointed at any garden a daftard serves:
//
//   DAFTAR_URL=http://127.0.0.1:8790 DAFTAR_KEY=<key> DAFTAR_GARDEN=<garden> node test/render/seven.mjs
//
// The navigation is the seven pages; each renders with no exception; an old page's address (#accounts, #posting,
// #calendar, #categorize, #clients, #vouchers) opens the page that holds it with that part chosen; the switch changes
// the part; who owes whom is drawn as flows whose arrow is the glyph of `next` on this right-to-left page; and a /go/
// address still opens the decision page. Any exception a page throws fails the run.
import assert from 'node:assert/strict';
import { browser } from './cdp.mjs';

const BASE = process.env.DAFTAR_URL, KEY = process.env.DAFTAR_KEY, GARDEN = process.env.DAFTAR_GARDEN;
if (!BASE || !KEY || !GARDEN) { console.error('DAFTAR_URL, DAFTAR_KEY and DAFTAR_GARDEN are needed'); process.exit(2); }
const b = await browser({base: BASE, key: KEY});
const {evaluate, until, ready, click, page} = b;
const step = name => console.log('·', name);
const navIds = () => evaluate(`[...document.querySelectorAll('#nav [data-nav]')].map(x => x.dataset.nav)`);

try {
  step('the navigation is the seven problems, the old tabs out of it');
  await page('now');
  const ids = await navIds();
  assert.deepEqual(ids, ['now', 'people-hub', 'time', 'money', 'books', 'company', 'between'], 'the navigation: ' + ids.join(' '));

  step('each page renders, its title and its parts');
  for (const id of ids) {
    await page(id);
    await until(`document.getElementById('content').getAttribute('aria-busy') === 'false'`, `${id} to render`);
    const err = await evaluate(`document.querySelector('#content .w-guided')?.textContent || ''`);
    assert.equal(err, '', `${id} shows an error: ${err}`);
    assert.ok(await evaluate(`document.querySelector('#nav [data-nav="${id}"]').classList.contains('active')`), `${id} is not marked in the navigation`);
  }

  step('an old page\'s address opens the page that holds it, its part chosen');
  for (const [old, host] of [['accounts', 'money'], ['posting', 'money'], ['categorize', 'money'], ['calendar', 'time'],
    ['clients', 'people-hub'], ['vouchers', 'books'], ['followups', 'time']]) {
    await page(old);
    await until(`document.getElementById('content').getAttribute('aria-busy') === 'false'`, `${old} to render`);
    assert.ok(await evaluate(`document.querySelector('#nav [data-nav="${host}"]').classList.contains('active')`), `#${old} does not open ${host}`);
    assert.ok(await evaluate(`!!document.querySelector('#content section[data-part="${old}"]')`), `#${old}: its part is not shown on ${host}`);
  }

  step('the switch changes the part, one at a time');
  await page('money');
  await click('[data-action="part-tab"][data-tab="posting"]');
  await until(`document.querySelector('#content section[data-part="posting"]') && !document.querySelector('#content section[data-part="accounts"]')`, 'the card purchases, alone');
  assert.ok(await evaluate(`!!document.querySelector('#content section[data-part="owes"]')`), 'who owes whom left the page with the switch');

  step('who owes whom: a flow from payer to payee, its arrow the glyph of next on a right-to-left page');
  const dir = await evaluate(`document.documentElement.dir`);
  const arrows = await evaluate(`[...document.querySelectorAll('.flow .arrow')].map(x => x.textContent.trim())`);
  if (arrows.length) assert.ok(arrows.every(a => a === (dir === 'rtl' ? '←' : '→')), 'an arrow against the page: ' + arrows.join(' '));

  step('a /go/ address still opens the decision page');
  await b.open(`to=/go/${GARDEN}&static=1`);
  await until(`location.pathname === '/go/${GARDEN}' && document.getElementById('content').getAttribute('aria-busy') === 'false'`, 'the landing list');
  assert.match(await evaluate(`document.getElementById('content').textContent`), /منتظر تصمیم شما/);

  assert.deepEqual(b.exceptions || [], [], 'a page threw');
  console.log('PASS: seven — the navigation, every page, the old addresses, the switch, the flows and the landing');
} finally { await b.close(); }
