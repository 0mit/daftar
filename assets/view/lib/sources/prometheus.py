#!/usr/bin/env python3
"""The `view` asset's adapter for a monitor that runs Prometheus — one adapter among siblings, chosen because the
monitor's own `knowledge` says it `uses` the technology this file is named for. Another technology is read by the
adapter named for it, beside this one.

WHAT IT READS. A binding's query for this technology (`view_bindings.query`, `technology: prometheus`), in PromQL: in
it, `$F` stands for the viewer's scope, which the served page fills in — the page never sends a query of its own. A
live-state is whether a being answers the probes its monitor runs against it. What the monitor watches is its own
`reaches` and each target's own `endpoints`: a reach over a protocol probes every endpoint of that protocol the target
states, or, where it states none, the address the page's reference chooses for it on the protocol's default ports; a
reach that has neither is not probed, and `view check` says so. An http endpoint at a `uri` is probed at it, and its
certificate too where its scheme is https. A name a probe reaches is resolved, for the probe alone, to where its serving
being stands on the LAN (`inside`, below): the blackbox service's `extra_hosts`.

WHAT ONLY THIS TECHNOLOGY NEEDS — its alert rules and where their mail goes, the credentials an SNMP read names, a
filesystem read over the monitor's own ssh access, the Grafana plugins its pages need — sits in the monitor's own record
where the page's `view_monitors.settings` points, read here as stated, and checked by nothing but this adapter until a
term of the law carries it:

    { alerts: [ { name, expr, for, severity, summary } ],
      alerting: { email_to, email_from, smarthost, repeat },
      snmp: { env_file, auths: { <name>: { community_env, version } }, modules: { <being>: [ { modules: [...], auth, org } ] } },
      filesystems: [ { being, user, path } ],
      grafana_plugins: [ "<plugin>@<version>" ],
      retention: "<a Prometheus duration: 30d>",
      image_tags: { prometheus, node-exporter, blackbox, grafana },
      mem_limits: { prometheus, node-exporter, blackbox, grafana },
      probe_timeouts: { icmp, tcp_connect, smtp_banner, http_2xx },
      tls_verify: true | false }

What the bundle deploys is the monitor's to say, each with its default (DEPLOY, below: today's values, and each image
pinned by version, so a bundle written today and one written next month run the same software, the one tested).

A secret is only ever an environment variable's NAME here; its value lives in the host's own file, never in the
bundle, the page or the ledger.

THE BUNDLE (`view bundle --out DIR`): a Prometheus + Grafana deployment written from the ledger — the probe targets,
each labelled with its being, its genos and the organisation it belongs to where one can be derived; one Grafana page
per drawing, the drawing itself mounted by the same runtime; the alert rules. It opens no network path; `values` and
`history` do, to the monitor's own address, which the host's configuration gives — each answer read within one
deadline, up to a size, and where it was asked (view_fetch), and one poll's reads within one budget.
"""
import ipaddress, json, os, re, urllib.parse

import view_fetch

import view_model as vm
import view_kit as kit

TECHNOLOGY = "prometheus"
# THE DEPLOYMENT'S DEFAULTS, each the monitor's settings may say otherwise: what is kept and for how long, each
# container's image and memory, each probe's deadline, and whether an https probe checks the certificate. An image is
# pinned by version: read 2026-10-12, each the newest release out two weeks or more, or a newer patch of its own line
# where that fixes the program's own security (Grafana 13.2.3: CVE-2026-13719, -13720, -81841). A certificate is not
# checked: a monitor probes hosts whose certificates are its own, and the tls probe reads a certificate's expiry. The
# http and tls probes share one module, so with tls_verify true the tls probe fails on a certificate it cannot verify,
# where it read the expiry before.
DEPLOY = {"retention": "30d",
          "image_tags": {"prometheus": "v3.15.0", "node-exporter": "v1.12.1", "blackbox": "v0.28.0", "grafana": "13.2.3"},
          "mem_limits": {"prometheus": "4g", "node-exporter": "512m", "blackbox": "256m", "grafana": "4g"},
          "probe_timeouts": {"icmp": "5s", "tcp_connect": "5s", "smtp_banner": "5s", "http_2xx": "8s"},
          "tls_verify": False}
