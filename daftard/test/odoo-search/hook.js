// hook — Odoo's own search tests (web/static/tests/search/), each read call they make answered by daftard
// (test/odoo-search/README.md). Evaluated in Odoo's own test page before its scripts, by run.mjs.
//
// 1. Of the test bundle, only the files of web/static/tests/search/ register tests. Every other module still loads, as
//    in Odoo's own run, since the search tests import helpers from some of them; Odoo's bundler wraps each file's body
//    in QUnit.module, so it is only test registration that is silenced.
// 2. Odoo's MockServer keeps answering what daftard does not answer (the web client's menus and actions, and writes:
//    onchange, web_save, create): those are named in the report, test by test. Each READ call daftard answers is
//    instead carried out of the page to the runner (its bridge, below), which first lays the test's own data where
//    daftard reads it — its views and fields as the garden's captures, its records as the register daftard's worker
//    reads, its favourites on the reader's own ref — and then asks daftard's Odoo origin, as Odoo's client would. What
//    daftard answers is what the test gets; a refusal is the test's server error.
(() => {
  const SEARCH = '@web/../tests/search/';
  const QUIET = ['test', 'only', 'skip', 'todo'];
  const NOOP = { test: () => {}, only: () => {}, skip: () => {}, todo: () => {} };
  const BRIDGED = new Set(['get_views', 'fields_get', 'web_search_read', 'web_read', 'read', 'search_read', 'search',
    'search_count', 'name_search', 'read_group', 'web_read_group', 'search_panel_select_range',
    'search_panel_select_multi_range']);
  const calls = (globalThis.__calls = []);
  const results = (globalThis.__results = { tests: [], done: null });
  let serial = 0, laid = null;
  // THE BRIDGE IS SYNCHRONOUS: the runner's proxy (its port in __DAFTAR_BRIDGE__) asks daftard while the page waits, so
  // the answer resolves the client's promise in the same turn as the mock server's own would. The tests were written
  // against an in-page server and await one tick after a call; what is answered is daftard's, and when is the mock's.
  const bridge = (kind, data) => {
    const x = new XMLHttpRequest();
    x.open('POST', `http://127.0.0.1:${globalThis.__DAFTAR_BRIDGE__}/bridge`, false);
    x.setRequestHeader('Content-Type', 'text/plain');
    x.send(JSON.stringify({ kind, data }));
    return JSON.parse(x.responseText);
  };

  let installed = false;
  function install() {
    if (installed || !globalThis.QUnit) return;
    installed = true;
    QUnit.testDone((d) => results.tests.push({ module: d.module, name: d.name, failed: d.failed, passed: d.passed,
      total: d.total, skipped: d.skipped, todo: d.todo }));
    QUnit.log((d) => {
      if (!d.result) {
        const t = results.tests.length;
        (results.assertions = results.assertions || []).push({ module: d.module, name: d.name, at: t,
          message: String(d.message || '').slice(0, 300), actual: String(JSON.stringify(d.actual) || '').slice(0, 300),
          expected: String(JSON.stringify(d.expected) || '').slice(0, 300), source: String(d.source || '').slice(0, 400) });
      }
    });
    QUnit.done((d) => { results.done = d; });
  }

  // the view the mock server would give for [id, type]: by its key, else the model's first of that type
  function archOf(server, model, viewId, type, context) {
    let id = viewId;
    if (!id) {
      const ref = (type === 'list' ? 'tree' : type) + '_view_ref';
      if (context && ref in context) id = context[ref];
    }
    let arch = server.archs[[model, id, type].join(',')];
    if (!arch) {
      const key = Object.keys(server.archs).find((k) => { const [m, , t] = k.split(','); return m === model && t === type; });
      if (key) arch = server.archs[key];
    }
    return arch;
  }

  function layout(server, args) {
    if (!server.__daftarSerial) server.__daftarSerial = ++serial;
    server.__daftarArchs = server.__daftarArchs || {};
    if (args.method === 'get_views') {
      const kw = args.kwargs || {};
      for (const [id, type] of kw.views || []) {
        const arch = archOf(server, args.model, id, type, kw.context || {});
        if (arch) server.__daftarArchs[`${args.model}|${type}`] = arch;
      }
    }
    const models = {}, filters = {};
    for (const [name, m] of Object.entries(server.models)) {
      models[name] = { fields: m.fields, records: m.records || [] };
      if (m.filters && m.filters.length) filters[name] = m.filters;
    }
    return { serial: server.__daftarSerial, models, archs: server.__daftarArchs, filters };
  }

  function wrapLoader(loader) {
    loader.bus.addEventListener('module-started', (ev) => {
      if (ev.detail.moduleName !== '@web/../tests/helpers/mock_server') return;
      const { MockServer, makeServerError } = ev.detail.module;
      const orig = MockServer.prototype.performRPC;
      MockServer.prototype.performRPC = async function (route, args) {
        const cur = QUnit.config.current;
        const where = { module: cur && cur.module && cur.module.name, test: cur && cur.testName };
        const method = args && args.method;
        if (!method || !BRIDGED.has(method) || !args.model || !(args.model in this.models)) {
          calls.push({ ...where, route, method, model: args && args.model, by: 'mock' });
          return orig.call(this, route, args);
        }
        args = JSON.parse(JSON.stringify(args));
        const lay = layout(this, args);
        const sig = JSON.stringify(lay);
        if (sig !== laid) {
          const r = bridge('lay', lay);
          if (r.error) throw new Error('the runner could not lay the test\'s data: ' + r.error);
          laid = sig;
        }
        const r = bridge('call', { route: `/web/dataset/call_kw/${args.model}/${method}`,
          params: { model: args.model, method, args: args.args || [], kwargs: args.kwargs || {} } });
        calls.push({ ...where, route, method, model: args.model, by: 'daftard', ok: !r.error,
          error: r.error ? String((r.error.data || {}).message || r.error.message).slice(0, 300) : undefined });
        if (r.error) {
          throw makeServerError({ message: r.error.message, description: (r.error.data || {}).message || r.error.message });
        }
        return r.result;
      };
    });
  }

  function hookOdoo(o) {
    let realDefine, realLoader;
    Object.defineProperty(o, 'define', { configurable: true, enumerable: true, get() { return realDefine && define; }, set(f) { realDefine = f; } });
    Object.defineProperty(o, 'loader', { configurable: true, enumerable: true, get() { return realLoader; }, set(l) { realLoader = l; wrapLoader(l); } });
    function define(name, deps, body) {
      install();
      if (globalThis.QUnit && !name.startsWith(SEARCH)) {
        const f = body;
        body = (req) => {
          const keep = {};
          for (const k of QUIET) { keep[k] = QUnit[k]; QUnit[k] = NOOP[k]; }
          try { return f(req); } finally { for (const k of QUIET) { if (QUnit[k] === NOOP[k]) QUnit[k] = keep[k]; } }
        };
      }
      return realDefine(name, deps, body);
    }
  }
  const cur = {};
  hookOdoo(cur);
  Object.defineProperty(globalThis, 'odoo', { configurable: true, get() { return cur; }, set(v) { if (v !== cur) Object.assign(cur, v); } });
})();
