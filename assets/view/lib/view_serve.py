#!/usr/bin/env python3
"""view_serve — the `view` asset's served page and action executor: the offline report, made live, served from a host.

WHY A SERVER OF ITS OWN. A page served by the asset can do what a static file cannot:
  - SCOPE what it sends. Who may see what is the host's configuration, never the ledger's, and one function answers it
    — `Host.may(user, bean, act)`: "may this viewer see this bean, or run this action?". The documentation the page
    sends (reference rows, part cards, addresses, wiring), the values it reads and every action pass through it. The
    page never sends a query; it asks for a drawing's values and the server builds the queries itself.
  - ACT: a button on a drawing runs a tool the host names.

CLOSED BY DEFAULT. A viewer's configuration names the organisations they may see (`orgs`, or `"*"` for all). A being
belongs to an organisation only where one can be derived from its record (view_model.org_of); a being with none is
seen by a viewer scoped to organisations only through an explicit grant in the host's configuration — `shared: true`,
every being no organisation can be derived for, or `beans: [<id>, …]`, those beings by name. Nothing is shown because
nothing said otherwise.

ACTIONS HAVE TWO KEYS. The LEDGER says where a button is and which tool it asks for (`views.actions`). The HOST's
configuration says what a tool runs (an argv, never a shell), whether it is enabled, and its timeout. A ledger edit can
place a button; only the host can make a command runnable. A tool that is not enabled runs as a DRY RUN: the server
says what it would run, and audits that. Every attempt, dry or real or refused, is appended to the host's audit log
(JSON lines, 0600) with who, what and the result. The viewer must be allowed to act, and to see the being acted on.

SESSIONS. A sign-in form; a signed, expiring, HttpOnly, SameSite=Strict cookie; a CSRF token on every POST. Passwords
are stored as PBKDF2-SHA256 hashes in the host's configuration, never in git. `dmview serve-init` writes the
configuration with a random password in a 0600 file beside it — never printed.

THE LEDGER IS READ AGAIN when the garden's git HEAD moves (asked at most every `recheck_seconds`, 30 by default). When it
moves, or the release GARDEN.md records moves, the server runs `dmview check` on the new state, and only if it passes
starts itself again on it, so new code and new drawings load together; until then it keeps serving what it had.

Usage (through assets/view/bin/dmview.py):
  dmview serve-init --config <path> --user <name> [--orgs "*"|org-a,org-b] [--shared] [--no-actions]
  dmview serve --config <path>
"""
import base64, hashlib, hmac, json, os, secrets, subprocess, sys, threading, time, urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import view_model as vm
import view_report

SESSION_HOURS = 12
PBKDF2_ROUNDS = 200000
COOKIE = "view_session"
CSRF = "X-View-CSRF"


# ---------------------------------------------------------------------------------------------------------------------
# the host's configuration, outside git
# ---------------------------------------------------------------------------------------------------------------------
def hash_password(pw, salt=None):
    salt = salt or secrets.token_hex(16)
    d = hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), PBKDF2_ROUNDS).hex()
    return "pbkdf2$%d$%s$%s" % (PBKDF2_ROUNDS, salt, d)


def check_password(pw, stored):
    try:
        _, rounds, salt, d = stored.split("$")
        got = hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), int(rounds)).hex()
        return hmac.compare_digest(got, d)
    except Exception:
        return False


def _write_private(path, text):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as fh:
        fh.write(text)


def serve_init(config, user, orgs="*", actions=True, shared=False):
    """Write (or add a viewer to) a host configuration. The password goes to a 0600 file, never to the terminal."""
    cfg = json.load(open(config)) if os.path.exists(config) else {
        "listen": "127.0.0.1:8780", "monitors": {}, "history": "",
        "session_key": secrets.token_hex(32), "audit_log": os.path.join(os.path.dirname(os.path.abspath(config)), "actions.log"),
        "users": {}, "tools": {}}
    pw = secrets.token_urlsafe(18)
    cfg["users"][user] = {"password": hash_password(pw),
                          "orgs": ["*"] if orgs == "*" else [o.strip() for o in orgs.split(",") if o.strip()],
                          "shared": bool(shared), "beans": [], "actions": bool(actions)}
    os.makedirs(os.path.dirname(os.path.abspath(config)), exist_ok=True)
    _write_private(config, json.dumps(cfg, indent=1))
    pwfile = os.path.join(os.path.dirname(os.path.abspath(config)), "%s.password" % user)
    _write_private(pwfile, pw + "\n")
    return pwfile


