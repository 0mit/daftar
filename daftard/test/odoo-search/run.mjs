// run — the acceptance of design §10.2: Odoo's own search tests (web/static/tests/search/) pass against daftard, and
// fail against a daftard with one call removed. test/odoo-search/README.md says what this proves, and what it does not.
//
//   ODOO_PASSWORD=… node test/odoo-search/run.mjs --tree <daftar tree> [--odoo http://127.0.0.1:8269] [--db views17]
//        [--login admin] [--without <call> | --all] [--filter <QUnit filter>] [--out <report.json>]
//
// It builds daftard from this tree (with --without, from a copy of it whose answerer has that call removed), grows a
// scratch garden of the core from the daftar tree, serves it with that daftard (its worker's records read from the
// register: register_worker.py), opens a seat on daftard's Odoo origin through its own door, and runs Odoo's own test
// page, from the Community instance named, in headless Chromium with hook.js: each read call the tests make is
// carried here and answered by daftard. --all runs once whole, then once per call the tests use, each removed alone.
// Exit 0 when every test passes whole but the two that assert the mock's own error (DISAGREE), which fail just as
// Odoo's server would have them, and (with --all) every call removed fails a test that uses it.
import { spawn, spawnSync } from 'node:child_process';
import { chmodSync, cpSync, mkdirSync, mkdtempSync, readFileSync, renameSync, rmSync, writeFileSync } from 'node:fs';
import { createServer, request } from 'node:http';
import net from 'node:net';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(HERE, '..', '..');
const opt = { odoo: 'http://127.0.0.1:8269', db: 'views17', login: 'admin', out: '' };
const argv = process.argv.slice(2);
for (let i = 0; i < argv.length; i++) {
  const k = argv[i].replace(/^--/, '');
  if (k === 'all' || k === 'keep') opt[k] = true;
  else opt[k] = argv[++i];
}
if (!opt.tree || !process.env.ODOO_PASSWORD) {
  console.error('usage: ODOO_PASSWORD=… node test/odoo-search/run.mjs --tree <daftar tree> [--without <call> | --all]');
  process.exit(2);
}
// the calls the answerer takes, each by the one branch that answers it (python/odoo_rpc.py Answerer.call)
const CALLS = ['get_views', 'fields_get', 'web_search_read', 'web_read', 'read', 'name_search', 'read_group',
  'web_read_group', 'search_count', 'search_panel_select_range', 'search_panel_select_multi_range'];
// Two tests assert the MOCK's own error (README, "What it shows"): its global counters read an array by record id, so a
// parent never gains its children's counts, where Odoo's server, and its own server test, add them. daftard answers as
// the server does, so each fails, and must fail just so: the first counts it asserts are the server's [2, 2] against
// the mock's [2, 1]. A run where either passes, or fails otherwise, is no acceptance.
const DISAGREE = {
  'web > Search > SearchPanel :: many2one: select one, expand, hierarchize, counters': { actual: '[2,2]', expected: '[2,1]' },
  'web > Search > SearchPanel :: many2one: select one, no expand, hierarchize, counters': { actual: '[2,2]', expected: '[2,1]' },
};
const SCRATCH = mkdtempSync(join(process.env.TMPDIR || tmpdir(), 'odoo-search-'));
const log = (...a) => console.error('·', ...a);
// what this run started, stopped however it ends: an interrupted run leaves no browser, no daftard and no scratch
const children = new Set();
for (const sig of ['SIGINT', 'SIGTERM']) {
  process.on(sig, () => {
    for (const c of children) c.kill();
    if (!opt.keep) rmSync(SCRATCH, { recursive: true, force: true });
    process.exit(2);
  });
}

function sh(cmd, args, o = {}) {
  const r = spawnSync(cmd, args, { encoding: 'utf8', ...o });
  if (r.status !== 0) throw new Error(`${cmd} ${args.join(' ')}: ${(r.stderr || '') + (r.stdout || '')}`.slice(-1500));
  return r.stdout;
}

function freePort() {
  return new Promise((ok) => { const s = net.createServer(); s.listen(0, '127.0.0.1', () => { const p = s.address().port; s.close(() => ok(p)); }); });
}