# Each setting's form. An image's tag names a whole version (v3.15.0, 13.2.3), never `latest` nor a line that moves
# (`v3`, `13.2`), so the bundle runs the image that was tested
DEPLOY_FORMS = {"retention": re.compile(r"^[1-9][0-9]*(ms|s|m|h|d|w|y)$"),
                "image_tags": re.compile(r"^v?[0-9]+\.[0-9]+\.[0-9]+([-+][A-Za-z0-9_.-]+)?$"),
                "mem_limits": re.compile(r"^[1-9][0-9]*[bkmg]$"),
                "probe_timeouts": re.compile(r"^[1-9][0-9]*(ms|s)$")}


def deploy(st):
    """The deployment's settings: the monitor's where it states them, each else its default (DEPLOY)."""
    st = st if isinstance(st, dict) else {}
    out = {"retention": str(st.get("retention") or DEPLOY["retention"])}
    for k in ("image_tags", "mem_limits", "probe_timeouts"):
        given = st.get(k) if isinstance(st.get(k), dict) else {}
        out[k] = {name: str(given.get(name) or v) for name, v in DEPLOY[k].items()}
    out["tls_verify"] = str(st.get("tls_verify", DEPLOY["tls_verify"])).lower() == "true"
    return out


def deploy_errors(st):
    """What of the deployment's settings this adapter cannot write: a key it has no such entry of, or a value not in
    its form."""
    st = st if isinstance(st, dict) else {}
    errs = []
    if "retention" in st and not DEPLOY_FORMS["retention"].match(str(st["retention"])):
        errs.append("its retention %r is no Prometheus duration (30d, 12w)" % st["retention"])
    for k in ("image_tags", "mem_limits", "probe_timeouts"):
        if k not in st:
            continue
        if not isinstance(st[k], dict):
            errs.append("its %s are not a mapping of %s" % (k, ", ".join(DEPLOY[k])))
            continue
        for name, v in st[k].items():
            if name not in DEPLOY[k]:
                errs.append("its %s name %r, which is none of %s%s" % (
                    k, name, ", ".join(DEPLOY[k]), " (alertmanager's and snmp-exporter's tags are their own sections' "
                                                   "image_tag)" if k == "image_tags" else ""))
            elif not DEPLOY_FORMS[k].match(str(v)):
                errs.append("its %s of %s, %r, is not in the form the bundle writes%s" % (
                    k, name, v, " (a whole version: an image is pinned, so the bundle runs the one tested)"
                    if k == "image_tags" else ""))
            elif k == "probe_timeouts" and seconds(v) > PROBE_MOST:
                errs.append("its probe_timeouts of %s, %r, is longer than a scrape leaves a probe (%ds: a target is "
                            "scraped every %ds)" % (name, v, PROBE_MOST, SCRAPE_EVERY))
    for sect in ("snmp", "alerting"):
        tag = (st.get(sect) or {}).get("image_tag") if isinstance(st.get(sect), dict) else None
        if tag is not None and not DEPLOY_FORMS["image_tags"].match(str(tag)):
            errs.append("its %s.image_tag, %r, is not in the form the bundle writes (a whole version: an image is "
                        "pinned, so the bundle runs the one tested)" % (sect, tag))
    if "tls_verify" in st and str(st["tls_verify"]).lower() not in ("true", "false"):
        errs.append("its tls_verify is %r, neither true nor false" % st["tls_verify"])
    return errs


# A PROBE'S DEADLINE IS KEPT ONLY WITHIN ITS SCRAPE'S: the blackbox exporter ends a probe half a second before the
# scrape that asked for it times out (prometheus.yml's global, SCRAPE_TIMEOUT), so a job whose probe may run longer is given a
# scrape deadline of its own, a second past the probe's, and no probe may run longer than a scrape leaves it.
SCRAPE_EVERY, SCRAPE_TIMEOUT, PROBE_MOST = 30, 10, 29


def seconds(d):
    """A probe's deadline (`5s`, `750ms`) in seconds."""
    d = str(d)
    return int(d[:-2]) / 1000 if d.endswith("ms") else int(d[:-1])


def scrape_timeout(probe):
    """The line a blackbox job takes for a probe of this deadline: none while the global scrape deadline keeps it."""
    s = seconds(probe)
    return "" if s <= SCRAPE_TIMEOUT - 0.5 else "    scrape_timeout: %ds\n" % min(SCRAPE_EVERY, int(s + 0.999) + 1)


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


_UNIT_SUFFIX = {"s": "seconds", "By": "bytes", "1": "ratio"}     # OpenTelemetry's unit, as a Prometheus name ends


