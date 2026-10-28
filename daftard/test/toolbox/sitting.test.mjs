// node test/toolbox/sitting.test.mjs — a write refused for want of a sitting (409, `sitting`) asks who is at the
// keyboard, and is made again, once, when a sitting is begun; refused again or declined, it is said as it was.
import assert from 'node:assert/strict';
globalThis.location = {pathname: '/', search: '?g=g'};
const calls = [];
let answers = [];
globalThis.fetch = async (url, init) => {
  calls.push([url, init?.method || 'GET']);
  const [status, body] = answers.shift();
  return {ok: status < 400, status, headers: {get: () => ''}, json: async () => body};
};
const api = await import('../../web/toolbox/api.js');
let asked = 0;
api.whenSittingAsked(async () => { asked++; return true; });
answers = [[409, {error: 'who is at the keyboard?', sitting: true}], [200, {saved: true}]];
assert.deepEqual(await api.post('/api/labels', {key: 'nav.cases'}), {saved: true});
assert.equal(asked, 1);
assert.deepEqual(calls.map(c => c[1]), ['POST', 'POST']);

// declined: the refusal is said as it was, and nothing is made again
api.whenSittingAsked(async () => { asked++; return false; });
answers = [[409, {error: 'who is at the keyboard?', sitting: true}]];
await assert.rejects(api.post('/api/labels', {}), e => e.message === 'who is at the keyboard?');
assert.equal(asked, 2);

// begun, and refused again: asked once, never in a loop
api.whenSittingAsked(async () => { asked++; return true; });
answers = [[409, {error: 'who?', sitting: true}], [409, {error: 'who?', sitting: true}]];
await assert.rejects(api.post('/api/labels', {}), e => e.message === 'who?');
assert.equal(asked, 3);

// another refusal is no question of who sits
answers = [[409, {error: 'saved already with other values'}]];
await assert.rejects(api.post('/api/save', {}), e => e.message === 'saved already with other values');
assert.equal(asked, 3);
console.log('PASS: sitting — a write refused for want of a sitting asks once, and is made again once a sitting is begun.');