// daftard from this tree, or from a copy of it whose answerer has `without` removed: the branch that answers the call
// never taken, so the call is refused as one daftard does not answer
function build(without) {
  let src = REPO;
  if (without) {
    src = join(SCRATCH, 'src-' + without);
    for (const f of sh('git', ['ls-files', '-z'], { cwd: REPO }).split('\0').filter(Boolean)) {
      mkdirSync(dirname(join(src, f)), { recursive: true });
      cpSync(join(REPO, f), join(src, f));
    }
    const p = join(src, 'python', 'odoo_rpc.py');
    const text = readFileSync(p, 'utf8');
    const branch = `        if method == '${without}':\n`;
    if (text.split(branch).length !== 2) throw new Error(`the answerer has no one branch for ${without}`);
    writeFileSync(p, text.replace(branch, `        if method == '${without}' and False:      # removed by the acceptance\n`));
  }
  const out = join(SCRATCH, without ? `daftard-without-${without}` : 'daftard');
  sh('go', ['build', '-o', out, './cmd/daftard'], { cwd: src });
  return out;
}

function http(port, method, path, { host, headers = {}, body } = {}) {
  return new Promise((ok, no) => {
    const req = request({ host: '127.0.0.1', port, method, path, headers: { Host: host || `127.0.0.1:${port}`, ...headers } }, (res) => {
      let data = '';
      res.setEncoding('utf8');
      res.on('data', (d) => { data += d; });
      res.on('end', () => ok({ status: res.statusCode, headers: res.headers, body: data }));
    });
    req.on('error', no);
    if (body) req.write(body);
    req.end();
  });
}

async function serve(bin, garden, register) {
  const port = await freePort(), odooPort = await freePort();
  const state = join(SCRATCH, 'state-' + bin.split('/').pop());
  mkdirSync(join(state, 'odoo', '17.0'), { recursive: true });
  writeFileSync(join(state, 'odoo', '17.0', 'CLIENT.json'), '{"what": "the acceptance: no client is served here; Odoo\'s own test page is"}\n');
  const py = join(SCRATCH, 'python-register');
  writeFileSync(py, `#!/bin/sh\nexec ${process.env.PYTHON || 'python3'} "${join(HERE, 'register_worker.py')}" "$@"\n`);
  chmodSync(py, 0o755);
  writeFileSync(join(state, 'daftard.json'), JSON.stringify({ listen: `127.0.0.1:${port}`, odoo_listen: `127.0.0.1:${odooPort}`,
    gardens: [{ name: 'g', path: garden, python: py, title: 'acceptance', kind: 'core', lang: 'en', gardener: 'sam' }] }, null, 1));
  const p = spawn(bin, ['serve'], { env: { ...process.env, DAFTARD_NOTIFY: 'off', DAFTARD_STATE: state, DAFTAR_ODOO_REGISTER: register },
    stdio: ['ignore', 'ignore', 'pipe'] });
  children.add(p);
  let err = '';
  p.stderr.on('data', (d) => { err += d; });
  for (let i = 0; ; i++) {
    try { if ((await http(port, 'GET', '/health')).status === 200) break; } catch { /* not yet */ }
    if (i > 300) throw new Error('daftard did not start: ' + err.slice(-800));
    await new Promise((r) => setTimeout(r, 100));
  }
  const key = readFileSync(join(state, 'key'), 'utf8').trim();
  // the seat, through daftard's own door: the handplace sends the page to Odoo's origin with a one-time token; the
  // machine's key goes in its header, as the command line sends it, never as a cookie
  const door = await http(port, 'GET', '/odoo?g=g', { headers: { 'X-Daftard-Key': key } });
  const enter = new URL(door.headers.location || 'http://x/');
  if (door.status !== 303 || enter.pathname !== '/odoo/enter') throw new Error('the door did not open: ' + door.status + door.body);
  const host = `localhost:${odooPort}`;
  const seat = await http(odooPort, 'GET', enter.pathname + enter.search, { host });
  const sid = /daftard-odoo=([^;]+)/.exec(String(seat.headers['set-cookie'] || ''))?.[1];
  if (!sid) throw new Error('no seat on Odoo\'s origin: ' + seat.status);
  let id = 0;
  return {
    p, state,
    async call(route, params) { // a call of Odoo's client, as its page on daftard's origin would make it
      const r = await http(odooPort, 'POST', route, { host, body: JSON.stringify({ jsonrpc: '2.0', id: ++id, method: 'call', params }),
        headers: { Origin: `http://${host}`, 'Content-Type': 'application/json', Cookie: `daftard-odoo=${sid}` } });
      let env;
      try { env = JSON.parse(r.body); } catch { return { error: { message: `daftard answered ${r.status}: ${r.body.slice(0, 200)}` } }; }
      return env.error ? { error: env.error } : { result: env.result };
    },
    stop() { p.kill(); },
  };
}