def signal_name(sig):
    """The name a signal is kept under in Prometheus, by OpenTelemetry's rule for it: dots become underscores, the unit
    becomes a suffix (an annotation in braces, `{request}`, is no unit and adds none; `1` is `ratio`, and on a gauge
    only), and a counter ends `_total`."""
    base = re.sub(r"[^a-zA-Z0-9_]", "_", str(sig.get("signal")))
    unit, inst = str(sig.get("unit") or ""), sig.get("instrument")
    suffix = _UNIT_SUFFIX.get(unit) if not unit.startswith("{") else None
    if suffix == "ratio" and inst != "gauge":
        suffix = None
    if suffix and not base.endswith("_" + suffix):
        base += "_" + suffix
    return base + ("_total" if inst == "counter" else "")


def signal_query(sig, sel):
    """A signal asked in PromQL, as its instrument is read now: a gauge averaged, an up-down counter summed, a counter's
    rate, and a histogram's mean over five minutes — the scope `sel` in every selector."""
    n, inst = signal_name(sig), sig.get("instrument")
    if inst == "histogram":
        return "sum(rate(%s_sum{%s}[5m])) / sum(rate(%s_count{%s}[5m]))" % (n, sel, n, sel)
    if inst == "counter":
        return "sum(rate(%s{%s}[5m]))" % (n, sel)
    return "%s(%s{%s})" % ("avg" if inst == "gauge" else "sum", n, sel)


def query(b, sel=None):
    if b.get("live") == "live-state":
        return 'min(probe_success{name="%s", %s})' % (b.get("probe"), PROBES)
    says = (b.get("query") or {}).get(TECHNOLOGY)
    if says is None and isinstance(b.get("signal"), dict):
        return signal_query(b["signal"], sel or selector())      # the published name, asked in this language
    return str(says).replace("$F", sel or selector()) if says is not None else None


def describe(b):
    """The path to a shown number: the query that computes it, as the page states it."""
    return query(b, "$F") or ""


def check_binding(b):
    out = []
    if b.get("live") != "live-state":
        says = (b.get("query") or {}).get(TECHNOLOGY)
        if (not isinstance(says, str) or not says.strip()) and not isinstance(b.get("signal"), dict):
            out.append("its %s query is not a text of PromQL, and it names no signal to ask in it" % TECHNOLOGY)
        if b.get("live") == "live-series" and not isinstance((b.get("items_by") or {}).get(TECHNOLOGY), str):
            out.append("a live-series read by %s names the label that tells its items apart (`items_by`)" % TECHNOLOGY)
    return out


def _get(url, timeout):
    if timeout <= 0:
        raise view_fetch.Refused("this poll's time is spent")
    return view_fetch.get_json(url, timeout)


POLL_SECONDS = 10       # one poll's reads of one monitor, together: a slow monitor costs a poll this, at most


def values(url, binds, sel=None):
    """{binding id: number | [{name, value}] | None} — each binding asked of the monitor at `url`, now."""
    out, budget = {}, view_fetch.Budget(POLL_SECONDS)
    for b in binds:
        q = query(b, sel)
        try:
            r = _get(url.rstrip("/") + "/api/v1/query?" + urllib.parse.urlencode({"query": q}), budget.left(5))
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
    out, budget = {}, view_fetch.Budget(2 * POLL_SECONDS)
    for b in binds:
        if b.get("live") != "live-value":
            continue
        try:
            r = _get(url.rstrip("/") + "/api/v1/query_range?" + urllib.parse.urlencode(
                {"query": query(b, sel), "start": now - hours * 3600, "end": now, "step": step}), budget.left(8))
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
        if p == "http":                                # an endpoint at a uri is probed at it: its name, scheme and port
            for e in vm.fm(t).get("endpoints") or []:
                if isinstance(e, dict) and e.get("protocol") == p and e.get("system") == "uri" and e.get("at"):
                    groups["http"].append({"targets": [str(e["at"])], "labels": dict(lb)})
                    if str(e["at"]).startswith("https://"):
                        groups["tls"].append({"targets": [str(e["at"])], "labels": dict(lb)})
        eps = [(str(e.get("at")), str(e.get("port")), e.get("confidentiality") == "encrypted")
               for e in (vm.fm(t).get("endpoints") or [])
               if isinstance(e, dict) and e.get("protocol") == p and e.get("at") and e.get("port")]
        if not eps and any(isinstance(e, dict) and e.get("protocol") == p and e.get("system") == "uri"
                           for e in vm.fm(t).get("endpoints") or []):
            continue                                   # probed at its uri, above
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


