#!/usr/bin/env python3
"""The `view` asset's adapter for a monitor that runs Prometheus — one adapter among siblings, chosen because the
monitor's own `knowledge` says it `uses` the technology this file is named for. Another technology is read by the
adapter named for it, beside this one.

WHAT IT READS. A binding's query for this technology (`view_bindings.query`, `technology: prometheus`), in PromQL: in
it, `$F` stands for the viewer's scope, which the served page fills in — the page never sends a query of its own. A
live-state is whether a being answers the probes its monitor runs against it. What the monitor watches is its own
`reaches` and each target's own `endpoints`: a reach over a protocol probes every endpoint of that protocol the target
states, or, where it states none, the address the page's reference chooses for it on the protocol's default ports; a
reach that has neither is not probed, and `dmview check` says so.

WHAT ONLY THIS TECHNOLOGY NEEDS — its alert rules and where their mail goes, the credentials an SNMP read names, a
filesystem read over the monitor's own ssh access, the Grafana plugins its pages need — sits in the monitor's own record
where the page's `view_monitors.settings` points, read here as stated, and checked by nothing but this adapter until a
term of the law carries it:

    { alerts: [ { name, expr, for, severity, summary } ],
      alerting: { email_to, email_from, smarthost, repeat },
      snmp: { env_file, auths: { <name>: { community_env, version } }, modules: { <being>: [ { modules: [...], auth, org } ] } },
      filesystems: [ { being, user, path } ],
      grafana_plugins: [ "<plugin>@<version>" ] }

A secret is only ever an environment variable's NAME here; its value lives in the host's own file, never in the
bundle, the page or the ledger.

THE BUNDLE (`dmview bundle --out DIR`): a Prometheus + Grafana deployment written from the ledger — the probe targets,
each labelled with its being, its genos and the organisation it belongs to where one can be derived; one Grafana page
per drawing, the drawing itself mounted by the same runtime; the alert rules. It opens no network path; `values` and
`history` do, to the monitor's own address, which the host's configuration gives.
"""
import json, os, re, urllib.parse, urllib.request

import view_model as vm
import view_kit as kit

TECHNOLOGY = "prometheus"
PROBES = 'job=~"blackbox-.*"'           # every probe the monitor runs against a being
MODULES = {"icmp": "icmp", "tcp": "tcp_connect", "http": "http_2xx", "smtp": "smtp_banner", "tls": "http_2xx"}
_KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


# ---------------------------------------------------------------------------------------------------------------------
# queries
# ---------------------------------------------------------------------------------------------------------------------
def selector(scope=None):
    """The viewer's scope as a label selector: every organisation (None), or those named, and with `shared` the series
    of beings no organisation can be derived for, which carry no `org` label."""
    if scope is None:
        return 'org=~".*"'
    orgs = sorted(o for o in scope.get("orgs") or [] if _KEBAB.match(str(o)))
    alts = orgs + ([""] if scope.get("shared") else [])
    return 'org=~"(%s)"' % "|".join(alts) if alts else 'org="-"'


def query(b, sel=None):
    if b.get("live") == "live-state":
        return 'min(probe_success{name="%s", %s})' % (b.get("probe"), PROBES)
    says = (b.get("query") or {}).get(TECHNOLOGY)
    return str(says).replace("$F", sel or selector()) if says is not None else None


def describe(b):
    """The path to a shown number: the query that computes it, as the page states it."""
    return query(b, "$F") or ""


def check_binding(b):
    out = []
    if b.get("live") != "live-state":
        says = (b.get("query") or {}).get(TECHNOLOGY)
        if not isinstance(says, str) or not says.strip():
            out.append("its %s query is not a text of PromQL" % TECHNOLOGY)
        if b.get("live") == "live-series" and not isinstance((b.get("items_by") or {}).get(TECHNOLOGY), str):
            out.append("a live-series read by %s names the label that tells its items apart (`items_by`)" % TECHNOLOGY)
    return out


def _get(url, timeout):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.load(r)


def values(url, binds, sel=None):
    """{binding id: number | [{name, value}] | None} — each binding asked of the monitor at `url`, now."""
    out = {}
    for b in binds:
        q = query(b, sel)
        try:
            r = _get(url.rstrip("/") + "/api/v1/query?" + urllib.parse.urlencode({"query": q}), 5)
            res = (r.get("data") or {}).get("result") or []
            if b.get("live") == "live-series":
                lab = (b.get("items_by") or {}).get(TECHNOLOGY)
                out[b["id"]] = [{"name": x["metric"].get(lab, "?"), "value": float(x["value"][1])} for x in res]
            else:
                out[b["id"]] = float(res[0]["value"][1]) if res else None
        except Exception:
            out[b["id"]] = None
    return out


