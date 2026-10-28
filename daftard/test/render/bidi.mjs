// bidi — headless Firefox driven over WebDriver BiDi, with Node's own WebSocket (no packages): what the render tests
// open the handplace with in Firefox, beside cdp.mjs's Chromium. `const b = await firefox({base, key})`, then b.open(query),
// b.navigate(url), b.evaluate(expr), b.until(expr, what), b.textOf(sel), b.cookies(), b.requests, b.shot(path), b.exceptions
// and b.close(). Its own profile, made for the run and removed after it: never the person's.
import { spawn } from 'node:child_process';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

export async function firefox({base, key, width = 1400, height = 1000}) {
  const profile = mkdtempSync(join(tmpdir(), 'bidi-'));
  const fx = spawn('firefox', ['--headless', '--no-remote', '--profile', profile, '--remote-debugging-port=0',
    `--width=${width}`, `--height=${height}`, 'about:blank'], {stdio: ['ignore', 'pipe', 'pipe']});
  const wsUrl = await new Promise((ok, no) => {
    let out = '';
    const hear = d => { out += d; const m = /WebDriver BiDi listening on (ws:\/\/\S+)/.exec(out); if (m) ok(m[1]); };
    fx.stdout.on('data', hear);
    fx.stderr.on('data', hear);
    setTimeout(() => no(new Error('firefox did not start: ' + out.slice(-500))), 30000);
  });
  const ws = new WebSocket(wsUrl + '/session');
  await new Promise((ok, no) => { ws.addEventListener('open', ok, {once: true}); ws.addEventListener('error', no, {once: true}); });
  let seq = 0;
  const waiting = new Map(), exceptions = [], requests = [];
  ws.addEventListener('message', ev => {
    const m = JSON.parse(ev.data);
    if (m.id && waiting.has(m.id)) {
      const {ok, no} = waiting.get(m.id);
      waiting.delete(m.id);
      m.type === 'error' ? no(new Error(`${m.error}: ${m.message}`)) : ok(m.result);
      return;
    }
    if (m.method === 'log.entryAdded' && m.params.type === 'javascript' && m.params.level === 'error') exceptions.push(m.params.text);
    if (m.method === 'network.beforeRequestSent') {            // each request as sent: its address and the cookies it carried
      const r = m.params.request;
      requests.push({url: r.url, method: r.method, cookies: (r.cookies || []).map(c => c.name), redirects: m.params.redirectCount});
    }
  });
  const send = (method, params = {}) => new Promise((ok, no) => {
    const id = ++seq; waiting.set(id, {ok, no}); ws.send(JSON.stringify({id, method, params}));
  });
  await send('session.new', {capabilities: {}});
  await send('session.subscribe', {events: ['log.entryAdded', 'network.beforeRequestSent']});
  const {contexts} = await send('browsingContext.getTree', {});
  const context = contexts[0].context;
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const b = {
    exceptions, requests, sleep,
    // an expression's value, carried as JSON (BiDi's own remote values need no reading then)
    async evaluate(expr) {
      const r = await send('script.evaluate', {expression: `JSON.stringify((() => (${expr}))())`, target: {context},
        awaitPromise: true, resultOwnership: 'none'});
      if (r.type !== 'success') throw new Error(expr + ': ' + (r.exceptionDetails?.text || 'failed'));
      return r.result.type === 'string' ? JSON.parse(r.result.value) : undefined;
    },
    async until(expr, what, ms = 30000) {
      const end = Date.now() + ms;
      for (;;) {
        try { const v = await b.evaluate(expr); if (v) return v; } catch { /* not yet */ }
        if (Date.now() > end) throw new Error('timed out waiting for ' + what);
        await sleep(200);
      }
    },
    textOf: sel => b.evaluate(`document.querySelector(${JSON.stringify(sel)})?.textContent || ''`),
    // a navigation as the browser's own (typed into its address bar): it carries no site of its own
    async navigate(url) { await send('browsingContext.navigate', {context, url, wait: 'complete'}); },
    // the key never goes in a URL: a one-time code from POST /door, as `daftard open` asks it, then the page by the code
    async open(query) {
      const door = await fetch(`${base}/door`, {method: 'POST', headers: {'X-Daftard-Key': key}});
      if (!door.ok) throw new Error(`the door refused the key: ${door.status}`);
      const {once} = await door.json();
      await b.navigate(`${base}/?once=${encodeURIComponent(once)}&${query}`);
    },
    // the cookies the browser keeps, each {name, domain, path, httpOnly, sameSite} — never their values
    async cookies() {
      const {cookies} = await send('storage.getCookies', {});
      return cookies.map(c => ({name: c.name, domain: c.domain, path: c.path, httpOnly: c.httpOnly, sameSite: c.sameSite}));
    },
    async shot(path) {
      const {data} = await send('browsingContext.captureScreenshot', {context});
      writeFileSync(path, Buffer.from(data, 'base64'));
    },
    async close() {
      try { await send('session.end', {}); } catch { /* ending */ }
      ws.close();
      fx.kill();
      await sleep(500);
      rmSync(profile, {recursive: true, force: true});
    },
  };
  return b;
}