# A PROBE'S INSIDE RESOLUTION (core 4.3): a site whose public address its LAN cannot reach (no hairpin) probes its own
# public names wrongly from inside. A name a probe reaches is resolved, for the probe alone, to the address its serving
# being stands at on the LAN — its own `be … as: location`, else that of the being it lives in — at an address of RFC
# 1918 or RFC 4193. Never guessed: where neither position states a prefix, only a name the monitor's own machine serves
# is resolved (its own address); a being elsewhere is on the monitor's LAN where a prefix either states holds both.
# Written as the blackbox service's `extra_hosts`, read from the ledger each time; `view check` names what is left.
# RFC 1918's three blocks — 10/8, 172.16/12 and 192.168/16, the last written by its number — and RFC 4193's fc00::/7
LANS = [ipaddress.ip_network(n) for n in ("10.0.0.0/8", "172.16.0.0/12", (0xC0A80000, 16), "fc00::/7")]


def _lan(b):
    """[(address, network or None)] — the private addresses a being stands at as its location."""
    out = []
    for e in vm.fm(b).get("located_at") or []:
        if not (isinstance(e, dict) and e.get("at")) or e.get("openness") == "unknown":
            continue
        try:
            i = ipaddress.ip_interface(str(e["at"]))
        except ValueError:
            continue
        if any(i.ip.version == n.version and i.ip in n for n in LANS):
            out.append((str(i.ip), i.network if "/" in str(e["at"]) else None))
    return out


def lan_of(b):
    """(the machine, [(address, network or None)]): the being itself, or the first being it lives in, that stands at a
    private address; (None, []) where none does."""
    seen = set()
    while isinstance(b, str) and b and b not in seen:
        seen.add(b)
        got = _lan(b)
        if got:
            return b, got
        li = vm.fm(b).get("lives_in")
        b = li.get("bean") if isinstance(li, dict) else None
    return None, []


def _one_lan(a, net, mine):
    """Whether `a` (its network `net`, where its position states one) is on the LAN of `mine`, by a prefix either side
    states: with none, nothing says it is."""
    ip = ipaddress.ip_address(a)
    return any(ipaddress.ip_address(x).version == ip.version and (net is not None or n is not None)
               and (net is None or ipaddress.ip_address(x) in net) and (n is None or ip in n) for x, n in mine)


def resolutions(m, groups):
    """([(name, address)], [(name, being, why)]): each name the monitor's probes reach, resolved to where its serving
    being stands on the LAN; and each served at a private address that nothing says is on the monitor's LAN."""
    machine, mine = lan_of(m["bean"])
    if not machine:
        return [], []                                  # a monitor on no LAN probes every name as the world resolves it
    out, left = {}, {}
    for mod in ("http", "tls", "tcp", "smtp"):
        for g in groups.get(mod) or []:
            for t in g.get("targets") or []:
                host = urllib.parse.urlsplit(t if "://" in t else "//" + t).hostname
                try:
                    ipaddress.ip_address(host or "")
                    continue                           # an address is reached as it is
                except ValueError:
                    pass
                being = (g.get("labels") or {}).get("name")
                where, theirs = lan_of(being)
                hit = theirs[0][0] if theirs and where == machine else \
                    next((a for a, net in theirs if _one_lan(a, net, mine)), None)
                if host and hit:
                    out.setdefault(host, hit)
                elif host and theirs:
                    left.setdefault(host, (being, "it stands at %s on a LAN, and no prefix says the monitor's machine "
                                                  "is on it: state the locations with their prefix" % theirs[0][0]))
    return sorted(out.items()), sorted((h, b, w) for h, (b, w) in left.items() if h not in out)


def inside(m, groups):
    """[(name, address)]: each name the monitor's probes reach, resolved to where its serving being stands on the LAN."""
    return resolutions(m, groups)[0]


def check_monitor(m):
    """(errors, warnings) of what the adapter reads: a reach it cannot probe is said, never dropped in silence."""
    errs, warns = [], []
    _g, parked = targets(m)
    for b, p, why in parked:
        warns.append("reaches %s over %s, and does not probe it: %s" % (b, p, why))
    for name, b, why in resolutions(m, _g)[1]:
        warns.append("probes %s, served by %s, as the world resolves it: %s" % (name, b, why))
    st = m.get("settings")
    if st is not None and not isinstance(st, dict):
        errs.append("its settings are not a mapping of what %s reads (alerts, alerting, snmp, filesystems, "
                    "grafana_plugins, and the deployment's: %s)" % (TECHNOLOGY, ", ".join(DEPLOY)))
    errs += deploy_errors(st)
    return errs, warns