// the test's data, laid where daftard reads a garden's: its views and fields as captures, its records as the register,
// its favourites on the reader's (the gardener's) own ref
function layer(garden, register) {
  const cap = join(garden, 'captures', 'views', 'odoo-17.0');
  let serial = null, favs = null;
  return (data) => {
    if (data.serial !== serial) {
      rmSync(cap, { recursive: true, force: true });
      serial = data.serial;
    }
    mkdirSync(cap, { recursive: true });
    writeFileSync(join(cap, 'CAPTURE.json'), JSON.stringify({ what: "the acceptance: the views of the Odoo test being run", series: '17.0' }) + '\n');
    for (const [m, { fields }] of Object.entries(data.models)) {
      mkdirSync(join(cap, m), { recursive: true });
      writeFileSync(join(cap, m, 'fields.json'), JSON.stringify(fields));
    }
    for (const [k, arch] of Object.entries(data.archs)) {
      const [m, type] = k.split('|');
      mkdirSync(join(cap, m), { recursive: true });
      writeFileSync(join(cap, m, `${type}.xml`), String(arch).trim() + '\n');
    }
    writeFileSync(register + '.part', JSON.stringify({ models: data.models }));
    renameSync(register + '.part', register);
    const doc = { person: 'sam', labels: {}, favourites: {} };
    for (const [m, list] of Object.entries(data.filters)) {
      list.forEach((f, i) => {
        doc.favourites[`${m}:${f.id ?? i}`] = { model: m, name: String(f.name || ''), domain: String(f.domain ?? '[]'),
          context: String(f.context ?? '{}'), sort: String(f.sort ?? '[]'), is_default: !!f.is_default,
          at: `2026-01-01T00:00:00.${String(i).padStart(9, '0')}Z` };
      });
    }
    const text = JSON.stringify(doc);
    if (text !== favs) {
      const g = (args, input) => sh('git', args, { cwd: garden, input }).trim();
      const blob = g(['hash-object', '-w', '--stdin'], text + '\n');
      const tree = g(['mktree'], `100644 blob ${blob}\tlabels.json\n`);
      const commit = g(['-c', 'user.name=sam', '-c', 'user.email=sam@x', 'commit-tree', tree, '-m', 'sam: the test\'s favourites']);
      g(['update-ref', 'refs/daftar/custom/sam', commit]);
      favs = text;
    }
  };
}

async function browser() {
  const profile = mkdtempSync(join(SCRATCH, 'cdp-'));
  const chrome = spawn('chromium', ['--headless=new', '--disable-gpu', '--no-sandbox', '--remote-debugging-port=0',
    `--user-data-dir=${profile}`, '--window-size=1400,1000', 'about:blank'], { stdio: ['ignore', 'ignore', 'pipe'] });
  children.add(chrome);
  const wsUrl = await new Promise((ok, no) => {
    let e = '';
    chrome.stderr.on('data', (d) => { e += d; const m = /DevTools listening on (ws:\/\/\S+)/.exec(e); if (m) ok(m[1]); });
    setTimeout(() => no(new Error('chromium did not start: ' + e)), 20000);
  });
  const ws = new WebSocket(wsUrl);
  await new Promise((ok) => ws.addEventListener('open', ok, { once: true }));
  let seq = 0;
  const waiting = new Map(), handlers = [];
  ws.addEventListener('message', (ev) => {
    const m = JSON.parse(ev.data);
    if (m.id && waiting.has(m.id)) { const { ok, no } = waiting.get(m.id); waiting.delete(m.id); m.error ? no(new Error(m.error.message)) : ok(m.result); }
    for (const h of handlers) h(m);
  });
  const send = (method, params = {}, sessionId) => new Promise((ok, no) => {
    const i = ++seq; waiting.set(i, { ok, no }); ws.send(JSON.stringify({ id: i, method, params, sessionId }));
  });
  const { targetId } = await send('Target.createTarget', { url: 'about:blank' });
  const { sessionId } = await send('Target.attachToTarget', { targetId, flatten: true });
  const S = (m, p) => send(m, p, sessionId);
  return { S, on: (h) => handlers.push(h), close() { chrome.kill(); } };
}

