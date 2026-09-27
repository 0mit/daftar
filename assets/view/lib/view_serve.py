#!/usr/bin/env python3
"""view_serve — the `view` asset's served page and action executor: the offline report, made live, served from a host.

WHY A SERVER OF ITS OWN. A page served by the asset can do what a static file cannot:
  - SCOPE what it sends. Who may see what is the LEDGER's — the grants its beings hold, asked of bin/dmpass.py `may`
    for the being the host names for the viewer (`bean`) — and one function answers it, `Host.may(user, bean, act,
    positions, write)`: "may this viewer see this bean, or this part of it, run this action, write here?". The
    documentation the page sends (reference rows, part cards, addresses, wiring), a table's lines, a funnel's counts,
    the values it reads, every action and every write pass through it. Where only a part of a bean is granted
    (`positions`), only that part is sent, marked a part. The page never sends a query; it asks for a drawing's values
    and the server builds the queries itself.
  - ACT: a button on a drawing runs a tool the host names; an action with `every` runs on its schedule as the being who
    answers for it (`run_scheduled`), asked like a press.
  - WRITE: a drawing's entry form (`views.writes`) adds an entry of a term the law gives, through bin/dmsave.py as the
    viewer's being; the gate judges it, and a refused save is undone and its message shown (`/api/write`).
  - EXPORT: a table's lines as CSV (`/api/csv`), each line scoped as on the page.

CLOSED BY DEFAULT, TWICE. The law grants nothing that no grant opens (the gardener excepted). The host's configuration
is a CEILING under it, never a key: a viewer's configuration names the organisations they may see (`orgs`, or `"*"` for
all, which leaves the ledger alone to decide). A being belongs to an organisation only where one can be derived from its
record (view_model.org_of); a being with none is under the ceiling of a viewer scoped to organisations only through the
host's `shared: true` (every being no organisation can be derived for) or `beans: [<id>, …]` (those beings by name).
Nothing is shown because nothing said otherwise.

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
import base64, hashlib, hmac, json, os, re, secrets, subprocess, sys, threading, time, urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import view_model as vm
import view_report

# The rows of the flow law this tool checks, and the fixture that shows it (`bin/dmpass.py --flows` computes the guard).
GUARDS = {
    'served': {'checks': "a page or an action is served only where a grant opens it to the viewer, asked before each",
               'proof': 'test/view.py', 'label': "serve: carol, granted what no organisation owns, sees the radio"},
}

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


def serve_init(config, user, orgs="*", actions=True, shared=False, bean=None):
    """Write (or add a viewer to) a host configuration. The password goes to a 0600 file, never to the terminal.
    `bean` is the viewer's own bean in the garden: the person a grant the law declares is asked about."""
    cfg = json.load(open(config)) if os.path.exists(config) else {
        "listen": "127.0.0.1:8780", "monitors": {}, "history": "",
        "session_key": secrets.token_hex(32), "audit_log": os.path.join(os.path.dirname(os.path.abspath(config)), "actions.log"),
        "users": {}, "tools": {}}
    pw = secrets.token_urlsafe(18)
    cfg["users"][user] = {"password": hash_password(pw),
                          "orgs": ["*"] if orgs == "*" else [o.strip() for o in orgs.split(",") if o.strip()],
                          "shared": bool(shared), "beans": [], "actions": bool(actions)}
    if bean:
        cfg["users"][user]["bean"] = bean
    os.makedirs(os.path.dirname(os.path.abspath(config)), exist_ok=True)
    _write_private(config, json.dumps(cfg, indent=1))
    pwfile = os.path.join(os.path.dirname(os.path.abspath(config)), "%s.password" % user)
    _write_private(pwfile, pw + "\n")
    return pwfile


