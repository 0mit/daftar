#!/usr/bin/env python3
"""VIEWCAP in a garden of the core (v1 part 12: today's suite, ported): what a served page may do, asked of the
garden's `grant` statements, and what the view asset draws, renders and feeds from a page of `draw` statements.

A garden of the core is grown from a release made of this tree (test/grow.py), taking the view, network and knowledge
profiles: an invented boat club — its boats, its outings, a bosun who is granted the page, the club and the boats (to
read, the boats to write, the reminders to enact), a guest who is granted nothing, and a hygrometer in the boathouse read
over HTTP. Every being is written in statements and saved through the core's gate.

  the page   a `draw` of each drawing — a table of a reading, a funnel whose stages are readings, a health chain whose
             values are read over HTTP — and the page's own `draw` naming them; `view check` finds them agreeing
  V-2        the report writes a table as CSV beside it, its columns read by the core's paths (`be.at`, the moment an
             outing is present); served, the CSV is what the viewer may see
  V-4        a document rendered per member of a reading, each `{{ path }}` read from the member's statements
  V-1        the host's ceiling opens everything, and the garden's grants decide: the bosun may read the page and the
             boats, the guest nothing; a grant that is not the gardener's to give opens nothing; an outing nobody granted
             the bosun is not sent to him, and the gardener's table has every line; the funnel's stages are counted; a
             scheduled action runs as the bosun who answers for it, asked of the grants and audited, on its days alone;
             a press by the guest is refused; a grant's `at` opens it over its extent and not the day after
  V-5        the http adapter: a live value at a JSON Pointer, a live series from the object there
  V-6        ics: a VEVENT per outing at its moment in UTC, a VALARM a day before, audited as the flow law's `served`
             pass; for the guest, refused and audited
  the doors  a Content-Length below nothing refused at once; a Secure cookie over HTTPS; a sign-out that holds; five wrong
             passwords lock the sixth try out

Not here, and why (test/ported.yaml): a grant of PART of a bean, over a reading (today's `over` and `positions`), has no
form in the core, so the translator keeps today's grants in `details`, where nothing reads them — a viewer they opened
a page to is refused in a garden of the core (closed by default); an entry form's `writes` of today's `observations`,
which the core keeps in `details` (v1 part 7) and has no form for; and daftar's own results drawn through a garden (the
`code` profile's runs as observations and a series), for the same reason.

Run: python3 test/viewcap.py   (0 = green)
"""
import hashlib
import http.client
import http.cookiejar
import http.server
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'test'))
import grow  # noqa: E402

PY = sys.executable
FAILS, TRACES = [], []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:1200]))
    if not cond:
        FAILS.append(name)


def run(*a, cwd=None):
    r = grow.run(*a, cwd=cwd)
    if "Traceback" in r.out:
        TRACES.append(r.out[-800:])
    return r


def free_port():
    import socket
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


T = tempfile.mkdtemp(prefix="core-viewcap-")
REL = grow.release(os.path.join(T, "release"))
G = os.path.join(T, "garden-club")
BOSUN, GUEST = "p-b05a0001", "p-9e570001"