async function runOnce(bin, garden, label) {
  const register = join(SCRATCH, `register-${label}.json`);
  writeFileSync(register, '{"models": {}}');
  const d = await serve(bin, garden, register);
  const lay = layer(garden, register);
  const auth = await fetch(`${opt.odoo}/web/session/authenticate`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params: { db: opt.db, login: opt.login, password: process.env.ODOO_PASSWORD } }) });
  const sid = /session_id=([^;]+)/.exec(auth.headers.get('set-cookie') || '')?.[1];
  if (!sid) throw new Error('the Community instance refused the login');
  // the bridge: the page asks it synchronously (hook.js), and it lays the test's data or asks daftard
  const bridgeServer = createServer((req, res) => {
    let body = '';
    req.setEncoding('utf8');
    req.on('data', (chunk) => { body += chunk; });
    req.on('end', async () => {
      let answer;
      try {
        const { kind, data } = JSON.parse(body);
        answer = kind === 'lay' ? (lay(data), {}) : await d.call(data.route, data.params);
      } catch (e) {
        answer = { error: { message: String(e.message || e).slice(0, 400) } };
      }
      res.writeHead(200, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': new URL(opt.odoo).origin });
      res.end(JSON.stringify(answer));
    });
  });
  await new Promise((ok) => bridgeServer.listen(0, '127.0.0.1', ok));
  const b = await browser();
  const { S } = b;
  const exceptions = [];
  b.on((m) => {
    if (m.method === 'Runtime.exceptionThrown') exceptions.push((m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text).slice(0, 300));
    if (m.method === 'Runtime.consoleAPICalled' && m.params.type === 'error') exceptions.push(m.params.args.map((x) => x.value ?? x.description ?? '').join(' ').slice(0, 600));
  });
  await S('Page.enable'); await S('Runtime.enable'); await S('Network.enable');
  await S('Network.setCookie', { name: 'session_id', value: sid, url: opt.odoo });
  await S('Page.addScriptToEvaluateOnNewDocument', { source: `globalThis.__DAFTAR_BRIDGE__ = ${bridgeServer.address().port};\n` + readFileSync(join(HERE, 'hook.js'), 'utf8') });
  await S('Page.navigate', { url: `${opt.odoo}/web/tests?debug=assets${opt.filter ? '&filter=' + encodeURIComponent(opt.filter) : ''}` });
  const t0 = Date.now();
  let got;
  for (;;) {
    await new Promise((r) => setTimeout(r, 2000));
    const r = await S('Runtime.evaluate', { expression: 'JSON.stringify({n: (globalThis.__results||{tests:[]}).tests.length, done: (globalThis.__results||{}).done})', returnByValue: true });
    got = JSON.parse(r.result.value || '{}');
    if (got.done || Date.now() - t0 > 40 * 60000) break;
  }
  const r = await S('Runtime.evaluate', { expression: 'JSON.stringify({results: globalThis.__results, calls: globalThis.__calls})', returnByValue: true });
  b.close();
  bridgeServer.close();
  d.stop();
  const { results, calls } = JSON.parse(r.result.value);
  const key = (m, n) => `${m} :: ${n}`;
  const perTest = new Map(results.tests.map((t) => [key(t.module, t.name), { ...t, daftard: [], mock: [] }]));
  for (const c of calls) {
    const t = perTest.get(key(c.module, c.test));
    if (t) t[c.by === 'daftard' ? 'daftard' : 'mock'].push(c.method || c.route);
    if (t && c.error) (t.refused = t.refused || []).push(`${c.model}.${c.method}: ${c.error}`);
  }
  const tests = [...perTest.values()];
  const failed = tests.filter((t) => t.failed && !t.skipped);
  return { label, done: results.done, tests, failed, assertions: results.assertions || [], exceptions: exceptions.slice(0, 60),
    seconds: Math.round((Date.now() - t0) / 1000) };
}