# ---------------------------------------------------------------------------------------------------------------------
# the server
# ---------------------------------------------------------------------------------------------------------------------
class Verdict(tuple):
    """(yes, why), and the grants the answer read — compares as the pair it is."""
    def __new__(cls, yes, why, grants=(), reason_asked=False):
        t = tuple.__new__(cls, (bool(yes), why))
        t.grants, t.reason_asked = list(grants), bool(reason_asked)
        return t


class Host:
    def __init__(self, config, argv=None):
        self.config_path = config
        self.cfg = json.load(open(config))
        self.key = bytes.fromhex(self.cfg["session_key"])
        self.lock = threading.Lock()
        self.wlock = threading.Lock()                # one form's save at a time in this host; dmsave's own lock queues others
        self.head, self.checked, self.payload, self.views = None, 0, None, {}
        self.fails = {}
        self.beans, self.gardener, self.answers = {}, None, {}
        self.argv = argv or sys.argv
        self.release_at_start = self.release()
        self.refresh(force=True)

    # --- MAY THIS VIEWER SEE THIS BEAN, OR RUN THIS ACTION -----------------------------------------------------------
    # The one place the answer is given (24.0, N33). The host's configuration is a CEILING: it can narrow what a viewer
    # is sent (orgs, shared, beans, actions), and never widen it. What opens a page, a bean or an action is a grant the
    # law declares, asked of `bin/dmpass.py` for the being the host names for this viewer — before every page, value,
    # history and action.
    def may(self, user, bean=None, act=False, tool=None, positions=None, reason=None, write=False):
        """(yes, why) — whether `user` may see `bean` (None: the page itself), at `positions` (None: the whole bean), and,
        with `act`, run `tool` on it, or with `write`, write it. The answer also carries `.grants` (every grant read) and
        `.reason_asked`."""
        u = (self.cfg.get("users") or {}).get(user)
        if not isinstance(u, dict):
            return Verdict(False, "no such viewer")
        if (act or write) and not u.get("actions"):
            return Verdict(False, "this viewer may view but not act")
        if bean is not None:
            ceiling = self._ceiling(u, bean)
            if ceiling:
                return Verdict(False, ceiling)
        actor = u.get("bean")
        if not actor:
            return Verdict(False, "the host names no being for this viewer (`bean`), and the law grants nobody unnamed")
        if act and not tool:
            return Verdict(True, "this viewer may act, where a grant opens the tool")
        what = ("act:" + tool) if act else "write" if write else "read"
        target = bean if bean is not None else vm.PAGE
        k = (actor, what, target, tuple(positions) if positions else None, bool(reason))
        a = self.answers.get(k)
        if a is None:
            import dmpass
            a = dmpass.may(actor, what, target, positions=positions, reason=reason, root=vm.ROOT, beans=self.beans,
                           gardener=self.gardener)
            self.answers[k] = a
        return Verdict(a.granted, a.why, a.grants, a.reason_asked)

    @staticmethod
    def _ceiling(u, bean):
        """Why the host's configuration narrows `bean` away from this viewer, or None where it does not."""
        orgs = u.get("orgs") or []
        if "*" in orgs or bean in (u.get("beans") or []):
            return None
        org = vm.org_of(bean)
        if org is None:
            return None if u.get("shared") is True else "the host opens nothing no organisation owns to this viewer (no grant: `shared`, or by name)"
        return None if org in orgs else "its organisation, %s, is outside the viewer's" % org

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

    def refresh(self, force=False, reexec=True):
        with self.lock:
            if not force and time.time() - self.checked < float(self.cfg.get("recheck_seconds", 30)):
                return
            self.checked = time.time()
            if reexec:
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
            import dmpass
            self.beans, self.gardener, self.answers = dmpass.beans_here(vm.ROOT), dmpass.gardener_of(vm.ROOT), {}
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
        beans = {}
        for b, v in p["beans"].items():
            if ok(b):
                beans[b] = v
                continue
            # A GRANT MAY OPEN PART OF A BEAN (`positions`): where the whole is not granted, each of its positions is
            # asked, and only those granted are sent.
            if self._ceiling(self.cfg["users"][user], b):
                continue
            fields = {k: x for k, x in (v.get("fields") or {}).items() if self.may(user, b, positions=[k])[0]}
            title = v.get("title") if self.may(user, b, positions=["title"])[0] else ""
            if fields or title:
                beans[b] = dict(v, fields=fields, title=title, part=True)
        p["beans"] = beans
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
            op = v.get("operate") or {}
            if op.get("table"):                      # a line of a table shows the parts of one being its columns read:
                op["table"]["rows"] = [r for r in op["table"]["rows"] if self.line_ok(user, r["bean"], op["table"])]
            for f in op.get("funnels") or []:          # a reading's count is of the members this viewer may see
                for st in f.get("stages") or []:
                    if st.get("members") is not None:
                        st["static"] = sum(1 for m in st["members"] if ok(m))
                    st.pop("members", None)
        return p

    def line_ok(self, user, bean, table):
        """Whether `user` may see a table's line of `bean`: the whole being, or every part its columns read (`positions`)."""
        if self.may(user, bean)[0]:
            return True
        reads = table.get("reads") or []
        return bool(reads) and not self._ceiling(self.cfg["users"][user], bean) and self.may(user, bean, positions=reads)[0]

    def _bound(self, user, key):
        v = self.views.get(key)
        if not v or not self.may(user)[0] or (v.get("draws_bean") and not self.may(user, v["draws_bean"])[0]):
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

    def act(self, user, key, el, inputs=None, reason=None, at=None, scheduled=False):
        """Run the action on `el` of drawing `key` for `user`: asked of the law's grants as `act:<tool>` for the being the
        host names for the viewer, with the reason where a grant asks one. The tool reads one JSON object on its standard
        input — the actor, the viewer, the record acted on, the moment, and the inputs the action declares — and every
        attempt, dry, real or refused, is audited with the answer that decided it."""
        v = self.views.get(key) if scheduled else self._bound(user, key)
        a = next((x for x in (v or {}).get("actions", []) if x["el"] == el), None)
        actor = ((self.cfg.get("users") or {}).get(user) or {}).get("bean")
        base = {"user": user, "actor": actor, "view": key, "element": el, "head": (self.head or "")[:12]}
        if not a:
            return 404, {"error": "no action is declared on that element in the ledger"}
        base.update(tool=a["tool"], act="act:" + a["tool"], bean=a.get("bean"), reason=reason or None)
        declared = {i.get("name"): i for i in a.get("inputs") or []}
        given = {k: str(x) for k, x in (inputs or {}).items() if k in declared}
        undeclared = sorted(set(inputs or {}) - set(declared))
        missing = sorted(n for n, i in declared.items() if n not in given and (i.get("origin") or {}).get("act", "said") == "said")
        base["inputs"] = given
        if undeclared or missing:
            self.audit(dict(base, mode="refused", why="inputs"))
            return 400, {"error": "refused: " + "; ".join(
                (["the action declares no input %s" % ", ".join(undeclared)] if undeclared else []) +
                (["the action asks for %s" % ", ".join(missing)] if missing else []))}
        ans = self.may(user, a.get("bean"), act=True, tool=a["tool"], reason=reason)
        base["answer"] = {"granted": ans[0], "why": ans[1], "grants": [list(g) for g in ans.grants]}
        if not ans[0]:
            self.audit(dict(base, mode="refused", why=ans[1]))
            return 403, {"error": "refused: %s" % ans[1], "reason_asked": ans.reason_asked}
        tool = (self.cfg.get("tools") or {}).get(a["tool"])
        if not tool:
            self.audit(dict(base, mode="refused", why="tool not in the host's allow-list"))
            return 403, {"error": "the host does not know tool %r — nothing ran" % a["tool"]}
        argv = [str(x) for x in tool["argv"]]
        if not tool.get("enabled"):
            self.audit(dict(base, mode="dry-run", argv=argv))
            return 200, {"mode": "dry-run", "tool": a["tool"], "argv": argv,
                         "message": "DRY RUN — the host has this tool but it is not enabled; it would run: " + " ".join(argv)}
        stdin = json.dumps({"actor": actor, "user": user, "record": a.get("bean"), "moment": at or time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                            "inputs": given, "reason": reason or None}, ensure_ascii=False)
        t0 = time.time()
        try:
            r = subprocess.run(argv, input=stdin, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=int(tool.get("timeout", 120)),
                               env={"PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin", "LANG": "C.UTF-8"})
            rc, out = r.returncode, (r.stdout + r.stderr)[-4000:]
        except subprocess.TimeoutExpired:
            rc, out = -1, "timed out after %ss" % tool.get("timeout", 120)
        except OSError as e:
            rc, out = -2, str(e)
        self.audit(dict(base, mode="run", argv=argv, rc=rc, seconds=round(time.time() - t0, 1), output_tail=out[-1500:]))
        return 200, {"mode": "run", "tool": a["tool"], "rc": rc, "output": out}

    # --- AN ENTRY FORM (24.0, N37) ----------------------------------------------------------------------------------
    def _git(self, *args):
        return subprocess.run(["git"] + list(args), cwd=vm.ROOT, capture_output=True, text=True, encoding="utf-8",
                              errors="replace")

    def write(self, user, key, w, bean, entry, values):
        """Add one entry to a term of `bean` through drawing `key`'s form `w`, for `user`: asked of the law's grants as
        `write` for the being the host names for the viewer, written through bin/dmsafe.py and saved through
        bin/dmsave.py with that being as <who> — the gate judges it as any commit, and a refused save is undone here,
        its messages returned to the page. The host writes only from a clone with nothing of its own uncommitted."""
        v = self._bound(user, key)
        forms = (v or {}).get("writes") or []
        f = next((x for x in forms if str(x["w"]) == str(w)), None)
        actor = ((self.cfg.get("users") or {}).get(user) or {}).get("bean")
        base = {"user": user, "actor": actor, "view": key, "act": "write", "bean": bean, "head": (self.head or "")[:12]}
        if not f:
            return 404, {"error": "no entry form of that drawing is declared in the ledger"}
        base.update(term=f["term"], entry=entry or None)
        allowed = {a["attr"]: a for a in f["attrs"]}
        given = {k: str(x).strip() for k, x in (values or {}).items() if str(x).strip()}
        bad = sorted(set(given) - set(allowed))
        missing = sorted(a for a, r in allowed.items() if r["required"] and a not in given)
        crooked = sorted(a for a, x in given.items() if "\n" in x or "\r" in x)
        base["values"] = given
        probs = (["the form asks for no %s" % ", ".join(bad)] if bad else []) + \
                (["the law asks for %s" % ", ".join(missing)] if missing else []) + \
                (["a value is one line (%s)" % ", ".join(crooked)] if crooked else []) + \
                (["an entry of %s is named: a short kebab name" % f["term"]]
                 if f["keyed"] and not re.fullmatch(r"[a-z0-9][a-z0-9-]*", entry or "") else []) + \
                (["the garden holds no bean %s" % bean] if not (isinstance(bean, str) and re.fullmatch(r"[A-Za-z0-9_.-]+", bean)
                                                               and vm.fm(bean)) else [])
        if probs:
            self.audit(dict(base, mode="refused", why="; ".join(probs)))
            return 400, {"error": "refused: " + "; ".join(probs)}
        ans = self.may(user, bean, write=True)
        base["answer"] = {"granted": ans[0], "why": ans[1], "grants": [list(g) for g in ans.grants]}
        if not ans[0]:
            self.audit(dict(base, mode="refused", why=ans[1]))
            return 403, {"error": "refused: %s" % ans[1]}
        # EACH VALUE IS ONE VALUE. A value may be a node of its own — `{ scheme: boat-checks, code: hull }`, a quantity —
        # but a viewer's text went into the entry as written, so `hello, by: someone, flag: yes` became three attributes
        # the form never offered. Each value is read alone, as `{ <attr>: <value> }`, and refused unless it is exactly
        # that attribute; and the entry is read again whole, and refused unless it holds exactly the attributes given.
        spill = []
        for a in given:
            try:
                one = vm.dmparse.loads("{ %s: %s }" % (a, given[a]))
            except Exception:
                one = None
            if not (isinstance(one, dict) and list(one) == [a]):
                spill.append(a)
        line = "{ %s }" % ", ".join("%s: %s" % (a, given[a]) for a in allowed if a in given)
        try:
            back = vm.dmparse.loads(line) if not spill else None
        except Exception:
            back = None
        if spill or not (isinstance(back, dict) and set(back) == set(given)):
            why = "a value is one value, of its own attribute (%s)" % ", ".join(spill or sorted(given))
            self.audit(dict(base, mode="refused", why=why))
            return 400, {"error": "refused: %s — nothing written" % why}
        line = ("  %s: %s" % (entry, line)) if f["keyed"] else ("  - %s" % line)
        with self.wlock:
            if self._git("status", "--porcelain").stdout.strip():
                self.audit(dict(base, mode="refused", why="the host's clone has uncommitted changes"))
                return 409, {"error": "refused: the host's clone holds changes not yet committed — nothing written"}
            path = os.path.join(vm.ROOT, "beans", bean + ".md")
            import dmsafe
            try:
                dmsafe.edit(path, lambda text: _add_entry(text, f["term"], line))
            except Exception as e:
                self.audit(dict(base, mode="refused", why="unsafe edit: %s" % e))
                return 400, {"error": "refused: the entry does not read as the term's (%s) — nothing written" % e}
            what = "%s %s on %s, entered on the page" % (f["term"], entry or "entry", bean)
            r = subprocess.run([sys.executable, os.path.join(vm.ROOT, "bin", "dmsave.py"), actor, what, "--body",
                                "- action: %s entered on the page %s (drawing %s) by viewer %s, granted `write` by the law"
                                % (f["term"], vm.PAGE, key, user)],
                               cwd=vm.ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
            out = (r.stdout + r.stderr)[-4000:]
            if r.returncode != 0:
                # undone whole: the clone was clean before, so every change now is this save's
                self._git("reset", "-q")
                for ln in self._git("status", "--porcelain", "-uall").stdout.splitlines():
                    p = ln[3:]
                    if ln.startswith("??"):
                        try:
                            os.remove(os.path.join(vm.ROOT, p))
                        except OSError:
                            pass
                    else:
                        self._git("checkout", "HEAD", "--", p)
                self.audit(dict(base, mode="refused", why="the gate refused the save", rc=r.returncode, output_tail=out[-1500:]))
                return 422, {"error": "the gate refused it — nothing kept", "output": out}
        self.audit(dict(base, mode="saved", rc=0, commit=self.git_head()))
        # the host's own save moves the head by one bean's entry, never the drawings: the page is rebuilt, not re-executed
        # (a re-exec here would drop the answer to the viewer who wrote it)
        self.refresh(force=True, reexec=False)
        return 200, {"mode": "saved", "output": out}

    def run_scheduled(self, at):
        """Every action with `every` whose recurrence falls on `at`'s day, run as the being it names (`answered_by`):
        the host's viewer whose `bean` is that being, asked of the grants like any press. [(view, element, code, answer)]"""
        import dmstale
        day = dmstale.day_of(str(at)[:10])
        out = []
        for key, v in self.views.items():
            for a in v.get("actions") or []:
                if a.get("every") is None:
                    continue
                try:
                    rec = a["every"]
                    if rec.get("from") is None:
                        raise ValueError("a schedule starts `from` a day")
                    due = False
                    for n in dmstale.occurrences(dmstale.day_of(rec["from"]), rec):
                        if n >= day:
                            due = n == day
                            break
                except Exception as e:
                    out.append((key, a["el"], 400, {"error": "its recurrence is not read here: %s" % e})); continue
                if not due:
                    continue
                who = next((n for n, u in (self.cfg.get("users") or {}).items() if u.get("bean") == a.get("answered_by")), None)
                if who is None:
                    self.audit({"user": None, "actor": a.get("answered_by"), "view": key, "element": a["el"], "mode": "refused",
                                "why": "the host has no viewer for the being who answers for this schedule"})
                    out.append((key, a["el"], 403, {"error": "no viewer is %s" % a.get("answered_by")})); continue
                code, obj = self.act(who, key, a["el"], at=str(at), scheduled=True)
                out.append((key, a["el"], code, obj))
        return out

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


def _add_entry(text, term, line):
    """The bean's text with `line` added as the last entry of `term`'s block in its front matter, the block begun at the
    front matter's end where the bean holds none. A term written inline is refused, never rewritten."""
    lines = text.split("\n")
    end = next(i for i in range(1, len(lines)) if lines[i].rstrip() == "---")
    at = next((i for i in range(1, end) if re.match(r"%s:(\s|$)" % re.escape(term), lines[i])), None)
    if at is None:
        return "\n".join(lines[:end] + ["%s:" % term, line] + lines[end:])
    if lines[at].split(":", 1)[1].strip():
        raise ValueError("%s is written inline on this bean; the form adds only to a block" % term)
    j = at + 1
    while j < end and (lines[j].startswith(" ") or not lines[j].strip()):
        j += 1
    while j > at + 1 and not lines[j - 1].strip():
        j -= 1
    return "\n".join(lines[:j] + [line] + lines[j:])


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
                ans = F.may(user)
                F.audit({"user": user, "actor": (F.cfg["users"][user] or {}).get("bean"), "act": "read", "bean": vm.PAGE,
                         "mode": "page", "head": (F.head or "")[:12],
                         "answer": {"granted": ans[0], "why": ans[1], "grants": [list(g) for g in ans.grants]}})
                if not ans[0]:
                    return self._send(403, "refused: %s" % view_report.esc(ans[1]), "text/plain; charset=utf-8")
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
            if u.path == "/api/csv":                 # a table's lines, as this viewer may see them (N36)
                key = urllib.parse.parse_qs(u.query).get("m", [""])[0]
                v = F._bound(user, key)
                t = ((v or {}).get("operate") or {}).get("table")
                if not t:
                    return self._send(404, "no such table", "text/plain")
                import view_export
                F.audit({"user": user, "actor": (F.cfg["users"][user] or {}).get("bean"), "act": "read", "view": key,
                         "mode": "csv", "head": (F.head or "")[:12]})
                return self._send(200, view_export.csv_text(t, keep=lambda b: F.line_ok(user, b, t)), "text/csv; charset=utf-8",
                                  headers={"Content-Disposition": 'attachment; filename="%s.csv"' % re.sub(r"[^A-Za-z0-9_.-]", "", key)})
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
                ins = body.get("inputs") if isinstance(body.get("inputs"), dict) else {}
                code, obj = F.act(user, str(body.get("m", "")), str(body.get("el", "")), inputs=ins,
                                  reason=str(body["reason"]) if body.get("reason") else None)
                return self._json(code, obj)
            if u.path == "/api/write":
                try:
                    body = json.loads(raw or "{}")
                except ValueError:
                    return self._json(400, {"error": "bad json"})
                F.refresh()
                vals = body.get("values") if isinstance(body.get("values"), dict) else {}
                code, obj = F.write(user, str(body.get("m", "")), str(body.get("w", "")), str(body.get("bean", "")),
                                    str(body.get("entry") or ""), vals)
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