# ---------------------------------------------------------------------------------------------------------------------
# the server
# ---------------------------------------------------------------------------------------------------------------------
class Host:
    def __init__(self, config, argv=None):
        self.config_path = config
        self.cfg = json.load(open(config))
        self.key = bytes.fromhex(self.cfg["session_key"])
        self.lock = threading.Lock()
        self.head, self.checked, self.payload, self.views = None, 0, None, {}
        self.fails = {}
        self.argv = argv or sys.argv
        self.release_at_start = self.release()
        self.refresh(force=True)

    # --- MAY THIS VIEWER SEE THIS BEAN, OR RUN THIS ACTION -----------------------------------------------------------
    # The one place the answer is given. Its body is the host's configuration today; a grant the law declares answers
    # the same question tomorrow, and replaces this body without any caller changing.
    def may(self, user, bean=None, act=False):
        """(yes, why) — whether `user` may see `bean` (None: the page itself) and, with `act`, run an action on it."""
        u = (self.cfg.get("users") or {}).get(user)
        if not isinstance(u, dict):
            return False, "no such viewer"
        if act and not u.get("actions"):
            return False, "this viewer may view but not act"
        if bean is None:
            return True, "the page"
        orgs = u.get("orgs") or []
        if "*" in orgs:
            return True, "every organisation"
        if bean in (u.get("beans") or []):
            return True, "granted by name"
        org = vm.org_of(bean)
        if org is None:
            return ((True, "granted what no organisation owns") if u.get("shared") is True else
                    (False, "no organisation can be derived for it, and no grant opens it"))
        return (True, "its organisation, %s" % org) if org in orgs else (False, "its organisation, %s, is outside the viewer's" % org)

    def scope(self, user):
        """The viewer's scope as a monitor's query reads it: None for every organisation."""
        u = self.cfg["users"][user]
        return None if "*" in (u.get("orgs") or []) else {"orgs": list(u.get("orgs") or []), "shared": u.get("shared") is True}

    # --- the ledger ---
    def git_head(self):
        try:
            return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=vm.ROOT, stderr=subprocess.DEVNULL).decode().strip()
        except Exception:
            return "no-git"

    def release(self):
        return str(vm.fm_path(os.path.join(vm.ROOT, "GARDEN.md")).get("daftar_release") or "")

    def refresh(self, force=False):
        with self.lock:
            if not force and time.time() - self.checked < float(self.cfg.get("recheck_seconds", 30)):
                return
            self.checked = time.time()
            self.maybe_reexec()
            h = self.git_head()
            if h == self.head and self.payload is not None:
                return
            vm.init(vm.ROOT, vm.PAGE)
            errs, _ = vm.check()
            if errs:
                if self.payload is None:
                    raise SystemExit("dmview serve: the page and its drawings disagree:\n  - " + "\n  - ".join(errs))
                sys.stderr.write("dmview serve: the ledger at %s does not check; still serving %s\n" % (h[:10], (self.head or "")[:10]))
                return
            self.payload, self.head = view_report.payload(), h
            self.views = {v["key"]: v for v in self.payload["views"].values()}

    def maybe_reexec(self):
        """The code that serves must be the release the garden records, and the drawings the ledger names. When a pull
        brings a new ledger head (which may carry a changed drawing module this process holds an old import of) or a new
        release, start again on it — only once `dmview check` passes on it; while it does not, keep serving and say why."""
        new = self.release()
        head_moved = self.payload is not None and self.git_head() != self.head
        if new == self.release_at_start and not head_moved:
            return
        probs = subprocess.run([sys.executable, os.path.join(os.path.dirname(HERE), "bin", "dmview.py"), "check",
                                "--garden", vm.ROOT] + (["--page", vm.PAGE] if vm.PAGE else []), capture_output=True, text=True, encoding="utf-8", errors="replace")
        if probs.returncode != 0:
            sys.stderr.write("dmview serve: the pulled ledger or release does not check; still serving %s\n" % self.release_at_start)
            return
        sys.stderr.write("dmview serve: reloading (release %s -> %s, or a new ledger head)\n" % (self.release_at_start, new))
        sys.stderr.flush()
        os.execv(sys.executable, [sys.executable] + self.argv)

    # --- what a viewer is sent ---
    def scoped_payload(self, user):
        """The page as `user` may see it: every being they may not see taken out of what is sent, and every drawing of a
        being they may not see."""
        p = json.loads(json.dumps(self.payload))
        ok = lambda b: self.may(user, b)[0]
        p["reference"] = [r for r in p["reference"] if ok(r["being"])]
        p["beans"] = {b: v for b, v in p["beans"].items() if ok(b)}
        p["addresses"] = {b: a for b, a in (p.get("addresses") or {}).items() if ok(b)}
        p.pop("author", None)                        # the served page edits nothing; the author mode is the report's
        for k in list(p["views"]):
            v = p["views"][k]
            if v.get("draws_bean") and not ok(v["draws_bean"]):
                del p["views"][k]
                p["order"] = [x for x in p["order"] if x != k]
                continue
            v["facts"] = {b: f for b, f in (v.get("facts") or {}).items() if ok(b)}
            v["parts"] = [x for x in (v.get("parts") or []) if ok(x["bean"])]
            if v.get("wiring") and not ok(v["wiring"]["bean"]):
                v["wiring"] = None
            v["tiles"] = [t for t in v.get("tiles") or [] if not t.get("bean") or ok(t["bean"])]
        return p

    def _bound(self, user, key):
        v = self.views.get(key)
        if not v or (v.get("draws_bean") and not self.may(user, v["draws_bean"])[0]):
            return None
        return v

    def values(self, user, key):
        v = self._bound(user, key)
        if v is None:
            return None
        out = {}
        by_monitor = {}
        for b in v["binds"]:
            if b.get("probe") and not self.may(user, b["probe"])[0]:
                out[b["id"]] = None                  # a being the viewer may not see is not asked about
                continue
            by_monitor.setdefault(b.get("monitor"), []).append(b)
        for mon, binds in by_monitor.items():
            m = next((x for x in vm.monitors() if x["bean"] == mon), None)
            url = ((self.cfg.get("monitors") or {}).get(mon) or {}).get("url") if mon else None
            if not m or not m["adapter"] or not url:
                out.update({b["id"]: None for b in binds}); continue
            sel = m["adapter"].selector(self.scope(user))
            out.update(m["adapter"].values(url, binds, sel))
        return out

    def history(self, user, key):
        """[[t, v], …] per live-value binding over the drawing's window — its sparklines and its correlate blocks — built
        here, with the viewer's scope, like every other query."""
        v = self._bound(user, key)
        if v is None:
            return None
        hours, step = (v.get("window") or {}).get("hours", 6), (v.get("window") or {}).get("step", 300)
        out, now = {}, int(time.time())
        by_monitor = {}
        for b in v["binds"]:
            if b.get("live") == "live-value" and not (b.get("probe") and not self.may(user, b["probe"])[0]):
                by_monitor.setdefault(b.get("monitor"), []).append(b)
        for mon, binds in by_monitor.items():
            m = next((x for x in vm.monitors() if x["bean"] == mon), None)
            url = ((self.cfg.get("monitors") or {}).get(mon) or {}).get("url") if mon else None
            if not m or not m["adapter"] or not url:
                out.update({b["id"]: [] for b in binds}); continue
            out.update(m["adapter"].history(url, binds, m["adapter"].selector(self.scope(user)), hours, step, now))
        return out

    # --- actions ---
    def audit(self, entry):
        entry = dict(entry, ts=time.strftime("%Y-%m-%dT%H:%M:%S%z"))
        fd = os.open(self.cfg["audit_log"], os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(fd, "a") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def act(self, user, key, el):
        v = self._bound(user, key)
        a = next((x for x in (v or {}).get("actions", []) if x["el"] == el), None)
        base = {"user": user, "view": key, "element": el, "head": (self.head or "")[:12]}
        if not a:
            return 404, {"error": "no action is declared on that element in the ledger"}
        base["tool"] = a["tool"]
        yes, why = self.may(user, a.get("bean"), act=True)
        if not yes:
            self.audit(dict(base, mode="refused", why=why))
            return 403, {"error": "refused: %s" % why}
        tool = (self.cfg.get("tools") or {}).get(a["tool"])
        if not tool:
            self.audit(dict(base, mode="refused", why="tool not in the host's allow-list"))
            return 403, {"error": "the host does not know tool %r — nothing ran" % a["tool"]}
        argv = [str(x) for x in tool["argv"]]
        if not tool.get("enabled"):
            self.audit(dict(base, mode="dry-run", argv=argv))
            return 200, {"mode": "dry-run", "tool": a["tool"], "argv": argv,
                         "message": "DRY RUN — the host has this tool but it is not enabled; it would run: " + " ".join(argv)}
        t0 = time.time()
        try:
            r = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=int(tool.get("timeout", 120)),
                               env={"PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin", "LANG": "C.UTF-8"})
            rc, out = r.returncode, (r.stdout + r.stderr)[-4000:]
        except subprocess.TimeoutExpired:
            rc, out = -1, "timed out after %ss" % tool.get("timeout", 120)
        except OSError as e:
            rc, out = -2, str(e)
        self.audit(dict(base, mode="run", argv=argv, rc=rc, seconds=round(time.time() - t0, 1), output_tail=out[-1500:]))
        return 200, {"mode": "run", "tool": a["tool"], "rc": rc, "output": out}

    def audit_tail(self, user, n=30):
        try:
            lines = open(self.cfg["audit_log"]).read().splitlines()[-400:]
        except OSError:
            return []
        rows = [json.loads(l) for l in lines if l.strip()]
        if self.scope(user) is not None:
            rows = [r for r in rows if r.get("user") == user]
        return rows[-n:]

    # --- sessions ---
    def token(self, user):
        exp = int(time.time()) + SESSION_HOURS * 3600
        body = "%s|%d" % (user, exp)
        sig = hmac.new(self.key, body.encode(), hashlib.sha256).hexdigest()
        return base64.urlsafe_b64encode(("%s|%s" % (body, sig)).encode()).decode()

    def user_of(self, tok):
        try:
            user, exp, sig = base64.urlsafe_b64decode(tok.encode()).decode().split("|")
            good = hmac.new(self.key, ("%s|%s" % (user, exp)).encode(), hashlib.sha256).hexdigest()
            if hmac.compare_digest(sig, good) and int(exp) > time.time() and user in self.cfg["users"]:
                return user
        except Exception:
            pass
        return None

    def csrf(self, tok):
        return hmac.new(self.key, ("csrf|" + tok).encode(), hashlib.sha256).hexdigest()