function summary(run) {
  const t = run.tests, skipped = t.filter((x) => x.skipped).length;
  const withD = t.filter((x) => x.daftard.length), mockOnly = t.filter((x) => x.mock.length);
  return `${run.label}: ${t.length} tests, ${t.length - run.failed.length - skipped} passed, ${run.failed.length} failed, ` +
    `${skipped} skipped by Odoo; ${withD.length} asked daftard ${withD.reduce((n, x) => n + x.daftard.length, 0)} calls; ` +
    `${mockOnly.length} also asked Odoo's mock server what daftard does not answer (${[...new Set(mockOnly.flatMap((x) => x.mock))].join(', ')}) — ${run.seconds}s`;
}

let exit = 0;
const report = { what: "Odoo's own search tests against daftard (design §10.2)", odoo: opt.odoo, runs: [] };
try {
  log('a scratch garden from', opt.tree);
  const garden = sh(process.env.PYTHON || 'python3', [join(HERE, 'garden.py'), opt.tree, join(SCRATCH, 'g')]).trim();
  const plan = opt.all ? [null, ...CALLS] : [opt.without || null];
  let whole = null;
  for (const without of plan) {
    log(without ? `daftard without ${without}` : 'daftard whole', '— building');
    const bin = build(without);
    const run = await runOnce(bin, garden, without ? `without ${without}` : 'whole');
    report.runs.push(run);
    console.log(summary(run));
    if (!without) {
      whole = run;
      const firstFailed = (k) => run.assertions.find((a) => `${a.module} :: ${a.name}` === k && (a.actual || a.expected));
      for (const f of run.failed) {
        const k = `${f.module} :: ${f.name}`, d = DISAGREE[k], a = firstFailed(k);
        const asServer = d && a && a.actual === d.actual && a.expected === d.expected;
        console.log(`  ${asServer ? 'AS ODOO\'S SERVER' : 'FAIL'}  ${k}  (daftard: ${f.daftard.join(', ') || '—'})` +
          (asServer ? ` — counts ${a.actual}, the mock's own ${a.expected}` : ''));
        if (!asServer) exit = 1;
      }
      for (const k of Object.keys(DISAGREE)) {
        if (!run.failed.some((f) => `${f.module} :: ${f.name}` === k)) { console.log(`  PASSES, AS THE MOCK  ${k}`); exit = 1; }
      }
      if (!run.done) exit = 1;
    } else {
      const users = new Set((whole || run).tests.filter((x) => x.daftard.includes(without)).map((x) => `${x.module} :: ${x.name}`));
      const hit = run.failed.filter((f) => users.has(`${f.module} :: ${f.name}`));
      const ok = users.size === 0 ? null : hit.length > 0;
      console.log(`  ${ok === null ? 'UNUSED' : ok ? 'FAILS ' : 'PASSES'}  without ${without}: ${hit.length} of the ${users.size} tests that ask it fail` +
        (ok === null ? ' (no test asks it)' : ''));
      if (ok === false) exit = 1;
      run.users = users.size;
      run.hit = hit.length;
    }
  }
} catch (e) {
  console.error('run:', e.stack || e);
  exit = 2;
} finally {
  if (opt.out) writeFileSync(opt.out, JSON.stringify(report, null, 1));
  for (const c of children) c.kill();
  await new Promise((r) => setTimeout(r, 500));          // the browser and daftard let go of their files first
  if (!opt.keep) {
    try { rmSync(SCRATCH, { recursive: true, force: true, maxRetries: 10, retryDelay: 300 }); } catch (e) { console.error('run: scratch left at', SCRATCH, e.code); }
  }
}
process.exit(exit);