# ---------------------------------------------------------------------------------------------------------------------
# the bundle
# ---------------------------------------------------------------------------------------------------------------------
PROM_YML = """# WRITTEN by `view bundle` from the garden's ledger — do not edit it here; write it again.
global:
  scrape_interval: %(every)ds
  scrape_timeout: %(stimeout)ds
  external_labels: {garden: %(garden)s, source: daftar}

scrape_configs:
  - job_name: prometheus
    static_configs: [{targets: ['localhost:9090']}]

  - job_name: node
    honor_labels: true      # a textfile value about another being (a filesystem read over ssh) keeps that being's labels
    static_configs: [{targets: ['host.docker.internal:9100'], labels: %(host)s}]

%(jobs)s%(alerting)s"""

BLACKBOX_JOB = """  - job_name: blackbox-%(mod)s
%(timeout)s    metrics_path: /probe
    params: {module: [%(bbmod)s]}
    file_sd_configs: [{files: ['/etc/prometheus/targets/%(mod)s.json'], refresh_interval: 60s}]
    relabel_configs:
      - {source_labels: [__address__], target_label: __param_target}
      - {source_labels: [__param_target], target_label: instance}
      - {target_label: __address__, replacement: 'blackbox:9115'}
"""

BLACKBOX_YML = """# blackbox_exporter modules
modules:
  icmp:        {prober: icmp,  timeout: %(icmp)s, icmp: {preferred_ip_protocol: ip4}}
  tcp_connect: {prober: tcp,   timeout: %(tcp_connect)s}
  smtp_banner: {prober: tcp,   timeout: %(smtp_banner)s, tcp: {query_response: [{expect: '^220'}]}}
  http_2xx:    {prober: http,  timeout: %(http_2xx)s, http: {valid_status_codes: [200,301,302,401,403], fail_if_not_ssl: false, tls_config: {insecure_skip_verify: %(skip)s}, preferred_ip_protocol: ip4}}
"""

COMPOSE = """# WRITTEN by `view bundle` — deploy: docker compose up -d ; take down: docker compose down
name: %(project)s
services:
  prometheus:
    image: prom/prometheus:%(img_prometheus)s
    restart: unless-stopped
    command: ['--config.file=/etc/prometheus/prometheus.yml',
              '--storage.tsdb.path=/prometheus',
              '--storage.tsdb.retention.time=%(retention)s',
              '--web.listen-address=0.0.0.0:9090',
              '--web.enable-lifecycle']
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./targets:/etc/prometheus/targets:ro
      - ./rules:/etc/prometheus/rules:ro
      - promdata:/prometheus
    ports: ['9090:9090']
    extra_hosts: ['host.docker.internal:host-gateway']
    mem_limit: %(mem_prometheus)s
  node-exporter:
    image: prom/node-exporter:%(img_node)s
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
    mem_limit: %(mem_node)s
  blackbox:
    image: prom/blackbox-exporter:%(img_blackbox)s
    restart: unless-stopped
    command: ['--config.file=/etc/blackbox.yml']
    volumes: ['./blackbox.yml:/etc/blackbox.yml:ro']
    ports: ['9115:9115']
    cap_add: ['NET_RAW']   # icmp
%(bb_hosts)s    mem_limit: %(mem_blackbox)s
  grafana:
    image: grafana/grafana:%(img_grafana)s
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
    mem_limit: %(mem_grafana)s   # a limit is a backstop, not a budget
%(extra)svolumes:
  promdata: {}
  grafanadata: {}
"""

