#!/usr/bin/env python3
"""view_serve — the `view` asset's served page and action executor: the offline report, made live, served from a host.

WHY A SERVER OF ITS OWN. A page served by the asset can do what a static file cannot:
  - SCOPE what it sends. Who may see what is the LEDGER's — the grants its beings hold, asked of bin/pass.py `may`
    for the being the host names for the viewer (`bean`) — and one function answers it, `Host.may(user, bean, act,
    positions, write)`: "may this viewer see this bean, or this part of it, run this action, write here?". The
    documentation the page sends (reference rows, part cards, addresses, wiring), a table's lines, a funnel's counts,
    the values it reads, every action and every write pass through it. Where only a part of a bean is granted
    (`positions`), only that part is sent, marked a part. The page never sends a query; it asks for a drawing's values
    and the server builds the queries itself.
  - ACT: a button on a drawing runs a tool the host names; an action with `every` runs on its schedule as the being who
    answers for it (`run_scheduled`), asked like a press.
  - WRITE: a sheet's Save, or a drawing's form of a verb, writes statements through the view's one write path
    (view_write.py, `ops`), and a drawing's entry form in today's words (`views.writes`) adds an entry of a term the law
    gives, through bin/save.py as the viewer's being; the gate judges it, and a refused save is undone and its message
    shown (`/api/write`).
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

SESSIONS. A sign-in form; a signed, expiring, HttpOnly, SameSite=Strict cookie, signed over the viewer's stored
password too, so a password changed voids every session signed before it; a CSRF token on every POST, signing out
among them, and a sign-in is taken only from the page's own origin. Passwords are stored as PBKDF2-SHA256 hashes in the host's configuration, never in git, and a name nobody
holds is checked against a hash of the same rounds, so the answer's time tells nobody who is kept here. `view
serve-init` writes the configuration with a random password in a 0600 file beside it — never printed — and `serve`
refuses a configuration others may read: it holds the session key and the password hashes.

A STRANGER LOCKS NOBODY OUT. Failures are counted per address and name, and per address; past a ceiling of failures
for one name, a stranger is refused even with the right password — and a viewer this browser has signed in as before
(the `view_known` cookie, signed over their password) is asked their password still, held only by their own failures.
Behind a proxy the configuration trusts (`"trusted_proxies": ["127.0.0.1", "::1"]`), the address counted is the client
the proxy names in `X-Forwarded-For` (the rightmost that is no trusted proxy); from any other peer the header is ignored.

ONE ADDRESS, ITS OWN NAMES, ITS OWN SCRIPTS. The page listens on the loopback (`listen`, 127.0.0.1:8780 by default);
an address beyond it is refused unless the configuration says `"listen_beyond_loopback": true` — passwords and
sessions would otherwise cross a network in clear: serve it beyond this machine through a proxy that speaks TLS, which
passes `X-Forwarded-Proto: https` (or set `"secure_cookie": true`). It answers only to its own names — its address,
the loopback's and the `hosts` its configuration lists, such as the name a proxy passes on — so a page served under a
stranger's name (DNS rebinding) is refused. Every answer carries a Content-Security-Policy: no source by default, and
the page's own scripts (view_report.SCRIPTS) by their hashes, nothing else that runs.

THE LEDGER IS READ AGAIN when the garden's git HEAD moves (asked at most every `recheck_seconds`, 30 by default, and
only for a signed-in viewer: a health check answers from what is held). When it moves, or the release GARDEN.md records
moves, and no code moved with it, the server runs `view check` on the new state, and only if it passes starts itself
again on it; until then it keeps serving what it had. CODE RUNS ONLY WHEN A PERSON STARTS IT: when the drawing module
the page names, or the release's assets, changed since the server was started, it keeps serving what it started with
and says that `view serve` must be run again by hand — whoever made the commit.

A CONNECTION IS BOUNDED: one that sends no request within `request_seconds` (15 by default) is closed, and at most 64
are held at once; past that a new one is closed at once rather than given a thread.

Usage (through assets/view/bin/view.py):
  view serve-init --config <path> --user <name> [--orgs "*"|org-a,org-b] [--shared] [--no-actions]
  view serve --config <path>
"""
import base64, hashlib, hmac, html, ipaddress, json, math, os, re, secrets, socket, subprocess, sys, threading, time, urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import view_model as vm
import view_report

# The rows of the flow law this tool checks, and the fixture that shows it (`bin/pass.py --flows` computes the guard).
GUARDS = {
    'served': {'checks': "a page or an action is served only where a grant opens it to the viewer, asked before each",
               'proof': 'test/view.py', 'label': "serve: carol, granted what no organisation owns, sees the radio"},
}

SESSION_HOURS = 12
PBKDF2_ROUNDS = 200000
COOKIE = "view_session"
KNOWN, KNOWN_DAYS = "view_known", 90       # the browser a viewer signed in with (see A STRANGER LOCKS NOBODY OUT)
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


_DUMMY = []


def dummy_hash():
    """A hash of the stored kind and rounds, of no one's password: what a name nobody holds is checked against."""
    if not _DUMMY:
        _DUMMY.append(hash_password(secrets.token_hex(16)))
    return _DUMMY[0]


def _write_private(path, text):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as fh:
        fh.write(text)


def loopback(host):
    """Whether `host` is this machine's loopback: 127.0.0.0/8, ::1, or `localhost`."""
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def listen_of(cfg):
    """(host, port) the page listens on: the configuration's `listen` — no address at all is the loopback, as `serve` has
    always read it — refused (SystemExit, before anything is bound) where it is beyond the loopback and the configuration
    does not choose that in as many words, `"listen_beyond_loopback": true` (security audit 2026-10-10, 3.2)."""
    listen = str(cfg.get("listen") or "127.0.0.1:8780")
    host, _, port = listen.rpartition(":")
    host = host.strip("[]") or "127.0.0.1"
    if not port.isdigit():
        raise SystemExit("view serve: `listen` is <address>:<port>, and %r is not — nothing is bound" % listen)
    if not loopback(host) and cfg.get("listen_beyond_loopback") is not True:
        raise SystemExit("view serve: `listen` is %s, beyond this machine's loopback, where passwords and sessions would "
                         "cross the network in clear — listen on 127.0.0.1 and serve the page beyond this machine through "
                         "a proxy that speaks TLS, or say `\"listen_beyond_loopback\": true` in the host's configuration "
                         "to choose it; nothing is bound" % listen)
    return host, int(port)


def private_config(path):
    """Refuse (SystemExit) a configuration others may read: it holds the session key, which signs every viewer's session,
    and the password hashes (security audit 2026-10-10, 3.11). Where the system has no such modes, nothing is asked."""
    if os.name != "posix":
        return
    mode = os.stat(path).st_mode & 0o777
    if mode & 0o077:
        raise SystemExit("view serve: %s may be read by others (mode %o), and it holds the session key and the password "
                         "hashes — `chmod 0600` it, as `serve-init` writes it; nothing is served" % (path, mode))


def _address(a):
    """An address as one writes it once: `::ffff:127.0.0.1` and `[::1]` as `127.0.0.1` and `::1`; None if it is none."""
    try:
        ip = ipaddress.ip_address(str(a).strip().strip("[]"))
    except ValueError:
        return None
    return str(ip.ipv4_mapped or ip) if ip.version == 6 else str(ip)