def put(rel, text):
    p = os.path.join(G, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def get(rel):
    with open(os.path.join(G, *rel.split("/")), encoding="utf-8") as fh:
        return fh.read()


def view(*a):
    r = run(PY, os.path.join(G, "assets", "view", "bin", "view.py"), *a, cwd=G)
    return r.out, r.returncode


def head():
    return run("git", "rev-parse", "HEAD", cwd=G).stdout.strip()


def clean():
    return not run("git", "status", "--porcelain", cwd=G).stdout.strip()


def bean(bid, kind, title, *statements, details=""):
    return (f"---\nbean: {bid}\nkind: {kind}\ntitle: \"{title}\"\nstatements:\n  - say: {{ by: rosa, at: now }}\n"
            + "".join(f"  - {s}\n" for s in statements) + details + f"---\n{title}, as the club records it.\n")


r = grow.garden(REL, G, "rosa", "--profile", "network", "--profile", "knowledge", "--profile", "view")
check(f"the club's garden of the core (core@{grow.VERSION}) germinates taking the view profile", r.returncode == 0, r.out[-800:])
if r.returncode:
    print("\nviewcap: %d failed" % len(FAILS))
    sys.exit(1)
_v = get("VOCAB.md")
put("VOCAB.md", _v.replace("\n---\n", "\nkinds:\n  - { kind: boat, nature: body, line: made, level: device }\n---\n", 1))
put("beans/boat-club.md", bean("boat-club", "org", "The lake boat club", "own: { by: rosa, of: self }"))
put(f"beans/{BOSUN}.md", bean(BOSUN, "person", BOSUN, "own: { by: theone, of: self }"))
put(f"beans/{GUEST}.md", bean(GUEST, "person", GUEST, "own: { by: theone, of: self }"))
for _b, _t in (("boat-heron", "The Heron"), ("boat-tern", "The Tern")):
    put(f"beans/{_b}.md", bean(_b, "boat", _t, "own: { by: boat-club, of: self }"))
for _o, _at, _boat in (("outing-0927", "2026-09-27 10:00+03:00", "boat-heron"), ("outing-1004", "2026-10-04 09:30+03:00", "boat-tern")):
    put(f"beans/{_o}.md", bean(_o, "event", f"{_o} on the {_boat[5:]}", "own: { by: theone, of: self }",
                               f'be: {{ id: present, by: self, at: "{_at}", as: presence }}',
                               details=f"details:\n  refs:\n    boat: {{ bean: {_boat}, rel: sails }}\n"
                                       f"  booked_by: \"a member, whose number is 555-0100\"\n"))
put("beans/clubhouse-pi.md", bean("clubhouse-pi", "host", "The clubhouse computer", "own: { by: boat-club, of: self }",
                                  "be: { by: self, at: 192.0.2.10, as: location, placed: { openness: here } }"))
put("beans/hygro-firmware.md", bean("hygro-firmware", "product", "The hygrometer's firmware",
                                    'own: { by: { someone: org }, of: self, note: "its makers" }'))
put("beans/boathouse-hygrometer.md", bean("boathouse-hygrometer", "instance", "The boathouse hygrometer",
                                          "own: { by: boat-club, of: self }", "be: { by: self, at: clubhouse-pi, as: habitat }",
                                          "run: { by: self, of: hygro-firmware }", "use: { by: self, of: 'technology:http' }"))
put("templates/slip.md", "# Sailing slip: {{ title }}\n\nStarts {{ be.at }}, on {{ details.refs.boat.bean }}.\n")
EVERY = "{ of: time, from: '2026-09-21', every: { count: '7', unit: d } }"
put("beans/club-page.md", bean(
    "club-page", "service", "The club's page", "own: { by: boat-club, of: self }",
    "be: { by: self, at: 'uri:http://club.example.org/page/', as: location, placed: { openness: here } }",
    "reckon: { id: booked, reading: { what: every outing booked, steps: [ { id: o, op: select, kind: event } ] } }",
    "reckon: { id: heron-outings, reading: { what: the outings on the heron, steps: [ { id: o, op: select, kind: event, "
    "where: [ { path: details.refs.boat.bean, '=': boat-heron } ] } ] } }",
    "draw: { id: outings, by: self, of: [boat-club], drawing: { purpose: Every booked outing sails on a checked boat., "
    "outcome: No boat leaves the jetty unchecked., stages: [ { label: Book an outing, doer: a member }, { label: Check the "
    "boat, doer: the bosun } ], questions: [ { lens: operate, ask: 'Which outings are coming, and is each boat checked?' } ], "
    "archetype: table, blind: [ { what: the weather on the day, why: no forecast is read } ], selection: booked, columns: "
    "[ { label: outing, path: title }, { label: starts, path: be.at } ], renders: [ { template: 'file:templates/slip.md', "
    "selection: booked } ], feed: [ { selection: booked, notice: { of: time, measure: { count: '1', unit: d } } } ], "
    f"actions: [ {{ element: remind, tool: send-reminders, confirm: 'Remind this week''s sailors?', every: {EVERY}, "
    f"answered_by: {BOSUN} }} ] }} }}",
    "draw: { id: pipeline, by: self, of: [boat-club], drawing: { purpose: Shows how many outings each boat takes., outcome: "
    "The heron is not overbooked., stages: [ { label: Book, doer: a member } ], questions: [ { lens: operate, ask: 'How many "
    "outings are on the heron?' } ], archetype: funnel, blind: [ { what: outings booked by telephone, why: they are written "
    "in later } ], funnels: [ { label: outings, stages: [ { label: booked, selection: booked }, { label: on the heron, "
    "selection: heron-outings } ] } ] } }",
    "draw: { id: boathouse, by: self, of: [clubhouse-pi], drawing: { purpose: Keeps the sails dry in the boathouse., outcome: "
    "The air in the boathouse stays below four fifths damp., stages: [ { label: Read the air, doer: the hygrometer, beings: "
    "[ { being: boathouse-hygrometer } ] } ], questions: [ { lens: operate, ask: 'Is the boathouse dry enough for the "
    "sails?' } ], archetype: health-chain, blind: [ { what: the damp inside a folded sail, why: no probe reaches it } ], "
    "values: { humidity: { element: boathouse, live: live-value, label: boathouse humidity, unit: '%', warn: '70', crit: "
    "'80', query: [ { technology: http, says: /humidity } ] }, rooms: { element: boathouse, live: live-series, label: by "
    "room, unit: '%', query: [ { technology: http, says: /rooms } ] } } } }",
    "draw: { id: page, by: self, of: [outings, pipeline, boathouse], page: { drawings: 'file:bin/drawings.py', opens_on: "
    "boat-club, reference: [ { being: clubhouse-pi, system: ipv4, what: \"serves the boathouse's readings\" } ], fields: "
    "[ { kind: event, fact: summary, shown_from: understand } ], monitors: [ { monitor: boathouse-hygrometer } ] } }"))
put("bin/drawings.py", '''"""The club's own drawings (the garden's code, named by the page's `drawings`)."""
from view_kit import node, store, action_btn, figure


def outings():
    b = [node(20, 20, 200, 48, "The club", "books the outings", bean="boat-club"), action_btn(260, 20, 170, "Remind", "reminds the sailors")]
    return ("The outings", figure(460, 90, "".join(b), "the outings"), "Each <b>outing</b> sails on a checked boat.", "No unchecked boat sails.")


def pipeline():
    b = [node(20, 20, 200, 48, "The club", "books the outings", bean="boat-club")]
    return ("Outings per boat", figure(260, 90, "".join(b), "outings per boat"), "How many outings each boat takes.", "The heron is not overbooked.")


def boathouse():
    b = [store(20, 20, 200, 60, "Boathouse", "the sails and the boats", bean="clubhouse-pi", eid="boathouse")]
    return ("The boathouse", figure(260, 100, "".join(b), "the boathouse"), "The <b>air</b> in the boathouse.", "Dry sails.")


COMPOSERS = {"outings": outings, "pipeline": pipeline, "boathouse": boathouse}
''')
GRANTS = [("bosun-page", "club-page", "read", "the bosun keeps the page"),
          ("bosun-club", "boat-club", "read", "the bosun serves the club"),
          ("bosun-boats", "boat-heron, boat-tern", "read", "the bosun keeps the boats"),
          ("bosun-checks", "boat-heron, boat-tern", "write", "the bosun records each boat's checks"),
          ("bosun-reminds", "club-page", "enact", "the bosun reminds the week's sailors")]
_rosa = get("beans/rosa.md")
put("beans/rosa.md", _rosa.replace("\n---\n", "\n  - say: { by: rosa, of: [%s], at: now }\n" % ", ".join(g for g, *_ in GRANTS)
                                   + "".join(f"  - grant: {{ id: {g}, by: rosa, to: [{BOSUN}], of: [{o}], as: {a}, why: \"{w}\" }}\n"
                                             for g, o, a, w in GRANTS) + "---\n", 1))
r = run(PY, "bin/save.py", "rosa", "the club, its boats, its outings and its page",
        "--body", "- action: [[boat-club]], [[boat-heron]], [[boat-tern]], [[outing-0927]], [[outing-1004]], [[clubhouse-pi]], "
        f"[[hygro-firmware]], [[boathouse-hygrometer]], [[club-page]], [[{BOSUN}]] and [[{GUEST}]] recorded; [[rosa]] grants the "
        "bosun the page, the club and the boats, the boats' checks and the reminders. RULE-CHANGE: VOCAB.md holds the club's "
        "boat.", cwd=G)
check("the club's garden, its page and the gardener's grants are saved through the core's gate, with 0 errors",
      r.returncode == 0 and "— 0 error(s)" in r.out and clean(), r.out[-2500:])
_o, _rc = view("check")
check("view check: the page and its drawings agree — a table, a funnel of readings, a health chain read over HTTP",
      _rc == 0 and "agree" in _o, _o[-1500:])

# ---------------------------------------------------------------- V-2 offline: the report writes each table as CSV
_rep = os.path.join(T, "out", "club.html")
_o, _rc = view("report", "--out", _rep)
_csv = os.path.join(T, "out", "club.outings.csv")
_ct = open(_csv, encoding="utf-8").read() if os.path.isfile(_csv) else ""
check("V-2 report: a table's lines are written as CSV beside the report — its columns read by the core's paths, one line "
      "per member", _rc == 0 and _ct.splitlines()[:1] == ["outing,starts"]
      and "outing-0927 on the heron,2026-09-27 10:00+03:00" in _ct and "outing-1004 on the tern,2026-10-04 09:30+03:00" in _ct
      and "club.outings.csv" in open(_rep, encoding="utf-8").read(), (_o, _ct))

# ---------------------------------------------------------------- V-4: rendered from a template
_slips = os.path.join(T, "out", "slips")
_o, _rc = view("render", "outings", "--out", _slips)
_s1 = os.path.join(_slips, "slip-outing-0927.md")
check("V-4 render: a document per member of the reading, each `{{ path }}` read from the member's statements",
      _rc == 0 and os.path.isfile(_s1) and open(_s1, encoding="utf-8").read()
      == "# Sailing slip: outing-0927 on the heron\n\nStarts 2026-09-27 10:00+03:00, on boat-heron.\n"
      and os.path.isfile(os.path.join(_slips, "slip-outing-1004.md")),
      _o + (open(_s1, encoding="utf-8").read() if os.path.isfile(_s1) else ""))
_h0 = head()
_o, _rc = view("render", "outings", "--out", _slips, "--member", "outing-0927", "--keep", "--who", "rosa")
_docs = [f for f in os.listdir(os.path.join(G, "beans")) if f.startswith("doc-outing")]
_want = hashlib.sha256(open(_s1, "rb").read()).hexdigest()
check("V-4 render --keep: the document is kept as a `document` bean named by its content (a name `sha-256` gives), saved "
      "through the core's gate", _rc == 0 and len(_docs) == 1 and _want in get("beans/" + _docs[0])
      and head() != _h0 and clean(), _o[-2000:])

# ---------------------------------------------------------------- the host
_hyg = {"humidity": 71.5, "rooms": {"sail-loft": 60, "boat-bay": 75}}


class Hygrometer(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        b = json.dumps(_hyg).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b)


_hp = free_port()
_hsrv = ThreadingHTTPServer(("127.0.0.1", _hp), Hygrometer)
threading.Thread(target=_hsrv.serve_forever, daemon=True).start()
CFG = os.path.join(T, "host", "serve.json")
for _u, _b in (("bosun", BOSUN), ("guest", GUEST), ("rosa", "rosa")):
    view("serve-init", "--config", CFG, "--user", _u, "--orgs", "*", "--bean", _b)
H = json.load(open(CFG))
_sp = free_port()
H["listen"] = "127.0.0.1:%d" % _sp
H["recheck_seconds"] = 1
H["monitors"] = {"boathouse-hygrometer": {"url": "http://127.0.0.1:%d/" % _hp}}
H["tools"] = {"send-reminders": {"argv": [PY, "-c", "import json,sys; d=json.load(sys.stdin); print('reminded, as', d['actor'], 'at', d['moment'])"],
                                 "enabled": True, "timeout": 20}}
json.dump(H, open(CFG, "w"))
_log = H.get("audit_log") or os.path.join(T, "host", "actions.log")

# The host runs the garden's own copy of the language: this tree's modules, which test/grow.py put on the path, are
# taken off it, so each import below finds the garden's file (a module of this tree reads this tree's root, no garden).
for _n, _m in list(sys.modules.items()):
    if os.path.abspath(getattr(_m, '__file__', '') or '').startswith((os.path.join(ROOT, 'bin'), os.path.join(ROOT, 'core'))):
        del sys.modules[_n]
sys.path[:] = [p for p in sys.path if os.path.abspath(p) not in (ROOT, os.path.join(ROOT, 'bin'))]
for _p in (G, os.path.join(G, "bin"), os.path.join(G, "assets", "view", "lib")):
    sys.path.insert(0, _p)
import view_model as _vm  # noqa: E402
_vm.init(G)
import view_serve as _vs  # noqa: E402
_H = _vs.Host(CFG)
check("V-1 the host's ceiling opens everything (`*`) to each viewer, and the garden's grants decide: the bosun may read the "
      "page and the boats; the guest, granted nothing, may read neither",
      _H.may("bosun")[0] and _H.may("bosun", "boat-heron")[0] and not _H.may("guest")[0] and not _H.may("guest", "boat-heron")[0],
      (_H.may("bosun"), _H.may("bosun", "boat-heron"), _H.may("guest")))
check("V-1 ...an outing nobody granted the bosun is closed to him: closed by default",
      not _H.may("bosun", "outing-0927")[0], _H.may("bosun", "outing-0927"))
_P = _H.scoped_payload("bosun")
check("V-1 the page the bosun is sent carries the boats and not the outings, nor the member's number",
      "boat-heron" in _P["beans"] and "outing-0927" not in _P["beans"] and "555-0100" not in json.dumps(_P),
      sorted(_P["beans"]))
_tab = _P["views"]["outings"]["operate"]["table"]
_P2 = _H.scoped_payload("rosa")
_tab2 = _P2["views"]["outings"]["operate"]["table"]
check("V-2 the bosun's table has no line of an outing not granted him; the gardener's has every line",
      _tab["columns"] == ["outing", "starts"] and not _tab["rows"]
      and [r["bean"] for r in _tab2["rows"]] == ["outing-0927", "outing-1004"], (_tab, _tab2))
_st = _P2["views"]["pipeline"]["operate"]["funnels"][0]["stages"]
check("V-2 the gardener's funnel: its stages are readings, counted — two outings booked, one on the heron — and the members "
      "are never sent", [s.get("static") for s in _st] == [2, 1] and all("members" not in s for s in _st), _st)
_vals = _H.values("rosa", "boathouse")
check("V-5 the http adapter: a live value at a JSON Pointer, a live series from the object there",
      json.dumps(_vals, sort_keys=True).count("71.5") == 1 and "sail-loft" in json.dumps(_vals), _vals)

# V-1 scheduled: every Monday from 2026-09-21, as the bosun
_o, _rc = view("run-scheduled", "--config", CFG, "--at", "2026-09-28")
check("V-1 run-scheduled on a Monday of its recurrence: the reminder runs as the bosun, asked of the grants like a press",
      _rc == 0 and "outings.remind: 200 run" in _o, _o)
_last = [json.loads(ln) for ln in open(_log, encoding="utf-8").read().splitlines()][-1] if os.path.isfile(_log) else {}
check("...and the audit records the actor, the grant that opened it and the moment the tool was handed",
      _last.get("actor") == BOSUN and _last.get("mode") == "run" and (_last.get("answer") or {}).get("granted") is True
      and "bosun-reminds" in json.dumps(_last.get("answer")) and "2026-09-28" in _last.get("output_tail", ""), _last)
_o, _rc = view("run-scheduled", "--config", CFG, "--at", "2026-09-29")
check("...and on a day that is not one of its occurrences, nothing runs", _rc == 0 and "0 action(s) due" in _o, _o)
_code, _obj = _H.act("guest", "outings", "remind")
check("V-1 a press by a viewer the law grants nothing is refused — the page is not theirs to see", _code in (403, 404),
      (_code, _obj))

# V-1 a grant's extent: open over its `at`, and not the day after
import dmpass  # noqa: E402 — the garden's
_today = time.strftime("%Y-%m-%d")
_after = time.strftime("%Y-%m-%d", time.localtime(time.time() + 2 * 86400))
_beans = dmpass.beans_here(G)
_beans["rosa"] = dict(_beans["rosa"], statements=list(_beans["rosa"]["statements"])
                      + [{"grant": {"id": "guest-today", "by": "rosa", "to": [GUEST], "of": ["boat-club"], "as": "read",
                                    "at": f"2026-01-01/{_today}"}}])
_in = dmpass.may(GUEST, "read", "boat-club", at=_today, root=G, beans=_beans, gardener="rosa")
_out = dmpass.may(GUEST, "read", "boat-club", at=_after, root=G, beans=_beans, gardener="rosa")
check("V-1 a grant whose `at` ends today opens its bean today, and the day after it does not",
      _in.granted and not _out.granted, (_in, _out))
_beans = dmpass.beans_here(G)
_beans[GUEST] = dict(_beans[GUEST], statements=list(_beans[GUEST]["statements"])
                     + [{"grant": {"id": "self-grant", "by": GUEST, "to": [GUEST], "of": ["boat-club"], "as": "read"}}])
_self = dmpass.may(GUEST, "read", "boat-club", root=G, beans=_beans, gardener="rosa")
check("V-1 ...and a grant in a bean whose holder may not decide for the club opens nothing", not _self.granted, _self)

# V-6 the calendar
_ics = os.path.join(T, "out", "club.ics")
_o, _rc = view("ics", "outings", "--out", _ics, "--config", CFG, "--user", "rosa")
_it = open(_ics, encoding="utf-8").read() if os.path.isfile(_ics) else ""
check("V-6 ics: a VEVENT per outing, at its moment in UTC, with a VALARM a day before",
      _rc == 0 and _it.count("BEGIN:VEVENT") == 2 and "DTSTART:20260927T070000Z" in _it and "TRIGGER:-P1D" in _it
      and "555-0100" not in _it, _o + _it[:600])
_last = [json.loads(ln) for ln in open(_log, encoding="utf-8").read().splitlines()][-1]
check("V-6 ...audited as a pass of the flow law's row `served` — out of the estate to a remote viewer — granted",
      _last.get("mode") == "ics" and _last.get("flow") == "served" and _last.get("granted") is True
      and _last.get("actor") == "rosa", _last)
os.remove(_ics)
_o, _rc = view("ics", "outings", "--out", _ics, "--config", CFG, "--user", "guest")
_last = [json.loads(ln) for ln in open(_log, encoding="utf-8").read().splitlines()][-1]
check("V-6 ...and for the guest, granted no read of the outings, refused, nothing written, the refusal audited",
      _rc == 2 and "grants guest no read" in _o and not os.path.exists(_ics) and _last.get("granted") is False, _o)

# ---------------------------------------------------------------- served, through the host's HTTP
srv = subprocess.Popen([PY, os.path.join(G, "assets", "view", "bin", "view.py"), "serve", "--config", CFG], cwd=G,
                       stderr=subprocess.PIPE, text=True, encoding="utf-8")
BASE = "http://127.0.0.1:%d" % _sp
for _ in range(80):
    try:
        urllib.request.urlopen(BASE + "/healthz", timeout=1)
        break
    except Exception:  # noqa: BLE001 — not up yet
        time.sleep(0.2)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def session(user):
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()), NoRedirect)
    pw = open(os.path.join(T, "host", user + ".password")).read().strip()
    try:
        op.open(BASE + "/login", urllib.parse.urlencode({"user": user, "password": pw}).encode())
    except urllib.error.HTTPError:
        pass
    return op


