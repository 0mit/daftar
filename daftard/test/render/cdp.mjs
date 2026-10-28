// cdp — headless Chromium driven over the DevTools protocol, with Node's own WebSocket (no packages): what the
// render tests click the handplace with. `const b = await browser({base, key})`, then b.open(query), b.click(sel),
// b.fill(sel, value), b.until(expr, what), b.evaluate(expr), b.textOf(sel), b.shot(path), b.exceptions, b.logs,
// and b.close().
import { spawn } from 'node:child_process';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

export async function browser({base, key, width = 1400, height = 1000}) {
  const profile = mkdtempSync(join(tmpdir(), 'cdp-'));
  const chrome = spawn('chromium', ['--headless=new', '--disable-gpu', '--no-sandbox', '--remote-debugging-port=0',
    `--user-data-dir=${profile}`, `--window-size=${width},${height}`, 'about:blank'], {stdio: ['ignore', 'ignore', 'pipe']});
  const wsUrl = await new Promise((ok, no) => {
    let err = '';
    chrome.stderr.on('data', d => { err += d; const m = /DevTools listening on (ws:\/\/\S+)/.exec(err); if (m) ok(m[1]); });
    setTimeout(() => no(new Error('chromium did not start: ' + err)), 20000);
  });
  const ws = new WebSocket(wsUrl);
  await new Promise(ok => ws.addEventListener('open', ok, {once: true}));
  let seq = 0;
  const waiting = new Map(), exceptions = [], logs = [];
  ws.addEventListener('message', ev => {
    const m = JSON.parse(ev.data);
    if (m.id && waiting.has(m.id)) { const {ok, no} = waiting.get(m.id); waiting.delete(m.id); m.error ? no(new Error(m.error.message)) : ok(m.result); }
    if (m.method === 'Runtime.exceptionThrown') exceptions.push(m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text);
    if (m.method === 'Runtime.consoleAPICalled') logs.push(m.params.args.map(a => a.value ?? a.description ?? '').join(' '));
  });
  const send = (method, params = {}, sessionId) => new Promise((ok, no) => {
    const id = ++seq; waiting.set(id, {ok, no}); ws.send(JSON.stringify({id, method, params, sessionId}));
  });
  const {targetId} = await send('Target.createTarget', {url: 'about:blank'});
  const {sessionId} = await send('Target.attachToTarget', {targetId, flatten: true});
  const S = (method, params) => send(method, params, sessionId);
  await S('Page.enable'); await S('Runtime.enable');
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const b = {
    exceptions, logs, sleep,
    async evaluate(expr) {
      const r = await S('Runtime.evaluate', {expression: expr, awaitPromise: true, returnByValue: true});
      if (r.exceptionDetails) throw new Error(expr + ': ' + (r.exceptionDetails.exception?.description || r.exceptionDetails.text));
      return r.result.value;
    },
    async until(expr, what, ms = 60000) {
      const end = Date.now() + ms;
      for (;;) {
        try { const v = await b.evaluate(expr); if (v) return v; } catch { /* not yet */ }
        if (Date.now() > end) throw new Error('timed out waiting for ' + what);
        await sleep(200);
      }
    },
    ready: () => b.until(`document.getElementById('content')?.getAttribute('aria-busy') === 'false'`, 'the page to render'),
    click: sel => b.evaluate(`(() => { const e = document.querySelector(${JSON.stringify(sel)}); if (!e) throw new Error('no ' + ${JSON.stringify(sel)}); e.click(); return true; })()`),
    fill: (sel, value) => b.evaluate(`(() => { const e = document.querySelector(${JSON.stringify(sel)}); if (!e) throw new Error('no ' + ${JSON.stringify(sel)}); e.value = ${JSON.stringify(value)}; e.dispatchEvent(new Event('input', {bubbles: true})); e.dispatchEvent(new Event('change', {bubbles: true})); return true; })()`),
    textOf: sel => b.evaluate(`document.querySelector(${JSON.stringify(sel)})?.textContent || ''`),
    // the key never goes in a URL (security audit 2.2): a one-time code is asked of POST /door with the key in a
    // header, as `daftard open` does, and the code's redirect sets the cookie and lands on `to`, or on / with the
    // switches given
    async open(query) {
      const door = await fetch(`${base}/door`, {method: 'POST', headers: {'X-Daftard-Key': key}});
      if (!door.ok) throw new Error(`the door refused the key: ${door.status}`);
      const {once} = await door.json();
      await b.evaluate('window.__before = true');
      await S('Page.navigate', {url: `${base}/?once=${encodeURIComponent(once)}&${query}`});
      await b.until(`!window.__before && document.readyState === 'complete'`, 'the page to load');
      await b.ready();
    },
    // go to a URL as the browser's own navigation does (Sec-Fetch-Site: none), and wait for nothing
    async navigate(url) { await S('Page.navigate', {url}); },
    // a page of the new handplace by its id (#id), events off
    async page(id, extra = '') { await b.open(`static=1${extra}`); await b.evaluate(`location.hash = ${JSON.stringify(id)}`); await b.sleep(100); await b.ready(); },
    // a phone's width (mobile: its layout viewport grows to fit what overflows, as a phone's does); mobile false keeps it
    async viewport(w, h, mobile = w < 700) { await S('Emulation.setDeviceMetricsOverride', {width: w, height: h, deviceScaleFactor: 1, mobile}); },
    async shot(path, full = true) {
      const r = await S('Page.captureScreenshot', {format: 'png', captureBeyondViewport: full});
      writeFileSync(path, Buffer.from(r.data, 'base64'));
    },
    async close() { ws.close(); chrome.kill(); await sleep(300); rmSync(profile, {recursive: true, force: true}); },
  };
  return b;
}