def source_of(peer, forwarded, trusted=()):
    """Who is signing in, as far as the host can tell: the address the connection comes from — or, where that is a proxy
    the host's configuration trusts (`trusted_proxies`), the client it names: the rightmost address of
    `X-Forwarded-For` that is not itself a trusted proxy. A header from any other peer is ignored, and so is one that
    names no address."""
    trusted = {t for t in (_address(x) for x in trusted or ()) if t}
    if not forwarded or _address(peer) not in trusted:
        return peer
    for a in reversed(forwarded.split(",")):
        a = _address(a)
        if a and a not in trusted:
            return a
        if not a:
            break
    return peer


def finite(x):
    """A monitor's value as JSON can carry it: a number that is no finite number — Prometheus's NaN for a ratio of 0/0,
    and ±Inf — is written as the word JavaScript reads it back by, "NaN", "Infinity" or "-Infinity", apart from null,
    a value nobody gave (security audit 2026-10-10, 3.7)."""
    if isinstance(x, float) and not math.isfinite(x):
        return "NaN" if x != x else "Infinity" if x > 0 else "-Infinity"
    if isinstance(x, dict):
        return {k: finite(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [finite(v) for v in x]
    return x


def _tail_lines(path, n, block=65536):
    """The last `n` lines of a file, read from its end: a log that grows for years costs what is asked of it."""
    with open(path, "rb") as fh:
        fh.seek(0, os.SEEK_END)
        pos, buf = fh.tell(), b""
        while pos > 0 and buf.count(b"\n") <= n:
            step = min(block, pos)
            pos -= step
            fh.seek(pos)
            buf = fh.read(step) + buf
    return buf.decode("utf-8", "replace").splitlines()[-n:]


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

_NIP = re.compile(r'<text [^>]*class="nip" data-addr-of="([^"]*)"[^>]*>[^<]*</text>')


def strip_addresses(svg, ok):
    """A private page's drawing as a viewer may see it: each part's address that belongs to a being the viewer may not
    see is taken out. What the drawing's own text says belongs to no being, and stays, as the page's `visibility` says."""
    return _NIP.sub(lambda m: m.group(0) if not m.group(1) or ok(html.unescape(m.group(1))) else "", svg)


_BEAN = re.compile(r' data-bean="([^"]*)"')


def strip_beans(svg, gone):
    """A drawing as a viewer may see it: the mark of the being a part depicts (`data-bean`) is taken off a part whose
    being the viewer may not see (3.8). The part stays as drawn: its words are the drawing's."""
    return _BEAN.sub(lambda m: "" if gone(html.unescape(m.group(1))) else m.group(0), svg)


def _hashes(scripts):
    return " ".join("'sha256-%s'" % base64.b64encode(hashlib.sha256(x.encode("utf-8")).digest()).decode() for x in scripts)


# THE PAGE'S POLICY (security audit 2026-10-10, 3.9): nothing loads or runs but what the page is — its own scripts by
# their hashes (view_report.SCRIPTS: the scripts the asset writes, never the ones a page happens to hold), its own
# style and pictures, its calls to itself. Every other answer runs nothing at all.
CSP = ("default-src 'none'; style-src 'unsafe-inline'; img-src 'self' data:; form-action 'self'; base-uri 'none'; "
       "frame-ancestors 'none'")
PAGE_CSP = CSP + "; script-src %s; connect-src 'self'" % _hashes(view_report.SCRIPTS)

class Verdict(tuple):
    """(yes, why), and the grants the answer read — compares as the pair it is."""
    def __new__(cls, yes, why, grants=(), reason_asked=False):
        t = tuple.__new__(cls, (bool(yes), why))
        t.grants, t.reason_asked = list(grants), bool(reason_asked)
        return t


def given_by_person(i):
    """Whether an action's input is a value the person pressing gives: any `origin` but the clock's, `{act: read, nature:
    soma, by: reader}` (core/law/profiles.yaml `actions.inputs.origin`), which the host reads itself."""
    o = i.get("origin") if isinstance(i.get("origin"), dict) else {}
    return not (o.get("act") == "read" and o.get("by") == "reader")


def optional(i):
    """Whether a person may leave an action's input empty (core/law/profiles.yaml `actions.inputs.optional`, ratified
    2026-10-13): left empty, the tool is given no value of that name — absent, never an empty one, its meaning the
    tool's own (no note, no cost centre, today's day). Any other input a person gives is asked, and nothing starts
    without it."""
    return i.get("optional") in ("true", True)


class Host:
    def __init__(self, config, argv=None):
        self.config_path = config
        self.cfg = json.load(open(config))
        self.key = bytes.fromhex(self.cfg["session_key"])
        self.lock = threading.Lock()
        self.wlock = threading.Lock()                # one form's save at a time in this host; save's own lock queues others
        self.head, self.checked, self.payload, self.views = None, 0, None, {}
        self.fails = {}                              # what failed to sign in -> [its moments in the window]
        self.flock = threading.Lock()                # threads sign in at once: the failures are counted under it
        self.closed_memo = {}                        # viewer -> (head, day, the beings they may not see, a pattern of them)
        self.revoked = self._load_revoked()          # the signatures of tokens signed out, until each would expire
        self.beans, self.gardener, self.answers = {}, None, {}
        self.argv = argv or sys.argv
        self.release_at_start = self.release()
        self.head_at_start, self.code_noted = self.git_head(), None
        self.refresh(force=True)

    # --- MAY THIS VIEWER SEE THIS BEAN, OR RUN THIS ACTION -----------------------------------------------------------
    # The one place the answer is given (24.0, N33). The host's configuration is a CEILING: it can narrow what a viewer
    # is sent (orgs, shared, beans, actions), and never widen it. What opens a page, a bean or an action is a grant the
    # law declares, asked of `bin/pass.py` for the being the host names for this viewer — before every page, value,
    # history and action.
    def may(self, user, bean=None, act=False, tool=None, positions=None, reason=None, write=False, held=False):
        """(yes, why) — whether `user` may see `bean` (None: the page itself), at `positions` (None: the whole bean), and,
        with `act`, run `tool` on it, or with `write`, write it; with `held`, at positions that hold a value held off git,
        which only a grant naming them opens (bin/pass.py `may_core`). The answer also carries `.grants` (every grant
        read) and `.reason_asked`."""
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
        # AN ANSWER HOLDS FOR THE MINUTE IT WAS ASKED IN. A grant's `at` is read by the day (pass `_during`), and an
        # answer kept until the next commit went on granting past a grant's last day; a grant's `window` opens and
        # closes at a time of day (`5T08:30`), so an answer kept for the day went on granting after hours: the cache is
        # the minute's — a window that lasts a length of whole minutes opens and closes on a minute, and one that does
        # not is seen at the next.
        minute = int(time.time() // 60)
        if getattr(self, "answers_minute", None) != minute:
            self.answers, self.answers_minute = {}, minute
        k = (actor, what, target, tuple(positions) if positions else None, bool(reason), bool(held))
        a = self.answers.get(k)
        if a is None:
            import importlib
            dmpass = importlib.import_module('pass')
            a = dmpass.may(actor, what, target, positions=positions, reason=reason, root=vm.ROOT, beans=self.beans,
                           gardener=self.gardener, **({'held': True} if held else {}))
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
                    raise SystemExit("view serve: the page and its drawings disagree:\n  - " + "\n  - ".join(errs))
                sys.stderr.write("view serve: the ledger at %s does not check; still serving %s\n" % (h[:10], (self.head or "")[:10]))
                return
            self.payload, self.head = view_report.payload(), h
            import importlib
            dmpass = importlib.import_module('pass')
            self.beans, self.gardener, self.answers = dmpass.beans_here(vm.ROOT), dmpass.gardener_of(vm.ROOT), {}
            self.views = {v["key"]: v for v in self.payload["views"].values()}

    def code_moved(self, old, new):
        """The files of code this server runs that changed between two ledger heads: the drawing module the page names,
        and the release's assets. None changed, or no history to tell by: []. An unreadable answer is a change."""
        if not old or old == "no-git" or old == new:
            return []
        try:
            rel = os.path.relpath(vm.drawings_path() or "", vm.ROOT)
        except Exception:
            rel = ""
        paths = [p for p in (rel, "assets") if p and not p.startswith("..")]
        r = subprocess.run(["git", "-C", vm.ROOT, "diff", "--name-only", old, new, "--"] + paths, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        if r.returncode != 0:
            return ["the ledger's history"]
        return sorted({f.split("/")[0] if f.startswith("assets/") else f for f in r.stdout.split() if f})

    def maybe_reexec(self):
        """The code that serves must be the release the garden records, and the drawings the ledger names. When a pull
        brings a new ledger head (which may carry a changed drawing module this process holds an old import of) or a new
        release, start again on it — only once `view check` passes on it; while it does not, keep serving and say why."""
        new = self.release()
        head = self.git_head()
        head_moved = self.payload is not None and head != self.head
        if new == self.release_at_start and not head_moved:
            return
        # CODE RUNS ONLY WHEN A PERSON STARTS IT (security audit 2026-10-10, 3.4): a pull that changes the drawing module
        # or the release's assets is not run by this server — not by `view check`, not by starting again — whoever made
        # the commit; it keeps serving what it started with, and says a person must start it again
        moved = self.code_moved(self.head_at_start, head)
        if moved:
            if moved != self.code_noted:
                sys.stderr.write("view serve: %s changed since this server was started (now %s): code is run only when a "
                                 "person starts it — run `view serve` again by hand\n" % (", ".join(moved), head[:10]))
                self.code_noted = moved
            return
        probs = subprocess.run([sys.executable, os.path.join(os.path.dirname(HERE), "bin", "view.py"), "check",
                                "--garden", vm.ROOT] + (["--page", vm.PAGE] if vm.PAGE else []), capture_output=True, text=True, encoding="utf-8", errors="replace")
        if probs.returncode != 0:
            sys.stderr.write("view serve: the pulled ledger or release does not check; still serving %s\n" % self.release_at_start)
            return
        sys.stderr.write("view serve: reloading (release %s -> %s, or a new ledger head)\n" % (self.release_at_start, new))
        sys.stderr.flush()
        os.execv(sys.executable, [sys.executable] + self.argv)

    # --- what a viewer is sent ---
    def set_prefs(self, user, prefs):
        """A viewer's own way of reading (view_prefs.check's), kept in the host's configuration beside their account —
        on this machine, for every browser they sign in from, never in git — and the pages it drew for them read again."""
        with self.lock:
            cfg = json.load(open(self.config_path))
            rec = cfg["users"][user]
            for k in ("locale", "date", "currency"):
                if prefs.get(k):
                    rec[k] = prefs[k]
                else:
                    rec.pop(k, None)
            import safe as dmsafe           # whole, flushed and swapped in: the file keeps the mode its keeper gave it
            dmsafe.write_atomic(self.config_path, json.dumps(cfg, indent=1), mode=0o600)
            self.cfg["users"][user] = rec
            self._engraved = None

    def closed(self, user):
        """(the beings of the garden `user` may not see, a pattern that finds one named in a value's query): asked of the
        grants once a head and a day, as every answer is."""
        key = (self.head, int(time.time() // 86400))
        m = self.closed_memo.get(user)
        if not m or m[0] != key:
            gone = frozenset(b for b in (self.payload or {}).get("beans") or {} if not self.may(user, b)[0])
            # named in a query as a label's value or a step of a JSON Pointer: delimited by a quote, a bar or a slash. A
            # technology's code in the published catalogue (`job="prometheus"`) names the technology as much as the being
            # a garden keeps for it, and is no name of a being in a query.
            words = sorted(gone - set((self.payload or {}).get("techcat") or {}), key=len, reverse=True)
            rx = re.compile(r"(?:^|(?<=[\"'/|]))(?:%s)(?=[\"'/|]|$)" % "|".join(map(re.escape, words))) if words else None
            m = self.closed_memo[user] = (key, gone, rx)
        return m[1], m[2]

    def bind_shown(self, user, b):
        """Whether a value is shown to `user`: its probe is a being they may see, and its query names none they may not."""
        if b.get("probe") and not self.may(user, b["probe"])[0]:
            return False
        rx = self.closed(user)[1]
        return not (rx and any(isinstance(t, str) and rx.search(t) for t in [b.get("source")] + list((b.get("query") or {}).values())))

    def scoped_payload(self, user):
        """The page as `user` may see it: every being they may not see taken out of what is sent, and every drawing of a
        being they may not see — and named nowhere (security audit 2026-10-10, 3.8): not as the part an element depicts
        (its picture's mark of it too), a value's probe or query, the being an action acts on or answers for it, a step's
        or a story's parts, a board's member, where the page is shown, who stated it, the organisation it opens on. The
        drawing's own words stay, as its picture does: an element's id is the slug of the label the drawing shows."""
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
        # WHO IS NAMED: a being of the garden the viewer is sent, whole or in part, and the page itself; any other is named
        # nowhere a being is named. A word that is no being's id (a series' item) is no name. A bean sent in part says
        # which organisation owns it only where the viewer may see that one too.
        named = set(beans) | {vm.PAGE}
        gone = lambda b: isinstance(b, str) and b in self.closed(user)[0] and b not in named
        for b, v in beans.items():
            if v.get("part") and gone(v.get("org")):
                v["org"] = None
        if gone(p.get("opens_on")):
            p["opens_on"] = ""
        hosts = [pl.get("host") for pl in (p.get("where") or {}).get("places") or [] if pl.get("host")]
        if any(gone(b) for b in hosts + [(vm.fm(h).get("lives_in") or {}).get("bean") for h in hosts
                                         if isinstance(vm.fm(h).get("lives_in"), dict)]):
            svg, places = vm.where_shown(shows=lambda b: not gone(b))
            p["where"] = {"svg": svg, "places": places}
        for k in list(p["views"]):
            v = p["views"][k]
            if v.get("draws_bean") and not ok(v["draws_bean"]):
                del p["views"][k]
                p["order"] = [x for x in p["order"] if x != k]
                continue
            hid = {e["id"] for e in v.get("elements") or [] if gone(e.get("bean"))
                   or (isinstance(e.get("of"), dict) and gone(e["of"].get("bean")))}
            for e in v.get("elements") or []:
                if gone(e.get("bean")):
                    e["bean"] = None
                if isinstance(e.get("of"), dict) and gone(e["of"].get("bean")):
                    e["of"] = None
            v["changed"] = [i for i in v.get("changed") or [] if i not in hid]
            v["binds"] = [b for b in v.get("binds") or [] if self.bind_shown(user, b)]
            shown = {b["id"] for b in v["binds"]}
            v["actions"] = [a for a in v.get("actions") or [] if not gone(a.get("bean"))]
            for a in v["actions"]:
                if gone(a.get("answered_by")):
                    a["answered_by"] = None
            for st in v.get("steps") or []:
                st["parts"] = [b for b in st.get("parts") or [] if not gone(b)]
            for st in (v.get("story") or {}).get("stages") or []:
                st["parts"] = [x for x in st.get("parts") or [] if not gone(x.get("title"))]
            if gone((v.get("sheet") or {}).get("by")):
                v["sheet"]["by"] = ""
            v["facts"] = {b: f for b, f in (v.get("facts") or {}).items() if ok(b)}
            v["svg"] = strip_beans(strip_addresses(v.get("svg") or "", ok), gone)
            v["parts"] = [x for x in (v.get("parts") or []) if ok(x["bean"])]
            if v.get("wiring") and not ok(v["wiring"]["bean"]):
                v["wiring"] = None
            v["tiles"] = [t for t in v.get("tiles") or [] if not t.get("bean") or ok(t["bean"])]
            for t in v["tiles"]:
                if "binds" in t:
                    t["binds"] = [i for i in t["binds"] if i in shown]
            op = v.get("operate") or {}
            if op.get("table"):                      # a line of a table shows the parts of one being its columns read:
                op["table"]["rows"] = [r for r in op["table"]["rows"] if self.line_ok(user, r["bean"], op["table"])]
            for f in op.get("funnels") or []:          # a reading's count is of the members this viewer may see
                for st in f.get("stages") or []:
                    if st.get("members") is not None:
                        st["static"] = sum(1 for m in st["members"] if ok(m))
                    st.pop("members", None)
            for it in op.get("items") or []:
                if gone(it.get("bean")):
                    it["bean"] = None
            for rc in op.get("rollcall") or []:
                rc["idle"] = [x for x in rc.get("idle") or [] if not gone(x)]
                rc["notes"] = {x: n for x, n in (rc.get("notes") or {}).items() if not gone(x)}
            # the alert rules that watch this drawing, as the parts and the values it is sent read them
            v["alerts"] = vm.alert_names([x["bean"] for x in v["parts"]], v["binds"]) if v.get("alerts") else []
        import view_engraved                         # the readings the engraved drawings draw: this viewer's own, never
        p["engraved"] = view_engraved.scoped(self, user, keep=set(p["views"]))   # the gardener's the report reads
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
            if not self.bind_shown(user, b):          # a being the viewer may not see is not asked about, nor named
                continue
            by_monitor.setdefault(b.get("monitor"), []).append(b)
        for mon, binds in by_monitor.items():
            m = next((x for x in vm.monitors() if x["bean"] == mon), None)
            url = ((self.cfg.get("monitors") or {}).get(mon) or {}).get("url") if mon else None
            if not m or not m["adapter"] or not url:
                out.update({b["id"]: None for b in binds}); continue
            sel = m["adapter"].selector(self.scope(user))
            out.update(finite(m["adapter"].values(url, binds, sel)))
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
            if b.get("live") == "live-value" and self.bind_shown(user, b):
                by_monitor.setdefault(b.get("monitor"), []).append(b)
        for mon, binds in by_monitor.items():
            m = next((x for x in vm.monitors() if x["bean"] == mon), None)
            url = ((self.cfg.get("monitors") or {}).get(mon) or {}).get("url") if mon else None
            if not m or not m["adapter"] or not url:
                out.update({b["id"]: [] for b in binds}); continue
            out.update(finite(m["adapter"].history(url, binds, m["adapter"].selector(self.scope(user)), hours, step, now)))
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
        given = {k: str(x) for k, x in (inputs or {}).items()       # a value left empty is no value: absent, or asked
                 if k in declared and x is not None and str(x).strip()}
        undeclared = sorted(set(inputs or {}) - set(declared))
        missing = sorted(n for n, i in declared.items() if n not in given and given_by_person(i) and not optional(i))
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

    # --- A RUN STARTED FROM A PAGE: a walk of the garden, with the inputs its action declares -------------------------
    # An action on a drawing engraved from a reading (a table's line, a sheet: view_engraved `ACTION_ELEMENTS`) names a
    # `tool` the host maps to a WALK of the garden (`tools: { <name>: { walk: <walk> } }`): what a page may start is the
    # host's to say. Started by bin/act.py `--start`, as the viewer's being, with the inputs given: the engine runs the
    # walk's tool to its plan and stops where a person ratifies; `decide` is that person's ratification, or refusal.
    def _act_py(self, *args):
        r = subprocess.run([sys.executable, os.path.join(vm.ROOT, "bin", "act.py")] + [str(a) for a in args], cwd=vm.ROOT,
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=3600)
        return r.returncode, (r.stdout + r.stderr).strip()

    def _plan_of(self, bean, course, step="plan"):
        d = os.path.join(vm.ROOT, "captures", "actions")
        caps = sorted((f for f in os.listdir(d) if f.startswith("%s.%s.%s." % (bean, course, step))),
                      key=lambda f: int(f.rsplit(".", 2)[-2]) if f.rsplit(".", 2)[-2].isdigit() else 0) if os.path.isdir(d) else []
        return open(os.path.join(d, caps[-1]), encoding="utf-8", errors="replace").read() if caps else ""

    def _refusal_of(self, bean, course, stands):
        """What a walk said as it refused a run: the last line of the capture of the last step it reached (verify,
        apply, check, plan); where that step said nothing, where the run stands."""
        d = os.path.join(vm.ROOT, "captures", "actions")
        have = os.listdir(d) if os.path.isdir(d) else []
        for step in ("verify", "apply", "check", "plan"):
            if any(f.startswith("%s.%s.%s." % (bean, course, step)) for f in have):
                said = [x for x in self._plan_of(bean, course, step).splitlines() if x.strip()]
                return said[-1].strip() if said else stands
        return stands

    def start(self, user, key, el, tool, bean, inputs=None, reason=None):
        """Start the walk the host maps `tool` to, on `bean`, for `user`: the action declared on `el` of drawing `key`,
        its inputs as it declares them, asked of the law as `act:<tool>` for the viewer's being. (status, answer): the
        run's course, where it stopped, and the plan it would apply, for a person to ratify.

        AN ACTION'S INPUTS (ratified 2026-10-13): on a row of a sheet (`el` a verb), `bean` names the row's statement,
        `<bean>#<id>`, which must be one of that verb in that bean; an input filled `from` the element is the host's to
        fill, whatever the page sent; one chosen `of` a reading or a scheme must be one of the choices this viewer is
        offered (a heading never); `many` takes a list; a `file` is kept off git under its SHA-256, the run given that.
        One a person may leave empty (`optional`) and left so is not given at all: the walk reads it absent, its meaning
        the walk's own; any other left empty, or filled from an element that gives none, starts nothing."""
        v = self._bound(user, key)
        a = next((x for x in (v or {}).get("actions", []) if x["el"] == el and x["tool"] == tool), None)
        actor = ((self.cfg.get("users") or {}).get(user) or {}).get("bean")
        base = {"user": user, "actor": actor, "view": key, "element": el, "tool": tool, "act": "act:" + str(tool),
                "bean": bean, "head": (self.head or "")[:12], "reason": reason or None}
        bean, _sep, stmt = str(bean or "").partition("#")
        bean = (a or {}).get("bean") or bean          # an action fixed on one being (`acts_on`) acts on that one
        base["bean"] = bean + ("#" + stmt if stmt else "")
        if not a or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,120}", str(bean or "")):
            return 404, {"error": "no action is declared on that element in the ledger"}
        verbs = vm.CORE.L.verbs if vm.CORE is not None else {}
        if el in verbs:                               # a row of a sheet: one statement of that verb in that bean
            b = vm.CORE.G.beans.get(bean)
            row = next((r for _i, vb, r in (b.items if b is not None else []) if vb == el and r.get("id") == stmt
                        and "held" not in r), None) if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,120}", stmt or "") else None
            if row is None:
                return 404, {"error": "no %s %r in %s: the action sits on a row of its sheet" % (el, stmt, bean)}
        elif stmt:
            return 400, {"error": "the action sits on the being, not on a row of it"}
        else:
            row = None
        import view_engraved as ve                    # the choices an input offers this viewer, as the page drew them
        declared = {i.get("name"): i for i in a.get("inputs") or []}
        undeclared = sorted(set(inputs or {}) - set(declared) - {n for n, i in declared.items() if i.get("from")})
        given, why = {}, []
        mine = lambda act, b, *x, **k: self.may(user, b)[0]
        for name, i in declared.items():
            if i.get("from"):                          # the host's to fill, never the page's, and never empty
                got = self._filled(bean, stmt, row, i["from"])
                if got:
                    given[name] = got
                else:
                    why.append("%s: the element gives none (%s)" % (name, i["from"]))
                continue
            got = (inputs or {}).get(name)
            if str(i.get("type") or "") == "file":
                if got in (None, "", {}):
                    continue
                sha, err = self._keep_file(got)
                if err:
                    why.append("%s: %s" % (name, err))
                else:
                    given[name] = sha
                continue
            vals = got if isinstance(got, list) else ([] if got in (None, "") else [got])
            vals = [str(x) for x in vals if str(x).strip()]
            if len(vals) > 1 and i.get("many") not in ("true", True):
                why.append("%s: one value, not %d" % (name, len(vals)))
                continue
            if i.get("of"):
                offered = {c["value"] for c in (ve.input_choices(i, mine) or []) if not c.get("disabled")}
                wrong = [x for x in vals if x not in offered]
                if wrong:
                    why.append("%s: %s is no choice offered here" % (name, ", ".join(wrong)))
                    continue
            if vals:
                given[name] = vals if i.get("many") in ("true", True) else vals[0]
        # A LIST BESIDE A LIST (the law's `beside`, ratified 2026-10-14): given row by row, so of one length — a person
        # beside their share; one given without the other is half a row
        for name, i in declared.items():
            other = i.get("beside")
            if other and (name in given or other in given):
                if name not in given or other not in given or len(given[name]) != len(given[other]):
                    why.append("%s: given row by row beside %s, one value of each a row (%d and %d)"
                               % (name, other, len(given.get(name) or []), len(given.get(other) or [])))
        missing = sorted(n for n, i in declared.items() if n not in given and given_by_person(i) and not i.get("from")
                         and not optional(i) and not any(n in w.split(":")[0] for w in why))
        base["inputs"] = given
        if undeclared or missing or why:
            self.audit(dict(base, mode="refused", why="inputs"))
            return 400, {"error": "refused: " + "; ".join(
                (["the action declares no input %s" % ", ".join(undeclared)] if undeclared else []) +
                (["the action asks for %s" % ", ".join(missing)] if missing else []) + why)}
        if a.get("reason") and not reason:
            return 400, {"error": "refused: the action asks a reason", "reason_asked": True}
        ans = self.may(user, bean, act=True, tool=tool, reason=reason)
        base["answer"] = {"granted": ans[0], "why": ans[1], "grants": [list(g) for g in ans.grants]}
        if not ans[0]:
            self.audit(dict(base, mode="refused", why=ans[1]))
            return 403, {"error": "refused: %s" % ans[1], "reason_asked": ans.reason_asked}
        walk = ((self.cfg.get("tools") or {}).get(tool) or {}).get("walk")
        if not walk:
            self.audit(dict(base, mode="refused", why="the host maps the tool to no walk"))
            return 403, {"error": "the host starts no walk for tool %r — nothing ran" % tool}
        args = [bean, "--start", walk, "--by", actor]
        for k, w in sorted(given.items()):             # a list given as its values, each an `--input` of the name,
            for x in (w if isinstance(w, list) else [w]):  # and named a list, so a list of one stays one
                args += ["--input", "%s=%s" % (k, x)]
            if isinstance(w, list):
                args += ["--list", k]
        with self.wlock:
            rc, out = self._act_py(*args)
        m = re.search(r"^act: \S+ (run-\d+): (.*)$", out, re.M)
        course = m.group(1) if m else None
        # A RUN ITS WALK REFUSED, OR ROLLED BACK, BEFORE ANY PERSON'S STEP (an action's walk ends at `refused` or
        # `rolled-back`, bin/act.py): answered refused, in the walk's own words — never a plan a person could ratify
        ended = bool(m) and re.match(r"stopped at (refused|rolled-back)\b", m.group(2)) is not None
        self.audit(dict(base, mode="refused" if rc != 0 or ended else "started", walk=walk, course=course, rc=rc,
                        output_tail=out[-1500:]))
        if rc != 0:
            return 422, {"error": out.splitlines()[-1][:600] if out else "the run did not start"}
        self.refresh(force=True, reexec=False)
        if ended:
            return 422, {"error": "refused: " + self._refusal_of(bean, course, m.group(2))[:600], "bean": bean,
                         "course": course}
        return 200, {"mode": "started", "bean": bean, "course": course, "stands": m.group(2) if m else out[-300:],
                     "plan": self._plan_of(bean, course) if course else ""}

    def _filled(self, bean, stmt, row, path):
        """An input filled from the element: `self` its own (the row's statement `<bean>#<id>`, or the being), or a path
        into it — into the row's roles on a row, into the being's front matter on a line or a sheet."""
        if path == "self":
            return "%s#%s" % (bean, stmt) if stmt else bean
        if row is not None:
            x = row
            for part in str(path).split("."):
                x = x.get(part) if isinstance(x, dict) else None
            return "" if x is None else str(x)
        import reckon as dmreckon
        got = dmreckon.path_values(vm.fm(bean), str(path), root=vm.ROOT)
        return str(got[0]) if isinstance(got, list) and got else ("" if got in (None, []) else str(got))

    def _keep_file(self, got):
        """A file a person gave, kept off git under its SHA-256 in the garden's git directory (`daftar-inputs/`, readable
        by its owner alone), at most the host's bound (`file_bound`, 16 MiB unless set): (sha-256, None) or (None, why).
        Its bytes are never written to the audit, the ledger or the run's capture: its SHA-256 is."""
        import base64, hashlib
        if not isinstance(got, dict) or not isinstance(got.get("data"), str):
            return None, "a file is given as its name and its bytes"
        bound = int(self.cfg.get("file_bound") or 16 * 2 ** 20)
        if len(got["data"]) > (bound * 4) // 3 + 4:
            return None, "the file is larger than this host takes (%d bytes)" % bound
        try:
            data = base64.b64decode(got["data"], validate=True)
        except (ValueError, TypeError):
            return None, "the file's bytes do not read"
        if len(data) > bound:
            return None, "the file is larger than this host takes (%d bytes)" % bound
        sha = hashlib.sha256(data).hexdigest()
        r = subprocess.run(["git", "-C", vm.ROOT, "rev-parse", "--absolute-git-dir"], capture_output=True, text=True,
                           encoding="utf-8")
        if r.returncode:
            return None, "no garden's git directory to keep it in"
        d = os.path.join(r.stdout.strip(), "daftar-inputs")
        os.makedirs(d, mode=0o700, exist_ok=True)
        path = os.path.join(d, sha)
        if not os.path.isfile(path):
            fd = os.open(path + ".part", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "wb") as fh:
                fh.write(data)
            os.replace(path + ".part", path)
        return sha, None

    def decide(self, user, bean, course, do):
        """A person's ratification of a run's plan, or their refusal of it (bin/act.py `--ratify`, `--decline`): who may
        is the walk's and the law's to say, and bin/act.py asks it. (status, answer)."""
        actor = ((self.cfg.get("users") or {}).get(user) or {}).get("bean")
        base = {"user": user, "actor": actor, "act": do, "bean": bean, "course": course, "head": (self.head or "")[:12]}
        if do not in ("ratify", "decline") or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,120}", str(bean or "")) \
                or not re.fullmatch(r"run-\d+", str(course or "")) or not actor:
            return 400, {"error": "a decision names the run (its bean and course) and ratify or decline"}
        with self.wlock:
            rc, out = self._act_py(bean, course, "--" + do, actor)
        self.audit(dict(base, mode="decided" if rc == 0 else "refused", rc=rc, output_tail=out[-1500:]))
        if rc != 0:
            return 422, {"error": out.splitlines()[-1][:600] if out else "nothing was decided"}
        self.refresh(force=True, reexec=False)
        return 200, {"mode": do, "bean": bean, "course": course, "said": out[-600:]}

    # --- AN ENTRY FORM (24.0, N37) ----------------------------------------------------------------------------------
    def _git(self, *args):
        return subprocess.run(["git"] + list(args), cwd=vm.ROOT, capture_output=True, text=True, encoding="utf-8",
                              errors="replace")

    def write(self, user, key, w, bean, entry, values):
        """Add one entry to a term of `bean` through drawing `key`'s form `w`, for `user`: asked of the law's grants as
        `write` for the being the host names for the viewer, written through bin/safe.py and saved through
        bin/save.py with that being as <who> — the gate judges it as any commit, and a refused save is undone here,
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
        # EACH VALUE IS ONE VALUE. A value may be a node of its own — a quantity, a position written long —
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
            import safe as dmsafe
            try:
                dmsafe.edit(path, lambda text: _add_entry(text, f["term"], line))
            except Exception as e:
                self.audit(dict(base, mode="refused", why="unsafe edit: %s" % e))
                return 400, {"error": "refused: the entry does not read as the term's (%s) — nothing written" % e}
            what = "%s %s on %s, entered on the page" % (f["term"], entry or "entry", bean)
            r = subprocess.run([sys.executable, os.path.join(vm.ROOT, "bin", "save.py"), actor, what, "--body",
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
        import stale as dmstale
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
            lines = _tail_lines(self.cfg["audit_log"], 400)   # from its end: the log is never rotated (3.11)
        except OSError:
            return []
        rows = [json.loads(l) for l in lines if l.strip()]
        # a viewer reads their own rows; only the one who keeps the garden reads everyone's (security audit 3.1): the
        # `orgs` ceiling narrows what a viewer sees and never decides who may read what others did
        if (self.cfg["users"].get(user) or {}).get("bean") != self.gardener:
            rows = [r for r in rows if r.get("user") == user]
        return rows[-n:]

    # --- sessions ---
    # SIGNING IN IS LIMITED, AND NO STRANGER LOCKS ANYONE OUT (security audit 2026-10-10, 3.5). A stranger — a browser that
    # has not signed in as the name it tries — is refused for a quarter of an hour, the password not even asked, once
    # five tries for one name from one address fail, twenty from one address for any names, or thirty for one name from
    # anywhere (a ceiling no spread of addresses passes). A viewer's own browser, known by the `view_known` cookie a
    # sign-in leaves (signed over their password, so a new password forgets every browser), is held by its own failures
    # alone: five, as for one address. So where every viewer comes through one address — a proxy the configuration does
    # not trust, a tunnel — strangers can hold that address, and never a viewer who has signed in before. Nothing
    # sleeps, so a flood ties up no thread; a failure older than the window is forgotten, and the count of what failed
    # is bounded. A token signed out is kept, by its signature, in `revoked.json` beside the host's configuration until
    # it would have expired — the key outlives a restart, so the revocation does too.
    FAIL_WINDOW, FAIL_LIMIT, SOURCE_LIMIT, NAME_CEILING = 900, 5, 20, 30

    def _recent(self, k, now):
        ts = [t for t in self.fails.get(k, ()) if now - t < self.FAIL_WINDOW]
        if ts:
            self.fails[k] = ts
        else:
            self.fails.pop(k, None)
        return len(ts)

    def held(self, source, user, known=False):
        """Whether a sign-in as `user` from `source` is refused now, the password not asked: by its own failures for a
        browser known as `user`'s, else by the address and the name's, and the name's ceiling."""
        now = time.time()
        with self.flock:
            if known:
                return self._recent("known|" + user, now) >= self.FAIL_LIMIT
            return (self._recent("pair|%s|%s" % (source, user), now) >= self.FAIL_LIMIT
                    or self._recent("source|" + source, now) >= self.SOURCE_LIMIT
                    or self._recent("name|" + user, now) >= self.NAME_CEILING)

    def failed(self, source, user, known=False):
        now = time.time()
        with self.flock:
            if len(self.fails) > 10000:              # a flood of addresses: forget the oldest, never grow without end
                for k in sorted(self.fails, key=lambda k: max(self.fails[k]))[:len(self.fails) - 10000]:
                    del self.fails[k]
            for k in (["known|" + user] if known else ["pair|%s|%s" % (source, user), "source|" + source, "name|" + user]):
                self.fails.setdefault(k, []).append(now)

    def signed_in(self, source, user):
        with self.flock:
            self.fails.pop("pair|%s|%s" % (source, user), None)
            self.fails.pop("known|" + user, None)

    def password_ok(self, user, pw):
        """Whether `pw` is `user`'s password. A name nobody holds is checked against a hash of the same rounds, so the
        answer takes as long as for a name somebody holds (3.5)."""
        rec = (self.cfg.get("users") or {}).get(user)
        stored = rec.get("password") if isinstance(rec, dict) and rec.get("password") else dummy_hash()
        return check_password(pw, stored) and isinstance(rec, dict) and stored is rec.get("password")

    def _pw(self, user):
        """What a viewer's tokens are signed over beside the key: their stored password hash (3.11), so a new password
        voids every token signed before it."""
        rec = (self.cfg.get("users") or {}).get(user)
        return str(rec.get("password") or "") if isinstance(rec, dict) else ""

    def _signed(self, kind, user, exp):
        return hmac.new(self.key, ("%s%s|%s|%s" % (kind, user, exp, self._pw(user))).encode(), hashlib.sha256).hexdigest()

    def known_token(self, user):
        exp = int(time.time()) + KNOWN_DAYS * 86400
        return base64.urlsafe_b64encode(("%s|%d|%s" % (user, exp, self._signed("known|", user, exp))).encode()).decode()

    def known_of(self, tok):
        """The viewer a browser has signed in as, by its `view_known` cookie, while it lasts and their password holds."""
        try:
            user, exp, sig = base64.urlsafe_b64decode((tok or "").encode()).decode().split("|")
            if user in (self.cfg.get("users") or {}) and int(exp) > time.time() and \
                    hmac.compare_digest(sig, self._signed("known|", user, exp)):
                return user
        except Exception:
            pass
        return None

    def _revoked_path(self):
        return os.path.join(os.path.dirname(os.path.abspath(self.config_path)), "revoked.json")

    def _load_revoked(self):
        try:
            with open(self._revoked_path()) as fh:
                got = json.load(fh)
        except (OSError, ValueError):
            return {}
        now = time.time()
        return {str(k): int(v) for k, v in (got.items() if isinstance(got, dict) else []) if int(v) > now}

    def revoke(self, tok):
        """Sign a token out: kept by its signature until it would have expired, and written whole beside the config, 0600
        as the configuration is (3.11)."""
        try:
            _user, exp, sig = base64.urlsafe_b64decode(tok.encode()).decode().split("|")
        except Exception:
            return
        now = time.time()
        self.revoked = {k: v for k, v in self.revoked.items() if v > now}
        self.revoked[sig] = int(exp)
        import safe as dmsafe
        dmsafe.write_atomic(self._revoked_path(), json.dumps(self.revoked), mode=0o600)

    def token(self, user):
        exp = int(time.time()) + SESSION_HOURS * 3600
        sig = self._signed("", user, exp)
        while sig in self.revoked:      # a token signed out this very second is never minted again: its signing in would be
            exp += 1                    # refused as the token signed out, and the person kept out until the next second
            sig = self._signed("", user, exp)
        return base64.urlsafe_b64encode(("%s|%d|%s" % (user, exp, sig)).encode()).decode()

    def user_of(self, tok):
        try:
            user, exp, sig = base64.urlsafe_b64decode(tok.encode()).decode().split("|")
            if user in self.cfg["users"] and int(exp) > time.time() and hmac.compare_digest(sig, self._signed("", user, exp)) \
                    and sig not in self.revoked:
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
    # THE NAMES IT ANSWERS TO (3.11): its own address, the loopback's, and the `hosts` its configuration lists — the name
    # a proxy in front of it passes on as the Host. A page served under another name (DNS rebinding) is refused.
    own = listen_of(F.cfg)[0].lower()
    names = {"127.0.0.1", "localhost", "::1"} | ({own} if own not in ("0.0.0.0", "::") else set()) | \
        {str(h).strip().lower() for h in F.cfg.get("hosts") or [] if str(h).strip()}

    class H(BaseHTTPRequestHandler):
        timeout = float(F.cfg.get("request_seconds", 15))   # a connection that sends nothing is closed (audit 3.3)
        server_version = "view"
        sys_version = ""

        def log_message(self, fmt, *a):
            sys.stderr.write("%s %s\n" % (time.strftime("%H:%M:%S"), fmt % a))

        def _send(self, code, body, ctype="text/html; charset=utf-8", headers=None, csp=CSP):
            b = body.encode() if isinstance(body, str) else body
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(b)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "same-origin")
            self.send_header("Content-Security-Policy", csp)
            for k, v in (headers.items() if isinstance(headers, dict) else headers or ()):
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(b)

        def _json(self, code, obj):
            # a value JSON cannot carry fails here, loudly, rather than reach a page as JSON no browser parses (3.7)
            self._send(code, json.dumps(obj, ensure_ascii=False, allow_nan=False), "application/json")

        def _host_ok(self):
            h = (self.headers.get("Host") or "").strip().lower()
            name = h[1:h.index("]")] if h.startswith("[") and "]" in h else h.rsplit(":", 1)[0] if h.count(":") == 1 else h
            return bool(name) and name in names

        def _from_here(self):
            """Whether a form comes from the page itself: the browser does not call it cross-site, and its `Origin`, where it
            names one, is one of the page's own names. A client that names none (a command line) is taken (3.11)."""
            if (self.headers.get("Sec-Fetch-Site") or "").strip().lower() == "cross-site":
                return False
            o = self.headers.get("Origin")
            return o is None or (urllib.parse.urlsplit(o.strip()).hostname or "").lower() in names

        def _cookie(self, name):
            for part in (self.headers.get("Cookie") or "").split(";"):
                k, _, v = part.strip().partition("=")
                if k == name:
                    return v
            return None

        def _secure(self):
            """`; Secure` where the viewer reached the host over HTTPS — said by the host's configuration, or by the proxy
            in front of it — so the cookie never travels in the clear; over plain HTTP a browser would refuse it."""
            https = F.cfg.get("secure_cookie") is True or (self.headers.get("X-Forwarded-Proto") or "").lower() == "https"
            return "; Secure" if https else ""

        def _session(self):
            v = self._cookie(COOKIE)
            return (v, F.user_of(v)) if v is not None else (None, None)

        def do_GET(self):
            u = urllib.parse.urlparse(self.path)
            if not self._host_ok():
                return self._send(421, "this page answers to its own names only", "text/plain; charset=utf-8")
            if u.path == "/healthz":   # answered from what is held; a stranger's request starts no work (audit 3.4)
                # which release it runs is a signed-in viewer's to be told, not a stranger's (3.11)
                return self._send(200, "ok", "text/plain", headers={"X-View-Release": F.release_at_start} if self._session()[1] else None)
            if u.path == "/login":
                return self._send(200, LOGIN % {"title": title, "err": ""})
            if u.path == "/logout":                # signing out is the page's own POST, with its CSRF token (3.11)
                return self._send(405, "signing out is the page's own button", "text/plain; charset=utf-8",
                                  headers={"Allow": "POST"})
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
                live = {"user": user, "csrf": F.csrf(tok), "history": F.cfg.get("history", ""), "poll": 30,
                        "actions": F.may(user, act=True)[0], "head": (F.head or "")[:10]}
                return self._send(200, vm.surface("python").render(p, live=live), csp=PAGE_CSP)   # this host's surface
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
            if u.path == "/api/prefs":     # the viewer's own way of reading, and what the panel offers (view_prefs)
                import view_prefs
                rec = F.cfg["users"].get(user) or {}
                return self._json(200, {"prefs": {k: rec[k] for k in ("locale", "date", "currency") if rec.get(k)},
                                        "zones": view_prefs.zones()})
            if u.path == "/api/audit":     # asked of the law like the page itself (security audit 2026-10-10, 3.1)
                if not F.may(user)[0]:
                    return self._json(403, {"error": "no grant opens this page to you"})
                return self._json(200, {"entries": F.audit_tail(user)})
            return self._send(404, "not found", "text/plain")

        def do_POST(self):
            u = urllib.parse.urlparse(self.path)
            if not self._host_ok():
                return self._send(421, "this page answers to its own names only", "text/plain; charset=utf-8")
            try:
                n = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                n = -1
            if n < 0:                                  # read(-1) would wait for a body that never ends
                return self._send(400, "a Content-Length is a count of bytes", "text/plain")
            if n > 65536:
                return self._send(413, "too large", "text/plain")
            raw = self.rfile.read(n).decode("utf-8", "replace")
            if u.path == "/login":
                f = urllib.parse.parse_qs(raw)
                user, pw = f.get("user", [""])[0], f.get("password", [""])[0]
                # a sign-in from another site signs nobody in: its form would sign this browser in as a name of that
                # site's choosing (login CSRF, security audit 2026-10-10, 3.11); it is refused before any name is tried
                if not self._from_here():
                    return self._send(403, LOGIN % {"title": title, "err": '<div class="e">a sign-in from another site is '
                                                                           'not taken here</div>'})
                src = source_of(self.client_address[0], self.headers.get("X-Forwarded-For"), F.cfg.get("trusted_proxies"))
                known = bool(user) and F.known_of(self._cookie(KNOWN)) == user
                if F.held(src, user, known):
                    return self._send(429, LOGIN % {"title": title, "err": '<div class="e">too many tries — wait a quarter '
                                                                           'of an hour</div>'})
                if F.password_ok(user, pw):
                    F.signed_in(src, user)
                    return self._send(303, "", headers=[
                        ("Location", "/"),
                        ("Set-Cookie", "%s=%s; Path=/; HttpOnly; SameSite=Strict; Max-Age=%d%s"
                         % (COOKIE, F.token(user), SESSION_HOURS * 3600, self._secure())),
                        # this browser, known as the viewer's: asked their password still when strangers have tried it
                        ("Set-Cookie", "%s=%s; Path=/login; HttpOnly; SameSite=Strict; Max-Age=%d%s"
                         % (KNOWN, F.known_token(user), KNOWN_DAYS * 86400, self._secure()))])
                F.failed(src, user, known)
                return self._send(401, LOGIN % {"title": title, "err": '<div class="e">wrong user or password</div>'})
            tok, user = self._session()
            if not user:
                return self._json(401, {"error": "sign in"})
            if not hmac.compare_digest(self.headers.get(CSRF) or "", F.csrf(tok)):
                return self._json(403, {"error": "missing or wrong CSRF token"})
            if u.path == "/logout":                  # the token itself, not only the browser's copy of it
                F.revoke(tok)
                return self._send(200, json.dumps({"out": True}), "application/json", headers={
                    "Set-Cookie": "%s=; Max-Age=0; Path=/; HttpOnly; SameSite=Strict%s" % (COOKIE, self._secure())})
            if u.path == "/api/action":
                try:
                    body = json.loads(raw or "{}")
                except ValueError:
                    return self._json(400, {"error": "bad json"})
                F.refresh()
                ins = body.get("inputs") if isinstance(body.get("inputs"), dict) else {}
                why = str(body["reason"]) if body.get("reason") else None
                if body.get("do") in ("ratify", "decline"):          # a run's plan ratified, or refused
                    return self._json(*F.decide(user, str(body.get("bean", "")), str(body.get("course", "")), body["do"]))
                if body.get("tool"):                                  # a walk started from a page, with its inputs
                    return self._json(*F.start(user, str(body.get("m", "")), str(body.get("el", "")), str(body["tool"]),
                                               str(body.get("bean", "")), inputs=ins, reason=why))
                code, obj = F.act(user, str(body.get("m", "")), str(body.get("el", "")), inputs=ins, reason=why)
                return self._json(code, obj)
            if u.path == "/api/prefs":                # the viewer's own way of reading: kept with their account, never in git
                try:
                    body = json.loads(raw or "{}")
                except ValueError:
                    return self._json(400, {"error": "bad json"})
                import view_prefs
                kept, bad = view_prefs.check(body)
                if bad:
                    return self._json(400, {"error": "; ".join(bad)})
                F.set_prefs(user, kept)
                return self._json(200, {"ok": True, "reader": view_prefs.settings_of(kept)})
            if u.path == "/api/write":
                try:
                    body = json.loads(raw or "{}")
                except ValueError:
                    return self._json(400, {"error": "bad json"})
                F.refresh()
                if isinstance(body, dict) and isinstance(body.get("ops"), list):   # statements: a sheet's Save, a form of a verb
                    import view_engraved
                    return self._json(*view_engraved.serve_write(F, user, body))
                vals = body.get("values") if isinstance(body.get("values"), dict) else {}
                code, obj = F.write(user, str(body.get("m", "")), str(body.get("w", "")), str(body.get("bean", "")),
                                    str(body.get("entry") or ""), vals)
                return self._json(code, obj)
            return self._json(404, {"error": "not found"})
    return H


class Bounded(ThreadingHTTPServer):
    """A threaded server that holds at most 64 connections at once: past that, a new one is closed at once rather than
    given a thread (security audit 2026-10-10, 3.3)."""
    daemon_threads = True
    request_queue_size = 128            # the kernel's queue of connections not yet taken, in the order they came
    slots = threading.BoundedSemaphore(64)

    def process_request(self, request, client_address):
        if not self.slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except Exception:
            self.slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.slots.release()


class Bounded6(Bounded):
    address_family = socket.AF_INET6


def serve(config, argv=None):
    # refused before anything is read of the garden or bound: a configuration others may read, an address beyond the
    # loopback nobody chose (3.11, 3.2)
    private_config(config)
    with open(config, encoding="utf-8") as fh:
        host, port = listen_of(json.load(fh))
    F = Host(config, argv)
    dummy_hash()                                     # made once, before the first stranger's name is asked
    srv = (Bounded6 if ":" in host else Bounded)((host, port), make_handler(F))
    if not loopback(host) and F.cfg.get("secure_cookie") is not True:
        sys.stderr.write("view serve: listening beyond the loopback, as the configuration chooses: unless a proxy that "
                         "speaks TLS stands in front (and passes X-Forwarded-Proto: https), passwords and sessions cross "
                         "the network in clear\n")
    sys.stderr.write("view serve: %s:%s · page %s of %s @ %s · %d viewers · %d tools (%d enabled)\n" % (
        host, port, vm.PAGE, vm.garden_name(), (F.head or "")[:10], len(F.cfg["users"]), len(F.cfg.get("tools") or {}),
        sum(1 for t in (F.cfg.get("tools") or {}).values() if t.get("enabled"))))
    srv.serve_forever()