LOGIN = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>%(title)s — sign in</title><style>body{background:#0f1319;color:#e8edf3;font:14px system-ui;display:grid;place-items:center;height:100vh;margin:0}
form{background:#161c24;border:1px solid #2a3644;border-radius:14px;padding:22px 26px;min-width:280px}h1{font-size:17px;margin:0 0 12px}
input{display:block;width:100%%;margin:6px 0 12px;background:#0f1319;color:#e8edf3;border:1px solid #2a3644;border-radius:7px;padding:8px}
button{background:#ff9d4a;color:#1a1206;border:0;border-radius:8px;padding:8px 16px;font-weight:700;cursor:pointer}.e{color:#f85149;margin-bottom:8px}</style></head>
<body><form method="post" action="/login"><h1>%(title)s</h1>%(err)s<label>user<input name="user" autocomplete="username" autofocus></label>
<label>password<input name="password" type="password" autocomplete="current-password"></label><button>Sign in</button></form></body></html>"""


def make_handler(F):
    title = view_report.esc(str(vm.page().get("title") or vm.PAGE))

    class H(BaseHTTPRequestHandler):
        server_version = "dmview"
        sys_version = ""

        def log_message(self, fmt, *a):
            sys.stderr.write("%s %s\n" % (time.strftime("%H:%M:%S"), fmt % a))

        def _send(self, code, body, ctype="text/html; charset=utf-8", headers=None):
            b = body.encode() if isinstance(body, str) else body
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(b)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "same-origin")
            for k, v in (headers or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(b)

        def _json(self, code, obj):
            self._send(code, json.dumps(obj, ensure_ascii=False), "application/json")

        def _session(self):
            for part in (self.headers.get("Cookie") or "").split(";"):
                k, _, v = part.strip().partition("=")
                if k == COOKIE:
                    return v, F.user_of(v)
            return None, None

        def do_GET(self):
            u = urllib.parse.urlparse(self.path)
            if u.path == "/healthz":
                F.refresh()      # a health check also notices a new ledger head or a new release
                return self._send(200, "ok", "text/plain", headers={"X-View-Release": F.release_at_start})
            if u.path == "/login":
                return self._send(200, LOGIN % {"title": title, "err": ""})
            if u.path == "/logout":
                return self._send(303, "", headers={"Location": "/login", "Set-Cookie": "%s=; Max-Age=0; Path=/; HttpOnly; SameSite=Strict" % COOKIE})
            tok, user = self._session()
            if not user:
                if u.path.startswith("/api/"):
                    return self._json(401, {"error": "sign in"})
                return self._send(303, "", headers={"Location": "/login"})
            F.refresh()
            if u.path == "/":
                p = F.scoped_payload(user)
                p["live"] = {"user": user, "csrf": F.csrf(tok), "history": F.cfg.get("history", ""), "poll": 30,
                             "actions": F.may(user, act=True)[0], "head": (F.head or "")[:10]}
                return self._send(200, view_report.build_html(p))
            if u.path == "/api/values":
                key = urllib.parse.parse_qs(u.query).get("m", [""])[0]
                vals = F.values(user, key)
                return self._json(200 if vals is not None else 404, {"values": vals, "at": int(time.time())} if vals is not None else {"error": "no such drawing"})
            if u.path == "/api/history":
                key = urllib.parse.parse_qs(u.query).get("m", [""])[0]
                hist = F.history(user, key)
                return self._json(200 if hist is not None else 404, {"history": hist} if hist is not None else {"error": "no such drawing"})
            if u.path == "/api/audit":
                return self._json(200, {"entries": F.audit_tail(user)})
            return self._send(404, "not found", "text/plain")

        def do_POST(self):
            u = urllib.parse.urlparse(self.path)
            n = int(self.headers.get("Content-Length") or 0)
            if n > 65536:
                return self._send(413, "too large", "text/plain")
            raw = self.rfile.read(n).decode("utf-8", "replace")
            if u.path == "/login":
                f = urllib.parse.parse_qs(raw)
                user, pw = f.get("user", [""])[0], f.get("password", [""])[0]
                ip = self.client_address[0]
                if F.fails.get(ip, 0) >= 5:
                    time.sleep(3)
                rec = F.cfg["users"].get(user)
                if rec and check_password(pw, rec["password"]):
                    F.fails.pop(ip, None)
                    return self._send(303, "", headers={"Location": "/", "Set-Cookie": "%s=%s; Path=/; HttpOnly; SameSite=Strict; Max-Age=%d"
                                                         % (COOKIE, F.token(user), SESSION_HOURS * 3600)})
                F.fails[ip] = F.fails.get(ip, 0) + 1
                time.sleep(1)
                return self._send(401, LOGIN % {"title": title, "err": '<div class="e">wrong user or password</div>'})
            tok, user = self._session()
            if not user:
                return self._json(401, {"error": "sign in"})
            if not hmac.compare_digest(self.headers.get(CSRF) or "", F.csrf(tok)):
                return self._json(403, {"error": "missing or wrong CSRF token"})
            if u.path == "/api/action":
                try:
                    body = json.loads(raw or "{}")
                except ValueError:
                    return self._json(400, {"error": "bad json"})
                F.refresh()
                code, obj = F.act(user, str(body.get("m", "")), str(body.get("el", "")))
                return self._json(code, obj)
            return self._json(404, {"error": "not found"})
    return H


def serve(config, argv=None):
    F = Host(config, argv)
    host, _, port = F.cfg.get("listen", "127.0.0.1:8780").rpartition(":")
    srv = ThreadingHTTPServer((host or "127.0.0.1", int(port)), make_handler(F))
    sys.stderr.write("dmview serve: %s:%s · page %s of %s @ %s · %d viewers · %d tools (%d enabled)\n" % (
        host, port, vm.PAGE, vm.garden_name(), (F.head or "")[:10], len(F.cfg["users"]), len(F.cfg.get("tools") or {}),
        sum(1 for t in (F.cfg.get("tools") or {}).values() if t.get("enabled"))))
    srv.serve_forever()