def history(url, binds, sel, hours, step, now):
    """{binding id: [[t, v], …]} — each live-value binding over the window, asked of the monitor at `url`."""
    out = {}
    for b in binds:
        if b.get("live") != "live-value":
            continue
        try:
            r = _get(url.rstrip("/") + "/api/v1/query_range?" + urllib.parse.urlencode(
                {"query": query(b, sel), "start": now - hours * 3600, "end": now, "step": step}), 8)
            res = (r.get("data") or {}).get("result") or []
            out[b["id"]] = [[int(float(t)), float(x)] for t, x in res[0]["values"]] if res else []
        except Exception:
            out[b["id"]] = []
    return out


def alerts(settings, beans, binds):
    """The alert rules the monitor's settings state that concern a drawing: a rule naming one of its beings, or a
    metric one of its bindings reads."""
    rules = (settings or {}).get("alerts") if isinstance(settings, dict) else None
    metrics = set()
    for b in binds:
        metrics |= set(re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*(?=\{)", str((b.get("query") or {}).get(TECHNOLOGY) or "")))
    out = []
    for a in rules or []:
        if not isinstance(a, dict):
            continue
        ex = str(a.get("expr", ""))
        if any(re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(b), ex) for b in beans) or any(m in ex for m in metrics):
            out.append(a.get("name"))
    return out


# ---------------------------------------------------------------------------------------------------------------------
# what the monitor probes: its reaches, each target's endpoints
# ---------------------------------------------------------------------------------------------------------------------
def protocol(p):
    return next((r for r in vm.registry("net_protocols") if r.get("protocol") == p), {})


def labels(b):
    lb = {"name": b, "genos": str(vm.fm(b).get("genos") or ""), "role": vm.role(b).replace("'", "").replace('"', "")}
    o = vm.org_of(b)
    if o:
        lb["org"] = o
    return lb


def primary(b):
    return vm.address(b, vm.reference_row(b).get("system") or "ipv4") or vm.address(b, "ipv4") or vm.address(b, "ipv6")


def targets(m):
    """({module: [file_sd group]}, [(being, protocol, why not probed)]) for one monitor."""
    groups = {k: [] for k in ("icmp", "tcp", "http", "smtp", "tls", "fs")}
    parked = []
    for key, r in (m.get("reaches") or {}).items():
        p, t = r.get("protocol"), (r.get("to") or {}).get("bean")
        if not t or not vm.fm(t):
            parked.append((t or key, p, "the reach names no being of the garden")); continue
        if p == "snmp":
            continue                                   # read by the SNMP exporter's jobs, below
        lb = labels(t)
        if p == "icmp":
            a = primary(t)
            if a:
                groups["icmp"].append({"targets": [a], "labels": dict(lb)})
            else:
                parked.append((t, p, "it states no address"))
            continue
        row = protocol(p)
        eps = [(str(e.get("at")), str(e.get("port")), e.get("confidentiality") == "encrypted")
               for e in (vm.fm(t).get("endpoints") or [])
               if isinstance(e, dict) and e.get("protocol") == p and e.get("at") and e.get("port")]
        if not eps:
            a = primary(t)
            eps = [(a, str(port), p == "http" and int(port) == 443) for port in (row.get("default_ports") or [])] if a else []
        if not eps:
            parked.append((t, p, "it states no endpoint of %s, nor an address to probe on a default port" % p)); continue
        transport = row.get("transport") or row.get("protocol")
        for at, port, enc in eps:
            host = "[%s]" % at if ":" in at else at
            if p == "http":
                groups["http"].append({"targets": ["%s://%s:%s/" % ("https" if enc else "http", host, port)],
                                       "labels": dict(lb, port=port)})
                if enc:
                    groups["tls"].append({"targets": ["https://%s:%s/" % (host, port)], "labels": dict(lb, port=port)})
            elif p == "smtp":
                groups["smtp"].append({"targets": ["%s:%s" % (host, port)], "labels": dict(lb, port=port)})
            elif transport == "tcp":
                groups["tcp"].append({"targets": ["%s:%s" % (host, port)], "labels": dict(lb, port=port, protocol=p)})
            else:
                parked.append((t, p, "a probe of a %s port is not one this adapter writes" % transport))
    st = m.get("settings") if isinstance(m.get("settings"), dict) else {}
    for f in st.get("filesystems") or []:
        if not isinstance(f, dict):
            continue
        b, a = f.get("being"), primary(f.get("being"))
        if not a or not f.get("user") or not f.get("path"):
            parked.append((b, "ssh", "a filesystem read needs the being's address, a user and a path")); continue
        groups["fs"].append({"targets": ["%s@%s:%s" % (f["user"], a, f["path"])], "labels": dict(labels(b), mount=f["path"]),
                             "ssh": "%s@%s" % (f["user"], a), "path": f["path"]})
    return groups, parked


def check_monitor(m):
    """(errors, warnings) of what the adapter reads: a reach it cannot probe is said, never dropped in silence."""
    errs, warns = [], []
    _g, parked = targets(m)
    for b, p, why in parked:
        warns.append("reaches %s over %s, and does not probe it: %s" % (b, p, why))
    st = m.get("settings")
    if st is not None and not isinstance(st, dict):
        errs.append("its settings are not a mapping of what %s reads (alerts, alerting, snmp, filesystems, "
                    "grafana_plugins)" % TECHNOLOGY)
    return errs, warns


# ---------------------------------------------------------------------------------------------------------------------
# the bundle
# ---------------------------------------------------------------------------------------------------------------------
PROM_YML = """# WRITTEN by `dmview bundle` from the garden's ledger — do not edit it here; write it again.
global:
  scrape_interval: 30s
  scrape_timeout: 10s
  external_labels: {garden: %(garden)s, source: daftar}

scrape_configs:
  - job_name: prometheus
    static_configs: [{targets: ['localhost:9090']}]

  - job_name: node
    honor_labels: true      # a textfile value about another being (a filesystem read over ssh) keeps that being's labels
    static_configs: [{targets: ['host.docker.internal:9100'], labels: %(host)s}]

%(jobs)s%(alerting)s"""

BLACKBOX_JOB = """  - job_name: blackbox-%(mod)s
    metrics_path: /probe
    params: {module: [%(bbmod)s]}
    file_sd_configs: [{files: ['/etc/prometheus/targets/%(mod)s.json'], refresh_interval: 60s}]
    relabel_configs:
      - {source_labels: [__address__], target_label: __param_target}
      - {source_labels: [__param_target], target_label: instance}
      - {target_label: __address__, replacement: 'blackbox:9115'}
"""

BLACKBOX_YML = """# blackbox_exporter modules
modules:
  icmp:        {prober: icmp,  timeout: 5s, icmp: {preferred_ip_protocol: ip4}}
  tcp_connect: {prober: tcp,   timeout: 5s}
  smtp_banner: {prober: tcp,   timeout: 5s, tcp: {query_response: [{expect: '^220'}]}}
  http_2xx:    {prober: http,  timeout: 8s, http: {valid_status_codes: [200,301,302,401,403], fail_if_not_ssl: false, tls_config: {insecure_skip_verify: true}, preferred_ip_protocol: ip4}}
"""

COMPOSE = """# WRITTEN by `dmview bundle` — deploy: docker compose up -d ; take down: docker compose down
name: %(project)s
services:
  prometheus:
    image: prom/prometheus:latest
    restart: unless-stopped
    command: ['--config.file=/etc/prometheus/prometheus.yml',
              '--storage.tsdb.path=/prometheus',
              '--storage.tsdb.retention.time=30d',
              '--web.listen-address=0.0.0.0:9090',
              '--web.enable-lifecycle']
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./targets:/etc/prometheus/targets:ro
      - ./rules:/etc/prometheus/rules:ro
      - promdata:/prometheus
    ports: ['9090:9090']
    extra_hosts: ['host.docker.internal:host-gateway']
    mem_limit: 4g
  node-exporter:
    image: prom/node-exporter:latest
    restart: unless-stopped
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--path.rootfs=/host/root'
      - '--collector.textfile.directory=/textfile'
    pid: host
    network_mode: host
    volumes:
      - '/proc:/host/proc:ro'
      - '/sys:/host/sys:ro'
      - '/:/host/root:ro'
      - '%(dir)s/textfile-out:/textfile:ro'
    mem_limit: 512m
  blackbox:
    image: prom/blackbox-exporter:latest
    restart: unless-stopped
    command: ['--config.file=/etc/blackbox.yml']
    volumes: ['./blackbox.yml:/etc/blackbox.yml:ro']
    ports: ['9115:9115']
    cap_add: ['NET_RAW']   # icmp
    mem_limit: 256m
  grafana:
    image: grafana/grafana:latest
    restart: unless-stopped
    env_file: [.env]
    environment:
      - GF_AUTH_ANONYMOUS_ENABLED=false
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_USERS_DEFAULT_THEME=dark
      - GF_PLUGINS_PREINSTALL_SYNC=%(plugins)s
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
      - ./grafana/dashboards:/var/lib/grafana/dashboards:ro
      - grafanadata:/var/lib/grafana
    ports: ['3000:3000']
    mem_limit: 4g   # a limit is a backstop, not a budget
%(extra)svolumes:
  promdata: {}
  grafanadata: {}
"""

README = """# Prometheus and Grafana, written by dmview from the garden's ledger

WRITTEN by `dmview bundle`. Write it again after the ledger changes; it overwrites every file it wrote here. Change the
SOURCE — the page, the monitor's record and its settings, or the garden's drawings — never these files. `.env` (the
Grafana sign-in) belongs to this host and is never written here.

## Deploy
    cd %(dir)s && docker compose up -d && curl -s -X POST localhost:9090/-/reload

## Pages
- view-index: one card per drawing, the drawing → its patterns → its page, every probed being, certificates.
- view-<drawing>: the drawing with its live values on its own elements; `lens` chooses the lens; `org` and `genos` narrow
  what it shows to the organisations chosen.
"""

GRAF_DS = """apiVersion: 1
datasources:
  - name: Prometheus
    uid: prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
"""
GRAF_PROVIDER = """apiVersion: 1
providers:
  - name: view
    orgId: 1
    folder: %(folder)s
    type: file
    disableDeletion: false
    options: {path: /var/lib/grafana/dashboards}
"""
DS = {"type": "prometheus", "uid": "prometheus"}
FSEL = 'org=~"$org", genos=~"$genos"'


def _templating(default_org):
    lst = []
    for f in ("org", "genos"):
        cur = default_org if f == "org" else None
        lst.append({"name": f, "label": f, "type": "query", "datasource": DS,
                    "query": {"query": "label_values(%s)" % f, "refId": f}, "refresh": 1, "sort": 1,
                    "includeAll": True, "allValue": ".*", "multi": True,
                    "current": ({"text": cur, "value": cur} if cur else {"text": "All", "value": "$__all"})})
    lv = vm.lenses()
    cur = next((l for l in lv if l.get("form") == "health-chain"), lv[0] if lv else {"id": "operate", "depth": 2, "name": "operate"})
    lst.append({"name": "lens", "label": "lens", "type": "custom",
                "query": ",".join("%s · %s : %s" % (l["depth"], l["name"], l["id"]) for l in lv),
                "options": [{"text": "%s · %s" % (l["depth"], l["name"]), "value": l["id"], "selected": l is cur} for l in lv],
                "current": {"text": "%s · %s" % (cur["depth"], cur["name"]), "value": cur["id"]}, "hide": 0})
    return {"list": lst}


STATE_MAP = [{"type": "value", "options": {"0": {"text": "DOWN", "color": "red", "index": 0},
                                           "1": {"text": "up", "color": "green", "index": 1}}}]


def _steps(b):
    st = [{"color": "green", "value": None}]
    if b.get("warn") is not None:
        st.append({"color": "orange", "value": b["warn"]})
    if b.get("crit") is not None:
        st.append({"color": "red", "value": b["crit"]})
    return {"mode": "absolute", "steps": st}


def _links():
    return [{"title": "Drawings", "type": "dashboards", "tags": ["view-drawing"], "asDropdown": True,
             "includeVars": True, "keepTime": True},
            {"title": "index", "type": "link", "url": "/d/view-index", "includeVars": True, "keepTime": True, "icon": "dashboard"}]


GLUE = r"""
const root = context.element.querySelector('.vwroot') || context.element;
if (!document.getElementById('vw-style')) { const st = document.createElement('style'); st.id = 'vw-style'; st.textContent = CSS; document.head.appendChild(st); }
const vals = {}, SER = {};
(VIEW.binds || []).forEach(b => { if (b.live === 'live-series') SER[b.id] = ITEMS[b.id]; });
for (const s of ((context.panelData && context.panelData.series) || [])) {
  const f = (s.fields || []).find(x => x.type === 'number');
  if (!f || !f.values.length) continue;
  const v = f.values.get ? f.values.get(f.values.length - 1) : f.values[f.values.length - 1];
  if (SER[s.refId]) (vals[s.refId] = vals[s.refId] || []).push({name: (f.labels || {})[SER[s.refId]] || '?', value: v});
  else vals[s.refId] = v;
}
const lens = context.grafana.replaceVariables('$lens');
const isDark = !(context.grafana.theme && context.grafana.theme.isLight);
root.classList.toggle('light', !isDark);
window.viewMount(root, VIEW, {level: lens, live: true, values: vals});
"""

VIEW_KEYS = ("key", "title", "claim", "caption", "rel", "svg", "elements", "binds", "facts", "steps", "legend", "source",
             "levels", "story", "tiles", "parts", "actions", "uid", "patternMeaning", "alerts", "questions", "operate",
             "wiring", "window")


def _panel(view, y, h):
    items = {b["id"]: (b.get("items_by") or {}).get(TECHNOLOGY) for b in view["binds"] if b.get("live") == "live-series"}
    code = ("const VIEW = %s;\nconst ITEMS = %s;\nconst CSS = %s;\n%s\n%s" %
            (json.dumps({k: view[k] for k in VIEW_KEYS}, ensure_ascii=False), json.dumps(items),
             json.dumps(kit.SCHEMA_CSS), kit.RUNTIME_JS, GLUE))
    ours = [b for b in view["binds"] if b.get("technology") == TECHNOLOGY]
    return {"type": "marcusolsson-dynamictext-panel", "title": "", "transparent": True,
            "gridPos": {"x": 0, "y": y, "w": 24, "h": h}, "datasource": DS,
            "targets": [dict({"expr": query(b, FSEL), "refId": b["id"], "instant": True},
                             **({"legendFormat": "{{%s}}" % items[b["id"]]} if b.get("live") == "live-series" else {}))
                        for b in ours],
            "options": {"renderMode": "data", "content": '<div class="vwroot"></div>',
                        "defaultContent": '<div class="vwroot"></div>', "afterRender": code,
                        "helpers": "", "styles": "", "wrap": False, "editors": ["afterRender"]}}


def drawing_dashboard(view, default_org, folder):
    vw, vh = [float(x) for x in view["svg"].split('viewBox="0 0 ')[1].split('"')[0].split()]
    h = round((1740 * vh / vw + 260) / 38) + 1
    states = [b for b in view["binds"] if b["live"] == "live-state" and b.get("technology") == TECHNOLOGY]
    values_ = [b for b in view["binds"] if b["live"] == "live-value" and b.get("technology") == TECHNOLOGY]
    names = "|".join(sorted({b["probe"] for b in states})) or "none"
    by_el = 'min by (name) (probe_success{name=~"%s", %s, %s})' % (names, PROBES, FSEL)
    panels = [_panel(view, 0, h)]
    y = h
    kpis = [
        {"type": "stat", "title": "bound parts up", "gridPos": {"x": 0, "y": y, "w": 4, "h": 4}, "datasource": DS,
         "targets": [{"expr": "count(%s == 1) or vector(0)" % by_el, "refId": "A"}],
         "fieldConfig": {"defaults": {"color": {"mode": "fixed", "fixedColor": "green"}}}, "options": {"graphMode": "none"}},
        {"type": "stat", "title": "bound parts down", "gridPos": {"x": 4, "y": y, "w": 4, "h": 4}, "datasource": DS,
         "targets": [{"expr": "count(%s == 0) or vector(0)" % by_el, "refId": "A"}],
         "fieldConfig": {"defaults": {"thresholds": {"mode": "absolute", "steps": [{"color": "green", "value": None}, {"color": "red", "value": 1}]}}},
         "options": {"graphMode": "none", "colorMode": "background"}}]
    for i, b in enumerate(values_):
        kpis.append({"type": "stat", "title": b["name"], "gridPos": {"x": 8 + 5 * (i % 3), "y": y + 4 * (i // 3), "w": 5, "h": 4},
                     "datasource": DS, "targets": [{"expr": query(b, FSEL), "refId": "A"}],
                     "fieldConfig": {"defaults": {"decimals": 1, "thresholds": _steps(b)}}, "options": {"graphMode": "area"}})
    panels += kpis
    y += 4 * max(1, (len(values_) + 2) // 3)
    hist = [{"type": "state-timeline", "title": "Bound parts over time", "gridPos": {"x": 0, "y": y + 1, "w": 24, "h": 3 + 2 * len(states)},
             "datasource": DS, "targets": [{"expr": by_el, "legendFormat": "{{name}}", "refId": "A"}],
             "fieldConfig": {"defaults": {"mappings": STATE_MAP}}}]
    for i, b in enumerate(values_):
        hist.append({"type": "timeseries", "title": b["name"], "gridPos": {"x": 12 * (i % 2), "y": y + 4 + 2 * len(states) + 8 * (i // 2), "w": 12, "h": 8},
                     "datasource": DS, "targets": [{"expr": query(b, FSEL), "legendFormat": b["name"], "refId": "A"}],
                     "fieldConfig": {"defaults": {"thresholds": _steps(b), "custom": {"thresholdsStyle": {"mode": "line"}}}}})
    panels.append({"type": "row", "title": "History", "collapsed": True, "gridPos": {"x": 0, "y": y, "w": 24, "h": 1}, "panels": hist})
    return {"title": "%s — %s" % (kit.esc(view["title"]).replace("&amp;", "&"), folder), "uid": view["uid"], "schemaVersion": 39,
            "version": 1, "refresh": "30s", "time": {"from": "now-6h", "to": "now"}, "editable": False,
            "tags": ["view", "view-drawing", view["key"]], "links": _links(), "templating": _templating(default_org),
            "description": "The drawing of %s, written by dmview from the garden's ledger; do not edit it here." % view["source"],
            "panels": panels}


def index_dashboard(views, default_org, folder):
    panels = [{"type": "text", "title": "", "gridPos": {"x": 0, "y": 0, "w": 24, "h": 2},
               "options": {"mode": "markdown", "content": "### %s\nEach card is one drawing: open it to see the drawing with "
                                                          "the live values on its own parts. Green: every bound part is up." % folder}}]
    for i, v in enumerate(views):
        names = "|".join(sorted({b["probe"] for b in v["binds"] if b["live"] == "live-state"})) or "none"
        panels.append({"type": "stat", "title": v["title"].replace("&amp;", "&"),
                       "gridPos": {"x": (i % 4) * 6, "y": 2 + (i // 4) * 4, "w": 6, "h": 4}, "datasource": DS,
                       "targets": [{"expr": 'min(min by (name) (probe_success{name=~"%s", %s, %s}))' % (names, PROBES, FSEL), "refId": "A"}],
                       "links": [{"title": "open the drawing's page", "url": "/d/%s?${__url_time_range}&${__all_variables}" % v["uid"]}],
                       "fieldConfig": {"defaults": {"mappings": [{"type": "value", "options": {
                           "0": {"text": "a part is down", "color": "red"}, "1": {"text": "all up", "color": "green"}}}],
                           "noValue": "no data in this scope", "color": {"mode": "thresholds"},
                           "thresholds": {"mode": "absolute", "steps": [{"color": "#5a6675", "value": None}]}}},
                       "options": {"colorMode": "background", "graphMode": "none", "textMode": "value"}})
    y = 2 + ((len(views) + 3) // 4) * 4
    rows = "".join("| [%s](/d/%s) | %s | %s | %s | %d |\n" % (v["title"].replace("&amp;", "&"), v["uid"], v["source"],
                   ", ".join(v["patterns"]), ", ".join(v["live_patterns"]), len(v["binds"])) for v in views)
    panels.append({"type": "text", "title": "The drawing → its patterns → its page", "gridPos": {"x": 0, "y": y, "w": 24, "h": 2 + len(views)},
                   "options": {"mode": "markdown", "content": "| page | draws | drawn with | live | bindings |\n|---|---|---|---|---|\n" + rows}})
    y += 2 + len(views)
    panels.append({"type": "state-timeline", "title": "Every probed being — answering any probe",
                   "gridPos": {"x": 0, "y": y, "w": 24, "h": 12}, "datasource": DS,
                   "targets": [{"expr": 'max by (name) (probe_success{%s, %s})' % (PROBES, FSEL), "legendFormat": "{{name}}", "refId": "A"}],
                   "fieldConfig": {"defaults": {"mappings": STATE_MAP}}})
    panels.append({"type": "table", "title": "Days until a certificate lapses", "gridPos": {"x": 0, "y": y + 12, "w": 24, "h": 6},
                   "datasource": DS, "targets": [{"expr": '(probe_ssl_earliest_cert_expiry{%s} - time()) / 86400' % FSEL, "format": "table", "instant": True, "refId": "A"}],
                   "transformations": [{"id": "organize", "options": {
                       "excludeByName": {"Time": True, "__name__": True, "instance": True, "job": True, "genos": True, "role": True, "port": True},
                       "renameByName": {"Value": "days left"}}}, {"id": "sortBy", "options": {"sort": [{"field": "days left"}]}}],
                   "fieldConfig": {"defaults": {"decimals": 0}, "overrides": [{"matcher": {"id": "byName", "options": "days left"}, "properties": [
                       {"id": "custom.cellOptions", "value": {"type": "color-background"}},
                       {"id": "thresholds", "value": {"mode": "absolute", "steps": [{"color": "red", "value": None}, {"color": "orange", "value": 15}, {"color": "green", "value": 30}]}}]}]}})
    t = _templating(default_org)
    t["list"] = [x for x in t["list"] if x["name"] != "lens"]
    return {"title": folder, "uid": "view-index", "schemaVersion": 39, "version": 1, "refresh": "30s",
            "time": {"from": "now-6h", "to": "now"}, "editable": False, "tags": ["view"], "links": _links(),
            "templating": t, "panels": panels}


REMOTE_FS = r"""#!/bin/sh
# WRITTEN by `dmview bundle` from the ledger — a filesystem's size and free space, read with `df` over the ssh access
# this host already has; nothing runs on the being but `df`. Run it from the stack user's crontab, every few minutes:
#   */5 * * * * {dir}/textfile/remote_fs.sh
OUT={dir}/textfile-out
mkdir -p "$OUT"; TMP="$OUT/remote_fs.prom.$$"
{
echo '# HELP remote_fs_size_bytes Size of a filesystem of another being, read with df over ssh'
echo '# TYPE remote_fs_size_bytes gauge'
echo '# HELP remote_fs_avail_bytes Free space of a filesystem of another being, read with df over ssh'
echo '# TYPE remote_fs_avail_bytes gauge'
echo '# HELP remote_fs_up 1 when the last read succeeded'
echo '# TYPE remote_fs_up gauge'
%(entries)s
} > "$TMP" && mv "$TMP" "$OUT/remote_fs.prom"
"""
REMOTE_FS_ENTRY = r"""L='%(labels)s'
if R=$(ssh -o BatchMode=yes -o ConnectTimeout=8 %(ssh)s "df -kP %(path)s" 2>/dev/null | awk 'NR==2 {print $2*1024, $4*1024}') && [ -n "$R" ]; then
  set -- $R; echo "remote_fs_size_bytes{$L} $1"; echo "remote_fs_avail_bytes{$L} $2"; echo "remote_fs_up{$L} 1"
else echo "remote_fs_up{$L} 0"; fi"""


def remote_fs(groups, dirpath):
    ent = []
    for g in groups.get("fs", []):
        lab = ",".join('%s="%s"' % (k, str(v).replace('"', "")) for k, v in sorted(g["labels"].items())
                       if k in ("name", "org", "genos", "mount"))
        ent.append(REMOTE_FS_ENTRY % {"labels": lab, "ssh": g["ssh"], "path": g["path"]})
    return (REMOTE_FS % {"entries": "\n".join(ent)}).replace("{dir}", dirpath) if ent else None


SNMP_JOB = """  - job_name: snmp-%(bean)s-%(tag)s
    scrape_interval: 60s
    scrape_timeout: 50s
    metrics_path: /snmp
    params: {module: [%(modules)s], auth: [%(auth)s]}
    static_configs: [{targets: ['%(addr)s'], labels: %(labels)s}]
    relabel_configs:
      - {source_labels: [__address__], target_label: __param_target}
      - {source_labels: [__param_target], target_label: instance}
      - {target_label: __address__, replacement: 'snmp-exporter:9116'}
"""


def _flow_labels(lb):
    return "{" + ", ".join("%s: '%s'" % (k, str(v).replace("'", "")) for k, v in lb.items()) + "}"


def snmp_parts(m):
    """(scrape jobs, entry script, compose service) for the beings the monitor reaches over SNMP. A secret is only ever
    an environment variable's NAME: the container writes its auth file at start from the host's own file, in its own
    /tmp, so the value never enters the bundle, git or the ledger."""
    st = m.get("settings") if isinstance(m.get("settings"), dict) else {}
    sn = st.get("snmp") if isinstance(st.get("snmp"), dict) else {}
    reached = [(r.get("to") or {}).get("bean") for r in (m.get("reaches") or {}).values() if r.get("protocol") == "snmp"]
    reached = [b for b in reached if b and vm.fm(b)]
    auths = sn.get("auths") if isinstance(sn.get("auths"), dict) else {}
    if not reached or not auths:
        return "", None, ""
    lines = ["#!/bin/sh",
             "# WRITTEN by `dmview bundle` — writes snmp_exporter's auth file from the host's env file (%s), then runs it."
             % sn.get("env_file", "snmp.env"), "set -e", "umask 077"]
    for _name, a in auths.items():
        lines.append('[ -n "${%s}" ] || { echo "snmp: %s is not set in the env file" >&2; exit 1; }' % (a["community_env"], a["community_env"]))
    lines += ["cat > /tmp/auth.yml <<EOF", "auths:"]
    for name, a in auths.items():
        lines += ["  %s:" % name, '    community: "${%s}"' % a["community_env"], "    version: %d" % int(a.get("version", 2))]
    lines += ["EOF", "exec /bin/snmp_exporter --config.file=/etc/snmp_exporter/snmp.yml --config.file=/tmp/auth.yml"]
    jobs = ""
    mods = sn.get("modules") if isinstance(sn.get("modules"), dict) else {}
    for b in reached:
        # one being may be read twice with different modules and organisations (a shared router's interfaces, and one
        # organisation's queues on it), so the job is named by being AND module set
        for t in mods.get(b) or [{"modules": ["if_mib"], "auth": next(iter(auths))}]:
            lb = labels(b)
            if t.get("org"):
                lb["org"] = t["org"]
            jobs += SNMP_JOB % {"bean": b, "tag": "-".join(t["modules"]).replace("_", "-"), "modules": ",".join(t["modules"]),
                                "auth": t["auth"], "addr": primary(b), "labels": _flow_labels(lb)}
    svc = """  snmp-exporter:
    image: prom/snmp-exporter:%s
    restart: unless-stopped
    entrypoint: ['/bin/sh', '/etc/snmp_exporter/entry.sh']
    volumes: ['./snmp-entry.sh:/etc/snmp_exporter/entry.sh:ro']
    env_file: [%s]      # the host's secrets (0600), never written here, never in git
    mem_limit: 256m
""" % (sn.get("image_tag", "v0.30.1"), sn.get("env_file", "snmp.env"))
    return jobs, "\n".join(lines) + "\n", svc


def alert_parts(m):
    """(prometheus.yml alerting block, rules, alertmanager.yml, compose service) from the monitor's alert rules."""
    st = m.get("settings") if isinstance(m.get("settings"), dict) else {}
    al, rules = st.get("alerting") or {}, st.get("alerts") or []
    if not rules or not al.get("email_to"):
        return "", None, None, ""
    r = "# WRITTEN by `dmview bundle` from the monitor's alert rules — change them in its record, never here\ngroups:\n  - name: view\n    rules:\n"
    for a in rules:
        r += ("      - alert: %s\n        expr: %s\n        for: %s\n        labels: {severity: %s}\n        annotations: {summary: %s}\n"
              % (a["name"], json.dumps(a["expr"]), a.get("for", "10m"), a.get("severity", "warning"), json.dumps(a.get("summary", a["name"]))))
    am = """# WRITTEN by `dmview bundle`
global:
  smtp_smarthost: '%(smarthost)s'
  smtp_from: '%(from)s'
  smtp_require_tls: false
route:
  receiver: keeper
  group_by: [alertname, name]
  group_wait: 1m
  group_interval: 10m
  repeat_interval: %(repeat)s
receivers:
  - name: keeper
    email_configs: [{to: '%(to)s', send_resolved: true}]
""" % {"smarthost": al.get("smarthost", "host.docker.internal:25"), "from": al.get("email_from", "alertmanager@localhost"),
       "to": al["email_to"], "repeat": al.get("repeat", "12h")}
    block = """
rule_files: ['/etc/prometheus/rules/*.yml']
alerting:
  alertmanagers: [{static_configs: [{targets: ['alertmanager:9093']}]}]
"""
    svc = """  alertmanager:
    image: prom/alertmanager:%s
    restart: unless-stopped
    command: ['--config.file=/etc/alertmanager/alertmanager.yml', '--storage.path=/alertmanager']
    volumes: ['./alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro', 'amdata:/alertmanager']
    extra_hosts: ['host.docker.internal:host-gateway']
    mem_limit: 256m      # no published port: only Prometheus, on the same network, talks to it
""" % al.get("image_tag", "v0.34.1")
    return block, r, am, svc


def deploy_dir(m, out):
    """Where the bundle runs: the monitor's own position in a filesystem (`located_at`), else where it is written."""
    for e in vm.fm(m["bean"]).get("located_at") or []:
        if isinstance(e, dict) and e.get("system") == "unix-filesystem" and isinstance(e.get("at"), str):
            at = e["at"]
            if not at.startswith("root:") and ":" in at:
                return at.split(":", 1)[1]
    return out


def bundle(m, views, out):
    """Write the bundle for one monitor. Returns (targets written, {module: n}, pages)."""
    groups, _parked = targets(m)
    host = (vm.fm(m["bean"]).get("lives_in") or {}).get("bean") if isinstance(vm.fm(m["bean"]).get("lives_in"), dict) else None
    dirpath = deploy_dir(m, out)
    folder = str(vm.page().get("title") or vm.PAGE)
    default_org = vm.page_view().get("opens_on")
    for sub in ("targets", "rules", "grafana/provisioning/datasources", "grafana/provisioning/dashboards", "grafana/dashboards"):
        os.makedirs(os.path.join(out, sub), exist_ok=True)
    jobs = []
    for mod in ("icmp", "tcp", "http", "smtp", "tls"):
        p = os.path.join(out, "targets", mod + ".json")
        if groups[mod]:
            json.dump(groups[mod], open(p, "w"), indent=2)
            jobs.append(BLACKBOX_JOB % {"mod": mod, "bbmod": MODULES[mod]})
        elif os.path.exists(p):
            os.remove(p)
    snmp_jobs, snmp_entry, snmp_svc = snmp_parts(m)
    al_block, rules, am, am_svc = alert_parts(m)
    for f, content in (("snmp-entry.sh", snmp_entry), ("alertmanager.yml", am), ("rules/view.yml", rules)):
        p = os.path.join(out, f)
        if content:
            open(p, "w").write(content)
        elif os.path.exists(p):
            os.remove(p)
    fs = remote_fs(groups, dirpath)
    if fs:
        os.makedirs(os.path.join(out, "textfile"), exist_ok=True)
        p = os.path.join(out, "textfile", "remote_fs.sh"); open(p, "w").write(fs); os.chmod(p, 0o755)
    open(os.path.join(out, "prometheus.yml"), "w").write(PROM_YML % {
        "garden": json.dumps(vm.garden_name()), "host": _flow_labels(labels(host)) if host else "{}",
        "jobs": "".join(jobs) + snmp_jobs, "alerting": al_block})
    open(os.path.join(out, "blackbox.yml"), "w").write(BLACKBOX_YML)
    st = m.get("settings") if isinstance(m.get("settings"), dict) else {}
    compose = COMPOSE % {"project": vm.PAGE, "dir": dirpath, "plugins": ",".join(st.get("grafana_plugins") or []),
                         "extra": snmp_svc + am_svc}
    if am_svc:
        compose = compose.replace("\nvolumes:\n  promdata: {}", "\nvolumes:\n  promdata: {}\n  amdata: {}")
    open(os.path.join(out, "docker-compose.yml"), "w").write(compose)
    open(os.path.join(out, "grafana/provisioning/datasources/prometheus.yml"), "w").write(GRAF_DS)
    open(os.path.join(out, "grafana/provisioning/dashboards/view.yml"), "w").write(GRAF_PROVIDER % {"folder": json.dumps(folder)})
    db = os.path.join(out, "grafana/dashboards")
    written = {"view-%s.json" % v["key"] for v in views} | {"view-index.json"}
    for f in os.listdir(db):
        if f.startswith("view-") and f.endswith(".json") and f not in written:
            os.remove(os.path.join(db, f))            # a drawing the page no longer lists leaves the bundle with it
    for v in views:
        json.dump(drawing_dashboard(v, default_org, folder), open(os.path.join(db, "view-%s.json" % v["key"]), "w"),
                  indent=1, ensure_ascii=False)
    json.dump(index_dashboard(views, default_org, folder), open(os.path.join(db, "view-index.json"), "w"), indent=1, ensure_ascii=False)
    for rel, (content, mode) in (getattr(vm.garden(), "DEPLOY_FILES", {}) or {}).items():
        p = os.path.join(out, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w").write(content.replace("{dir}", dirpath)); os.chmod(p, mode)
    open(os.path.join(out, "README.md"), "w").write(README % {"dir": dirpath})
    return sum(len(v) for v in groups.values()), {k: len(v) for k, v in groups.items() if v}, len(views)