README = """# Prometheus and Grafana, written by view from the garden's ledger

WRITTEN by `view bundle`. Write it again after the ledger changes; it overwrites every file it wrote here. Change the
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
    return {"title": "%s — %s" % (kit.plain(view["title"]), folder), "uid": view["uid"], "schemaVersion": 39,
            "version": 1, "refresh": "30s", "time": {"from": "now-6h", "to": "now"}, "editable": False,
            "tags": ["view", "view-drawing", view["key"]], "links": _links(), "templating": _templating(default_org),
            "description": "The drawing of %s, written by view from the garden's ledger; do not edit it here." % view["source"],
            "panels": panels}


def index_dashboard(views, default_org, folder):
    panels = [{"type": "text", "title": "", "gridPos": {"x": 0, "y": 0, "w": 24, "h": 2},
               "options": {"mode": "markdown", "content": "### %s\nEach card is one drawing: open it to see the drawing with "
                                                          "the live values on its own parts. Green: every bound part is up." % folder}}]
    for i, v in enumerate(views):
        names = "|".join(sorted({b["probe"] for b in v["binds"] if b["live"] == "live-state"})) or "none"
        panels.append({"type": "stat", "title": kit.plain(v["title"]),
                       "gridPos": {"x": (i % 4) * 6, "y": 2 + (i // 4) * 4, "w": 6, "h": 4}, "datasource": DS,
                       "targets": [{"expr": 'min(min by (name) (probe_success{name=~"%s", %s, %s}))' % (names, PROBES, FSEL), "refId": "A"}],
                       "links": [{"title": "open the drawing's page", "url": "/d/%s?${__url_time_range}&${__all_variables}" % v["uid"]}],
                       "fieldConfig": {"defaults": {"mappings": [{"type": "value", "options": {
                           "0": {"text": "a part is down", "color": "red"}, "1": {"text": "all up", "color": "green"}}}],
                           "noValue": "no data in this scope", "color": {"mode": "thresholds"},
                           "thresholds": {"mode": "absolute", "steps": [{"color": "#5a6675", "value": None}]}}},
                       "options": {"colorMode": "background", "graphMode": "none", "textMode": "value"}})
    y = 2 + ((len(views) + 3) // 4) * 4
    rows = "".join("| [%s](/d/%s) | %s | %s | %s | %d |\n" % (kit.plain(v["title"]), v["uid"], v["source"],
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
# WRITTEN by `view bundle` from the ledger — a filesystem's size and free space, read with `df` over the ssh access
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
             "# WRITTEN by `view bundle` — writes snmp_exporter's auth file from the host's env file (%s), then runs it."
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
    r = "# WRITTEN by `view bundle` from the monitor's alert rules — change them in its record, never here\ngroups:\n  - name: view\n    rules:\n"
    for a in rules:
        r += ("      - alert: %s\n        expr: %s\n        for: %s\n        labels: {severity: %s}\n        annotations: {summary: %s}\n"
              % (a["name"], json.dumps(a["expr"]), a.get("for", "10m"), a.get("severity", "warning"), json.dumps(a.get("summary", a["name"]))))
    am = """# WRITTEN by `view bundle`
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
    st = m.get("settings") if isinstance(m.get("settings"), dict) else {}
    d = deploy(st)
    jobs = []
    for mod in ("icmp", "tcp", "http", "smtp", "tls"):
        p = os.path.join(out, "targets", mod + ".json")
        if groups[mod]:
            json.dump(groups[mod], open(p, "w"), indent=2)
            jobs.append(BLACKBOX_JOB % {"mod": mod, "bbmod": MODULES[mod],
                                        "timeout": scrape_timeout(d["probe_timeouts"][MODULES[mod]])})
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
        "jobs": "".join(jobs) + snmp_jobs, "alerting": al_block, "every": SCRAPE_EVERY, "stimeout": SCRAPE_TIMEOUT})
    open(os.path.join(out, "blackbox.yml"), "w").write(BLACKBOX_YML % dict(d["probe_timeouts"],
                                                                          skip="false" if d["tls_verify"] else "true"))
    it, ml = d["image_tags"], d["mem_limits"]
    names = inside(m, groups)
    bb_hosts = ("    extra_hosts: [%s]   # each name probed where it is served on the LAN\n"
                % ", ".join("'%s:%s'" % (n, a) for n, a in names)) if names else ""
    compose = COMPOSE % {"project": vm.PAGE, "dir": dirpath, "plugins": ",".join(st.get("grafana_plugins") or []),
                         "extra": snmp_svc + am_svc, "retention": d["retention"], "bb_hosts": bb_hosts,
                         "img_prometheus": it["prometheus"], "img_node": it["node-exporter"], "img_blackbox": it["blackbox"],
                         "img_grafana": it["grafana"], "mem_prometheus": ml["prometheus"], "mem_node": ml["node-exporter"],
                         "mem_blackbox": ml["blackbox"], "mem_grafana": ml["grafana"]}
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