def get_(op, path):
    try:
        r = op.open(BASE + path)
        return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


try:
    st, body = get_(session("guest"), "/")
    check("V-1 served: the guest, granted nothing, is refused the page, and told why", st == 403 and "no grant" in body,
          (st, body[:300]))
    bosun = session("bosun")
    st, pg = get_(bosun, "/")
    check("V-1 served: the bosun's page is sent him", st == 200 and 'id="viewdata"' in pg, (st, pg[:300]))
    st, csvb = get_(bosun, "/api/csv?m=outings")
    check("V-2 served: the table's CSV, as the bosun may see it — no line of an outing not granted him",
          st == 200 and csvb.splitlines() == ["outing,starts"], (st, csvb))
    st, csvr = get_(session("rosa"), "/api/csv?m=outings")
    check("V-2 ...and as the gardener may: every line", st == 200 and len(csvr.splitlines()) == 3, (st, csvr))
    # ---- the doors: a body's length, a cookie over HTTPS, a sign-out that holds, and a lockout
    _hc = http.client.HTTPConnection("127.0.0.1", _sp, timeout=180)
    _hc.putrequest("POST", "/api/write")
    _hc.putheader("Content-Length", "-1")
    _hc.endheaders()
    try:
        _st = _hc.getresponse().status
    except Exception as e:  # noqa: BLE001 — what happened is the answer
        _st = repr(e)
    check("a request whose Content-Length is less than nothing is refused at once, never waited on", _st == 400, _st)
    _pw = open(os.path.join(T, "host", "bosun.password")).read().strip()
    _hc = http.client.HTTPConnection("127.0.0.1", _sp, timeout=180)
    _hc.request("POST", "/login", urllib.parse.urlencode({"user": "bosun", "password": _pw}),
                {"Content-Type": "application/x-www-form-urlencoded", "X-Forwarded-Proto": "https"})
    _r = _hc.getresponse()
    _ck = _r.getheader("Set-Cookie") or ""
    _r.read()
    check("reached over HTTPS (the proxy says so), the session's cookie is Secure", "; Secure" in _ck, _ck)
    _tok = _ck.split(";", 1)[0]

    def _with(cookie, path):
        c = http.client.HTTPConnection("127.0.0.1", _sp, timeout=180)
        c.request("GET", path, headers={"Cookie": cookie})
        r = c.getresponse()
        r.read()
        return r.status
    _before = _with(_tok, "/")
    _with(_tok, "/logout")
    _after = _with(_tok, "/")
    check("a token signed out opens nothing again, though the browser that held it kept a copy",
          _before == 200 and _after == 303, (_before, _after))
    _codes = []
    for _i in range(6):
        c = http.client.HTTPConnection("127.0.0.1", _sp, timeout=180)
        c.request("POST", "/login", urllib.parse.urlencode({"user": "bosun", "password": "wrong" if _i < 5 else _pw}),
                  {"Content-Type": "application/x-www-form-urlencoded"})
        r = c.getresponse()
        r.read()
        _codes.append(r.status)
    check("five wrong passwords lock the address and the user out: the sixth try, right or wrong, is refused (429)",
          _codes == [401] * 5 + [429], _codes)
finally:
    srv.terminate()
    try:
        srv.wait(timeout=10)
    except Exception:  # noqa: BLE001
        srv.kill()
    _err = srv.stderr.read()
    if "Traceback" in _err:
        TRACES.append(_err[-1500:])
    _hsrv.shutdown()

check("NOTHING above ended in a traceback: every case is a refusal or a pass", not TRACES, "\n----\n".join(TRACES)[-2500:])
shutil.rmtree(T, ignore_errors=True)
print("\nviewcap: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
