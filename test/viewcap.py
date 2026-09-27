#!/usr/bin/env python3
"""VIEWCAP (24.0, N33, N36–N40): what a served page may do, asked of the ledger's grants — and daftar's own suite results
drawn through the same mechanisms.

Two gardens are grown from this tree as a release, with the `view` profile.

  the club   an invented boat club: its boats, its outings, a bosun who is granted the boats and only the title and the
             timing of each outing, a guest who is granted nothing, and a hygrometer in the boathouse read over HTTP.
             V-1: the page, each value and each action are asked of the grants (`bin/dmpass.py`) for the being the host
                  names for the viewer; the host's configuration only narrows; a part of a bean is sent where only part
                  is granted. A scheduled action runs as the being who answers for it, asked like a press.
             V-2: a table of a reading, its lines scoped per viewer, as CSV beside the report and from the host; a
                  funnel whose stages are readings.
             V-3: an entry form writes an observation through bin/dmsave.py as the viewer; the gate refuses a unit the
                  law has not got, the page shows its message, and nothing is kept.
             V-4: each outing rendered from a template of the garden into a document, kept as a `document` bean by its
                  content_hash.
             V-5: the http adapter reads a JSON document at pointers: a live value and a live series.
             V-6: a calendar of the outings, each with a notice a day before, audited as a pass — and refused where the
                  viewer is granted no read of what it carries.
             The gate's own ply refuses a schedule nobody answers for, a table of two things, a form of an attribute
             the law does not give, and a table's attribute on another shape.
  results    daftar's own: a suite's result an observation of the codebase at a commit (a scheme the garden holds as
             an extract, pinned to the commit), the run a `race` read from the runner's status document, and runs across
             commits a series drawn as a table — behind the same guard.
"""
import http.cookiejar, http.server, json, os, re, shutil, subprocess, sys, tempfile, threading, time, urllib.error, urllib.parse, urllib.request
from http.server import ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS, TRACES = [], []
PY = sys.executable


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:1200]))
    if not cond:
        FAILS.append(name)


def run(*a, cwd=None, env=None, stdin=None):
    r = subprocess.run(list(a), capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd, input=stdin,
                       env=dict(os.environ, **(env or {})))
    if "Traceback" in r.stdout + r.stderr:
        TRACES.append((r.stdout + r.stderr)[-800:])
    return r


def free_port():
    import socket
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


T = tempfile.mkdtemp(prefix="dmviewcap-")

# A RELEASE, made of this tree as seed/LANGUAGE ships it, tagged — as test/view.py makes one.
sys.path.insert(0, os.path.join(ROOT, "bin"))
import dmparse, dmpass
REL = os.path.join(T, "release")
_law0 = dmparse.loads(dmparse.split_front_matter(open(os.path.join(ROOT, "seed", "std-vocab.md"), encoding="utf-8").read())[0])
for _f in dmpass.kept([f for f in dmpass.tracked(ROOT) if os.path.isfile(os.path.join(ROOT, f))],
                      dmpass.language(open(os.path.join(ROOT, "seed", "LANGUAGE"), encoding="utf-8").read()),
                      dmpass.offered(_law0)):
    os.makedirs(os.path.join(REL, os.path.dirname(_f)), exist_ok=True)
    shutil.copy2(os.path.join(ROOT, _f), os.path.join(REL, _f))
_env = {"GIT_AUTHOR_NAME": "r", "GIT_AUTHOR_EMAIL": "r@example.org", "GIT_COMMITTER_NAME": "r", "GIT_COMMITTER_EMAIL": "r@example.org"}
for _c in (["git", "init", "-q"], ["git", "add", "-A"], ["git", "commit", "-qm", "a release"], ["git", "tag", "v9.9.9"]):
    run(*_c, cwd=REL, env=_env)


class Garden:
    def __init__(self, name, gardener, *profiles):
        self.g = os.path.join(T, name)
        r = run(PY, os.path.join(REL, "seed", "germinate.py"), self.g, "--gardener", gardener,
                *[x for p in profiles for x in ("--profile", p)], cwd=T)
        self.ok = r.returncode == 0
        self.out = r.stdout + r.stderr
        run("git", "config", "user.name", gardener, cwd=self.g)
        run("git", "config", "user.email", gardener + "@example.org", cwd=self.g)
        self.dmview_path = os.path.join(self.g, "assets", "view", "bin", "dmview.py")

    def put(self, rel, text):
        p = os.path.join(self.g, *rel.split("/"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)

    def get(self, rel):
        with open(os.path.join(self.g, *rel.split("/")), encoding="utf-8") as fh:
            return fh.read()

    def vocab(self, extra):
        v = self.get("VOCAB.md")
        for k in [k for k in ("local_gene", "registry_additions", "registry_files") if re.search(rf"(?m)^{k}:", extra)]:
            v = re.sub(rf"(?m)^{k}: (\[\]|\{{\}}).*\n", "", v)
        h, sep, rest = v.partition("\n---\n")
        self.put("VOCAB.md", h + "\n" + extra + sep + rest)

    def save(self, who, what, body):
        r = run(PY, os.path.join(self.g, "bin", "dmsave.py"), who, what, "--body", body, cwd=self.g)
        return r.returncode, r.stdout + r.stderr

    def gate(self):
        r = run(PY, os.path.join(self.g, "bin", "dmcheck.py"), "--all", cwd=self.g)
        return r.stdout + r.stderr, r.returncode

    def dmview(self, *a):
        r = run(PY, self.dmview_path, *a, cwd=self.g)
        return r.stdout + r.stderr, r.returncode

    def head(self):
        return run("git", "rev-parse", "HEAD", cwd=self.g).stdout.strip()

    def clean(self):
        return not run("git", "status", "--porcelain", cwd=self.g).stdout.strip()


def person(pid, what):
    return f"""---
bean: {pid}
genos: person
title: "{pid}"
status: active
summary: "{what}"
nature: empsychon
owned_by: {{ legal: {{ crown: agape }} }}
responsibility: {{ legal: {{ self: true }} }}
identity: {{ status: confirmed, anchors: [ {{ key: person_id, value: "person:{pid}", class: logical, establishing: true }} ] }}
provenance: {{ src: asserted-by-human, by: "rosa (gardener)", as_of: now }}
---
{what}.
"""


def bean(bid, genos, nature, title, summary, anchor, extra="", own="owned_by: { legal: { owner: { bean: boat-club } } }\n"):
    k, v, c = anchor
    return (f"---\nbean: {bid}\ngenos: {genos}\ntitle: \"{title}\"\nstatus: active\nsummary: \"{summary}\"\nnature: {nature}\n"
            f"identity:\n  status: confirmed\n  anchors:\n    - {{ key: {k}, value: \"{v}\", class: {c}, establishing: true }}\n"
            f"provenance: {{ src: asserted-by-human, by: \"rosa (gardener)\", as_of: now }}\n{own}"
            f"responsibility: {{ legal: {{ holder: {{ bean: rosa }} }} }}\n{extra}---\n{title}, as the club records it.\n")


# ==================================================================================================== the club
C = Garden("garden-club", "rosa", "network", "knowledge", "view")
check("the club's garden germinates with the view profile", C.ok, C.out[-800:])
if not C.ok:
    print("\nviewcap: %d failed" % len(FAILS))
    sys.exit(1)
BOSUN, GUEST = "p-b05a0001", "p-9e570001"
C.vocab("""local_gene:
  - { genos: boat, of_nature: soma, meaning: "a boat the club keeps, invented" }
registry_additions:
  knowledge_schemes:
    - scheme: boat-checks
      classifies: what the club checks of a boat before it sails, invented
      holding: extract
      licence: CC0-1.0
      release: "the club's own, 2026"
      publisher: the club (invented)
      url: "extracts/boat-checks.tsv"
      levels: [ { level: check } ]
      neighbours: none
      sources: extracts/boat-checks.tsv
registry_files:
  - { registry: boat-checks, file: extracts/boat-checks.tsv, key: code }
""")
C.put("extracts/boat-checks.tsv", "code\tparent\tname\nhull\t\tthe hull, for cracks\nmast\t\tthe mast, for a bend\n")
C.put("beans/boat-club.md", bean("boat-club", "org", "lekton", "The lake boat club", "An invented club that keeps boats on a lake.",
                                 ("org_id", "org:boat-club", "logical"), own="owned_by: { legal: { owner: { bean: rosa } } }\n"))
C.put(f"beans/{BOSUN}.md", person(BOSUN, "the club's bosun, a volunteer"))
C.put(f"beans/{GUEST}.md", person(GUEST, "a guest of the club"))
for _b, _s in (("boat-heron", "SN-HERON-1"), ("boat-tern", "SN-TERN-2")):
    C.put(f"beans/{_b}.md", bean(_b, "boat", "soma", _b.replace("boat-", "The ").title(), "A dinghy the club keeps.",
                                 ("serial", _s, "hardware"),
                                 extra="" if _b == "boat-heron" else "observations:\n  mast-sprung: { property: { scheme: boat-checks, code: mast }, "
                                       "at: \"2026-09-20\", value: { count: \"4\", unit: millimetre } }\n"))
for _o, _at, _boat in (("outing-0927", "2026-09-27 10:00+03:00", "boat-heron"), ("outing-1004", "2026-10-04 09:30+03:00", "boat-tern")):
    C.put(f"beans/{_o}.md", bean(_o, "event", "lekton", "%s on the %s" % (_o, _boat[5:]),
                                 "Booked by a member, whose number is 555-0100.", ("event_id", "event:" + _o, "logical"),
                                 extra=f"timing:\n  start: {{ system: gregorian-civil, at: \"{_at}\", unit: minute }}\n"
                                       f"refs:\n  boat: {{ bean: {_boat}, rel: sails }}\n",
                                 own="owned_by: { legal: { crown: logos } }\n"))
C.put("beans/clubhouse-pi.md", bean("clubhouse-pi", "host", "soma", "The clubhouse computer", "A small computer in the clubhouse.",
                                    ("serial", "SN-PI-77", "hardware"), extra="provides_habitat: linux-baremetal\nlocated_at:\n  - { system: ipv4, openness: here, at: 192.0.2.10, observed: now }\n"))
C.put("beans/hygro-firmware.md", bean("hygro-firmware", "product", "lekton", "The hygrometer's firmware",
                                      "The software a hygrometer runs, recorded so its copy has a type.", ("product_id", "product:hygro-firmware", "logical"),
                                      own="owned_by: { legal: { external: \"its makers\" } }\n"))
C.put("beans/boathouse-hygrometer.md", bean("boathouse-hygrometer", "instance", "empsychon", "The boathouse hygrometer",
                                            "Reads the air in the boathouse and serves it as one JSON document.",
                                            ("instance_id", "instance:boathouse-hygrometer", "logical"),
                                            extra="instance_of: { bean: hygro-firmware }\nlives_in: { bean: clubhouse-pi }\n"
                                                  "knowledge:\n  - { scheme: technology, code: http, rel: uses }\n"))
C.put("templates/slip.md", "# Sailing slip: {{ title }}\n\nStarts {{ timing.start.at }}, on {{ refs.boat.bean }}.\n")
EVERY = '{ of: time, from: "2026-09-21", every: { count: 7, unit: day } }'
PAGE = f"""---
bean: club-page
genos: service
title: "The club's page"
status: active
summary: "The club's outings, its boats and its boathouse, drawn."
nature: lekton
identity:
  status: confirmed
  anchors:
    - {{ key: service_id, value: "service:club-page", class: logical, establishing: true }}
provenance: {{ src: asserted-by-human, by: "rosa (gardener)", as_of: now }}
owned_by: {{ legal: {{ owner: {{ bean: boat-club }} }} }}
responsibility: {{ legal: {{ holder: {{ bean: rosa }} }} }}
selections:
  outings: {{ what: "every outing booked", steps: [ {{ id: o, op: select, genos: event }} ] }}
  heron-outings: {{ what: "the outings on the heron", steps: [ {{ id: o, op: select, genos: event, where: [ {{ path: refs.boat.bean, is: boat-heron }} ] }} ] }}
view:
  drawings: file:bin/drawings.py
  opens_on: boat-club
  reference:
    - {{ being: clubhouse-pi, system: ipv4, what: "serves the boathouse's readings" }}
  fields:
    - {{ genos: event, term: summary, shown_from: understand }}
    - {{ genos: event, term: timing, shown_from: understand }}
view_monitors:
  - {{ monitor: boathouse-hygrometer }}
views:
  outings:
    draws: {{ bean: boat-club }}
    purpose: "Every booked outing sails on a checked boat."
    outcome: "No boat leaves the jetty unchecked."
    stages:
      - {{ label: "Book an outing", doer: "a member" }}
      - {{ label: "Check the boat", doer: "the bosun" }}
    questions: [ {{ lens: operate, ask: "Which outings are coming, and is each boat checked?" }} ]
    archetype: table
    blind: [ {{ what: "the weather on the day", why: "no forecast is read" }} ]
    selection: outings
    columns:
      - {{ label: outing, path: title }}
      - {{ label: starts, path: timing.start.at }}
    writes:
      - {{ term: observations, attrs: [ {{ attr: property }}, {{ attr: at }}, {{ attr: value }} ] }}
    renders:
      - {{ template: "file:templates/slip.md", selection: outings }}
    feed:
      - {{ selection: outings, notice: {{ of: time, measure: {{ count: 1, unit: day }} }} }}
    actions:
      - {{ element: remind, tool: send-reminders, confirm: "Remind this week's sailors?", every: {EVERY}, answered_by: {BOSUN} }}
  pipeline:
    draws: {{ bean: boat-club }}
    purpose: "Shows how many outings each boat takes."
    outcome: "The heron is not overbooked."
    stages: [ {{ label: "Book", doer: "a member" }} ]
    questions: [ {{ lens: operate, ask: "How many outings are on the heron?" }} ]
    archetype: funnel
    blind: [ {{ what: "outings booked by telephone", why: "they are written in later" }} ]
    funnels:
      - {{ label: outings, stages: [ {{ label: booked, selection: outings }}, {{ label: "on the heron", selection: heron-outings }} ] }}
  boathouse:
    draws: {{ bean: clubhouse-pi }}
    purpose: "Keeps the sails dry in the boathouse."
    outcome: "The air in the boathouse stays below four fifths damp."
    stages: [ {{ label: "Read the air", doer: "the hygrometer", beings: [ {{ being: boathouse-hygrometer }} ] }} ]
    questions: [ {{ lens: operate, ask: "Is the boathouse dry enough for the sails?" }} ]
    archetype: health-chain
    blind: [ {{ what: "the damp inside a folded sail", why: "no probe reaches it" }} ]
view_bindings:
  humidity: {{ view: boathouse, element: boathouse, live: live-value, label: "boathouse humidity", unit: percent, warn: 70, crit: 80, query: [ {{ technology: http, says: "/humidity" }} ] }}
  rooms: {{ view: boathouse, element: boathouse, live: live-series, label: "by room", unit: percent, query: [ {{ technology: http, says: "/rooms" }} ] }}
---
The club's page of drawings.
"""
C.put("beans/club-page.md", PAGE)
C.put("bin/drawings.py", '''"""The club's own drawings (the garden's code, named by the page's `view.drawings`)."""
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
_rosa = C.get("beans/rosa.md")
C.put("beans/rosa.md", _rosa.replace("\n---\n", f"""
selections:
  pages: {{ what: "the club's page", steps: [ {{ id: p, op: select, genos: service }} ] }}
  boats: {{ what: "the club's boats", steps: [ {{ id: b, op: select, genos: boat }} ] }}
  club: {{ what: "the club itself", steps: [ {{ id: c, op: select, genos: org }} ] }}
  outings: {{ what: "every outing booked", steps: [ {{ id: o, op: select, genos: event }} ] }}
grants:
  bosun-page: {{ act: read, over: pages, audience: {{ who: {BOSUN} }}, why: "the bosun keeps the page" }}
  bosun-club: {{ act: read, over: club, audience: {{ who: {BOSUN} }}, why: "the bosun serves the club" }}
  bosun-boats: {{ act: read, over: boats, audience: {{ who: {BOSUN} }}, why: "the bosun keeps the boats" }}
  bosun-outings: {{ act: read, over: outings, positions: [ {{ path: title }}, {{ path: timing }} ], audience: {{ who: {BOSUN} }}, why: "the bosun sees when each boat sails, not who booked it" }}
  bosun-checks: {{ act: write, over: boats, audience: {{ who: {BOSUN} }}, why: "the bosun records each boat's checks" }}
  bosun-reminds: {{ act: "act:send-reminders", over: pages, audience: {{ who: {BOSUN} }}, why: "the bosun reminds the week's sailors" }}
---
""", 1))
rc, out = C.save("rosa", "the club, its boats, its outings and its page", "- action: [[boat-club]], [[boat-heron]], [[boat-tern]], "
                 "[[outing-0927]], [[outing-1004]], [[clubhouse-pi]], [[hygro-firmware]], [[boathouse-hygrometer]], "
                 f"[[club-page]], [[{BOSUN}]] and [[{GUEST}]] recorded; [[rosa]] grants the bosun the boats, the page, part of each "
                 "outing, the boats' checks and the reminders. RULE-CHANGE: VOCAB.md holds the club's boat and its boat-checks scheme.")
check("the club's garden, its page and the gardener's grants are saved through the gate, with 0 errors and 0 warnings",
      rc == 0 and " 0 error(s), 0 warning(s)" in out, out[-2500:])
_o, _rc = C.dmview("check")
check("dmview check: the page and its drawings agree — a table, a funnel of readings, a health chain read over HTTP", _rc == 0, _o[-1500:])

# ---------------------------------------------------------------- the ply: what the gate refuses of a page's asks
_bad = PAGE.replace(f", answered_by: {BOSUN} }}", " }", 1) \
           .replace("    selection: outings\n    columns:", "    selection: outings\n    series: { bean: club-page, field: none }\n    columns:", 1) \
           .replace("{ attr: value } ]", "{ attr: value }, { attr: colour } ]", 1) \
           .replace("    funnels:\n", "    selection: outings\n    funnels:\n", 1)
C.put("beans/club-page.md", _bad)
_o, _rc = C.gate()
check("VIEWCAP: a schedule that names nobody who answers for it is refused, naming `answered_by`",
      _rc != 0 and "runs on a schedule (`every`) and names nobody who answers for it" in _o, _o[-1500:])
check("VIEWCAP: a table of a reading AND a series is refused — a table lists one thing", "both given" in _o, _o[-1500:])
check("VIEWCAP: a form of an attribute the law does not give the term is refused, naming what it has",
      "`observations` has no attribute 'colour'" in _o, _o[-1500:])
check("VIEWCAP: a table's `selection` on a funnel is refused", "`selection` belongs to a table, and this drawing's shape is funnel" in _o, _o[-1500:])
C.put("beans/club-page.md", _bad.replace(" }\n  pipeline:", f", answered_by: {BOSUN}, every: {EVERY} }}\n  pipeline:", 1)
      if False else PAGE.replace("every: " + EVERY + ", ", "", 1))
_o, _rc = C.gate()
check("VIEWCAP: `answered_by` on an action nobody schedules is refused — a press is answered for by whoever presses",
      _rc != 0 and "names `answered_by` without `every`" in _o, _o[-1500:])
run("git", "checkout", "--", "beans/club-page.md", cwd=C.g)
_o, _rc = C.gate()
check("...and the page as saved passes again", _rc == 0, _o[-800:])

# ---------------------------------------------------------------- V-2 offline: the report writes each table as CSV
_rep = os.path.join(T, "out", "club.html")
_o, _rc = C.dmview("report", "--out", _rep)
_csv = os.path.join(T, "out", "club.outings.csv")
_ct = open(_csv, encoding="utf-8").read() if os.path.isfile(_csv) else ""
check("V-2 report: a table's lines are written as CSV beside the report — its columns, one line per member",
      _rc == 0 and _ct.splitlines()[:1] == ["outing,starts"] and "outing-0927 on the heron,2026-09-27 10:00+03:00" in _ct
      and "outing-1004 on the tern" in _ct and "club.outings.csv" in open(_rep, encoding="utf-8").read(), (_o, _ct))

# ---------------------------------------------------------------- V-4: rendered from a template, kept by content
_slips = os.path.join(T, "out", "slips")
_o, _rc = C.dmview("render", "outings", "--out", _slips)
_s1 = os.path.join(_slips, "slip-outing-0927.md")
check("V-4 render: a document per member of the reading, each `{{ path }}` read from the member's record",
      _rc == 0 and os.path.isfile(_s1) and open(_s1).read() == "# Sailing slip: outing-0927 on the heron\n\nStarts 2026-09-27 10:00+03:00, on boat-heron.\n"
      and os.path.isfile(os.path.join(_slips, "slip-outing-1004.md")), _o)
_h0 = C.head()
_o, _rc = C.dmview("render", "outings", "--out", _slips, "--member", "outing-0927", "--keep", "--who", "rosa")
_docs = [f for f in os.listdir(os.path.join(C.g, "beans")) if f.startswith("doc-outing")]
import hashlib
_want = "sha256:" + hashlib.sha256(open(_s1, "rb").read()).hexdigest()
check("V-4 render --keep: the document is kept as a `document` bean named by its content_hash, saved through the gate",
      _rc == 0 and len(_docs) == 1 and _want in C.get("beans/" + _docs[0]) and "rendered-from" in C.get("beans/" + _docs[0])
      and C.head() != _h0 and C.clean(), _o[-2000:])

# ---------------------------------------------------------------- the host
_hyg = {"humidity": 71.5, "rooms": {"sail-loft": 60, "boat-bay": 75}}


class Hygrometer(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        b = json.dumps(_hyg).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(b)


_hp = free_port()
_hsrv = ThreadingHTTPServer(("127.0.0.1", _hp), Hygrometer)
threading.Thread(target=_hsrv.serve_forever, daemon=True).start()
CFG = os.path.join(T, "host", "serve.json")
for _u, _b in (("bosun", BOSUN), ("guest", GUEST), ("rosa", "rosa")):
    C.dmview("serve-init", "--config", CFG, "--user", _u, "--orgs", "*", "--bean", _b)
H = json.load(open(CFG))
_sp = free_port()
H["listen"] = "127.0.0.1:%d" % _sp
H["recheck_seconds"] = 1
H["monitors"] = {"boathouse-hygrometer": {"url": "http://127.0.0.1:%d/" % _hp}}
H["tools"] = {"send-reminders": {"argv": [PY, "-c", "import json,sys; d=json.load(sys.stdin); print('reminded, as', d['actor'], 'at', d['moment'])"],
                                 "enabled": True, "timeout": 20}}
json.dump(H, open(CFG, "w"))

sys.path.insert(0, os.path.join(C.g, "assets", "view", "lib"))
import view_model as _vm
_vm.init(C.g)
import view_serve as _vs
_H = _vs.Host(CFG)
check("V-1 the host's ceiling opens everything (`*`) to each viewer, and the LEDGER decides: the bosun may read the page and the "
      "boats; the guest, granted nothing, may read neither",
      _H.may("bosun")[0] and _H.may("bosun", "boat-heron")[0] and not _H.may("guest")[0] and not _H.may("guest", "boat-heron")[0],
      (_H.may("bosun"), _H.may("guest")))
check("V-1 ...an outing is granted the bosun only in part: its title and its timing, never the whole",
      not _H.may("bosun", "outing-0927")[0] and _H.may("bosun", "outing-0927", positions=["title"])[0]
      and _H.may("bosun", "outing-0927", positions=["timing"])[0] and not _H.may("bosun", "outing-0927", positions=["summary"])[0],
      _H.may("bosun", "outing-0927"))
_P = _H.scoped_payload("bosun")
_ob = _P["beans"].get("outing-0927") or {}
check("V-1 the page the bosun is sent carries an outing's timing and title, marked a part, and not the summary with the "
      "member's number", _ob.get("part") is True and "timing" in _ob.get("fields", {}) and "summary" not in _ob.get("fields", {})
      and "555-0100" not in json.dumps(_P), _ob)
_tab = _P["views"]["outings"]["operate"]["table"]
check("V-2 the bosun's table: a line per outing, since every part its columns read (the title, the timing) is granted him",
      _tab["columns"] == ["outing", "starts"] and [r["bean"] for r in _tab["rows"]] == ["outing-0927", "outing-1004"], _tab)
check("V-2 ...and a line whose columns read a part not granted (the summary, with the member's number) is not sent",
      _H.line_ok("bosun", "outing-0927", {"reads": ["title", "timing"]}) and not _H.line_ok("bosun", "outing-0927", {"reads": ["title", "summary"]})
      and not _H.line_ok("guest", "outing-0927", {"reads": ["title"]}))
_P2 = _H.scoped_payload("rosa")
_st = _P2["views"]["pipeline"]["operate"]["funnels"][0]["stages"]
check("V-2 the gardener's funnel: its stages are readings, counted — two outings booked, one on the heron — and the members "
      "are never sent", [s.get("static") for s in _st] == [2, 1] and all("members" not in s for s in _st), _st)
_vals = _H.values("rosa", "boathouse")
check("V-5 the http adapter: a live value at a JSON Pointer, a live series from the object there",
      json.dumps(_vals, sort_keys=True).count("71.5") == 1 and "sail-loft" in json.dumps(_vals), _vals)

# V-1 scheduled: every Monday from 2026-09-21, as the bosun
_log = H.get("audit_log") or os.path.join(T, "host", "actions.log")
_o, _rc = C.dmview("run-scheduled", "--config", CFG, "--at", "2026-09-28")
check("V-1 run-scheduled on a Monday of its recurrence: the reminder runs as the bosun, asked of the grants like a press",
      _rc == 0 and "outings.remind: 200 run" in _o, _o)
_last = [json.loads(l) for l in open(_log, encoding="utf-8").read().splitlines()][-1]
check("...and the audit records the actor, the grant that opened it and the moment the tool was handed",
      _last.get("actor") == BOSUN and _last.get("mode") == "run" and _last["answer"]["granted"] is True
      and any("bosun-reminds" in json.dumps(g) for g in _last["answer"]["grants"]) and "2026-09-28" in _last.get("output_tail", ""), _last)
_o, _rc = C.dmview("run-scheduled", "--config", CFG, "--at", "2026-09-29")
check("...and on a day that is not one of its occurrences, nothing runs", _rc == 0 and "0 action(s) due" in _o, _o)
_code, _obj = _H.act("guest", "outings", "remind")
check("V-1 a press by a viewer the law grants nothing is refused — the page is not theirs to see", _code in (403, 404), (_code, _obj))

# V-6 the calendar
_ics = os.path.join(T, "out", "club.ics")
_o, _rc = C.dmview("ics", "outings", "--out", _ics, "--config", CFG, "--user", "bosun")
_it = open(_ics, encoding="utf-8").read() if os.path.isfile(_ics) else ""
check("V-6 ics: a VEVENT per outing, at its timing in UTC, with a VALARM a day before",
      _rc == 0 and _it.count("BEGIN:VEVENT") == 2 and "DTSTART:20260927T070000Z" in _it and "TRIGGER:-P1D" in _it
      and "555-0100" not in _it, _o + _it[:600])
_last = [json.loads(l) for l in open(_log, encoding="utf-8").read().splitlines()][-1]
check("V-6 ...audited as a pass of the flow law's row `served` — out of the estate to a remote viewer, served — granted",
      _last.get("mode") == "ics" and _last.get("flow") == "served"
      and _last.get("pass") == {"from": {"layer": "estate"}, "to": {"layer": "remote"}, "method": "serve"}
      and _last.get("granted") is True and _last.get("actor") == BOSUN, _last)
os.remove(_ics)
_o, _rc = C.dmview("ics", "outings", "--out", _ics, "--config", CFG, "--user", "guest")
_last = [json.loads(l) for l in open(_log, encoding="utf-8").read().splitlines()][-1]
check("V-6 ...and for the guest, granted no read of the outings, refused, nothing written, the refusal audited",
      _rc == 2 and "grants guest no read" in _o and not os.path.exists(_ics) and _last.get("granted") is False, _o)

# V-3 served: the entry form, through the host's HTTP
srv = subprocess.Popen([PY, C.dmview_path, "serve", "--config", CFG], cwd=C.g, stderr=subprocess.PIPE, text=True, encoding="utf-8")
BASE = "http://127.0.0.1:%d" % _sp
for _ in range(80):
    try:
        urllib.request.urlopen(BASE + "/healthz", timeout=1); break
    except Exception:
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
        r = op.open(BASE + path); return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def post_(op, path, obj, csrf):
    req = urllib.request.Request(BASE + path, json.dumps(obj).encode(), {"Content-Type": "application/json", "X-View-CSRF": csrf})
    try:
        r = op.open(req); return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")
    except (ConnectionError, OSError) as e:
        return 0, {"error": repr(e)}


try:
    guest = session("guest")
    st, body = get_(guest, "/")
    check("V-1 served: the guest, granted nothing, is refused the page, and told why", st == 403 and "no grant" in body, (st, body[:300]))
    bosun = session("bosun")
    st, pg = get_(bosun, "/")
    m = re.search(r'<script type="application/json" id="viewdata">(.*?)</script>', pg, re.S)
    PB = json.loads(m.group(1).replace("<\\/", "</")) if m else {}
    csrf = PB.get("live", {}).get("csrf", "")
    check("V-3 served: the bosun's page carries the drawing's entry form, the law's own attributes of `observations`",
          st == 200 and [a["attr"] for a in PB["views"]["outings"]["writes"][0]["attrs"]] == ["property", "at", "value"], (st, PB.get("views", {}).get("outings", {}).get("writes")))
    st, csvb = get_(bosun, "/api/csv?m=outings")
    check("V-2 served: the table's CSV, as the bosun may see it — the parts granted, never the member's number",
          st == 200 and len(csvb.splitlines()) == 3 and "555-0100" not in csvb, (st, csvb))
    st, csvr = get_(session("rosa"), "/api/csv?m=outings")
    check("V-2 ...and as the gardener may: every line", st == 200 and len(csvr.splitlines()) == 3, (st, csvr))
    _h0 = C.head()
    st, j = post_(bosun, "/api/write", {"m": "outings", "w": 0, "bean": "boat-heron", "entry": "hull-crack",
                                        "values": {"property": "{ scheme: boat-checks, code: hull }", "at": "2026-09-26",
                                                   "value": "{ count: \"3\", unit: furlong }"}}, csrf)
    check("V-3 a value the law refuses (a unit it has not got): the GATE refuses the save, the page is shown its message, and "
          "nothing is kept — the bean, the journal and HEAD as they were",
          st == 422 and "furlong" in j.get("output", "") and C.head() == _h0 and C.clean() and "hull-crack" not in C.get("beans/boat-heron.md"),
          (st, j.get("error"), j.get("output", "")[-800:]))
    st, j = post_(bosun, "/api/write", {"m": "outings", "w": 0, "bean": "boat-heron", "entry": "hull-crack",
                                        "values": {"property": "{ scheme: boat-checks, code: hull }", "at": "2026-09-26",
                                                   "value": "{ count: \"3\", unit: millimetre }"}}, csrf)
    _lg = run("git", "log", "-1", "--format=%s", cwd=C.g).stdout.strip()
    _jn = C.get("log/journal.md").split("\n## ")[-1]
    check("V-3 a value the law takes: saved through bin/dmsave.py, the entry on the boat, the journal naming the bosun as who",
          st == 200 and C.head() != _h0 and "hull-crack: { property: { scheme: boat-checks, code: hull }" in C.get("beans/boat-heron.md")
          and _lg == "observations hull-crack on boat-heron, entered on the page" and BOSUN in _jn.splitlines()[0] and C.clean(),
          (st, j, _lg, _jn[:300]))
    st, j = post_(bosun, "/api/write", {"m": "outings", "w": 0, "bean": "outing-0927", "entry": "late",
                                        "values": {"property": "{ scheme: boat-checks, code: hull }", "at": "2026-09-26"}}, csrf)
    check("V-3 a write to an outing, which the bosun is granted only to read in part, is refused by the law before anything is written",
          st == 403 and "outing-0927" not in run("git", "status", "--porcelain", cwd=C.g).stdout, (st, j))
    st, j = post_(bosun, "/api/write", {"m": "outings", "w": 0, "bean": "boat-heron", "entry": "x",
                                        "values": {"colour": "red"}}, csrf)
    check("V-3 an attribute the form does not ask for is refused", st == 400 and "asks for no colour" in j.get("error", ""), (st, j))
    st, j = post_(bosun, "/api/write", {"m": "outings", "w": 0, "bean": "boat-heron", "entry": "spill",
                                        "values": {"property": "{ scheme: boat-checks, code: hull }", "at": "2026-09-26, by: rosa",
                                                   "value": "{ count: \"1\", unit: millimetre }"}}, csrf)
    check("V-3 a value that would spill into an attribute the form does not offer (`2026-09-26, by: rosa`) is refused, "
          "naming it, and nothing is written", st == 400 and "one value, of its own attribute (at)" in j.get("error", "")
          and "spill" not in C.get("beans/boat-heron.md") and C.clean(), (st, j))
    _aud = [json.loads(l) for l in open(_log, encoding="utf-8").read().splitlines()]
    check("V-3 every write, saved or refused, is audited with the answer that decided it",
          [a["mode"] for a in _aud if a.get("act") == "write"] == ["refused", "saved", "refused", "refused", "refused"], [a.get("mode") for a in _aud])
finally:
    srv.terminate()
    try:
        srv.wait(timeout=10)
    except Exception:
        srv.kill()
    _err = srv.stderr.read()
    if "Traceback" in _err:
        TRACES.append(_err[-1500:])
    _hsrv.shutdown()

# ==================================================================================================== daftar's own results
R = Garden("garden-results", "keeper", "code", "knowledge", "view")
check("the results garden germinates with the code and view profiles", R.ok, R.out[-800:])
SUITES = sorted(f[:-3] for f in os.listdir(os.path.join(ROOT, "test")) if f.endswith(".py"))
R.vocab("""registry_additions:
  knowledge_schemes:
    - scheme: daftar-suites
      classifies: daftar's own test suites, one code each, and what a run of one found
      holding: extract
      licence: GPL-3.0-or-later
      release: "the suites of the release this garden runs"
      publisher: daftar
      url: "extracts/daftar-suites.tsv"
      levels: [ { level: suite }, { level: verdict } ]
      neighbours: none
      sources: extracts/daftar-suites.tsv
registry_files:
  - { registry: daftar-suites, file: extracts/daftar-suites.tsv, key: code }
""")
R.put("extracts/daftar-suites.tsv", "code\tparent\tname\n" + "".join("%s\t\tthe suite test/%s.py\n" % (s, s) for s in SUITES)
      + "passed\t\tevery check of the run passed\nfailed\t\ta check of the run failed\n")
RUN = [("save", 38.2, "passed"), ("view", 61.0, "passed"), ("viewcap", 44.5, "passed")]
HOLDS = "".join("      - { name: %s, quantity: duration, unit: second, stands_for: point }\n" % s for s, _d, _v in RUN)
R.put("beans/daftar.md", """---
bean: daftar
genos: codebase
title: "daftar"
status: active
summary: "The ledger's own code, whose suites are run at each part and kept here as what was found of it."
nature: lekton
identity: { status: confirmed, anchors: [ { key: git_remote, value: "example.org:git/daftar.git", class: logical, establishing: true } ] }
provenance: { src: asserted-by-human, by: keeper, as_of: now }
owned_by: { legal: { owner: { bean: keeper } } }
responsibility: { legal: { holder: { bean: keeper } } }
code_paths:
  - { path: "root:daftar", role: own-source, scan_policy: index }
analysis_cache:
  code-structure: { produced_by: "tool:suite.py", as_of: 2026-09-26, staleness_key: "daftar@f0e1d2c", policy: index, form: inline, covers_paths: ["root:daftar"] }
series:
  suite-seconds:
    span: { of: time, from: "2026-09-26 08:00+03:00" }
    unit: second
    holds:
""" + HOLDS + """    rows: |
      at\t""" + "\t".join(s for s, _d, _v in RUN) + """
      0\t40.1\t58.3\t41.0
      7200\t""" + "\t".join(str(d) for _s, d, _v in RUN) + """
---
daftar, as its own suites find it.
""")
R.put("beans/runner.md", "---\nbean: runner\ngenos: host\ntitle: \"The machine the suites run on\"\nstatus: active\n"
      "summary: \"Runs the suites and serves the run's status document.\"\nnature: soma\n"
      "identity:\n  status: confirmed\n  anchors:\n    - { key: serial, value: \"SN-RUNNER-1\", class: hardware, establishing: true }\n"
      "provides_habitat: linux-baremetal\n"
      "provenance: { src: observed, by: keeper, as_of: now }\nowned_by: { legal: { owner: { bean: keeper } } }\n"
      "responsibility: { legal: { holder: { bean: keeper } } }\n"
      "located_at:\n  - { system: ipv4, openness: here, at: 192.0.2.90, observed: now }\n---\nThe runner.\n")
R.put("beans/suite-py.md", "---\nbean: suite-py\ngenos: product\ntitle: \"The suite runner\"\nstatus: active\n"
      "summary: \"The script that runs every suite and writes its status as one JSON document.\"\nnature: lekton\n"
      "identity:\n  status: confirmed\n  anchors:\n    - { key: product_id, value: \"product:suite-py\", class: logical, establishing: true }\n"
      "provenance: { src: asserted-by-human, by: keeper, as_of: now }\nowned_by: { legal: { owner: { bean: keeper } } }\n"
      "responsibility: { legal: { holder: { bean: keeper } } }\n---\nThe runner's script.\n")
R.put("beans/suite-status.md", "---\nbean: suite-status\ngenos: instance\ntitle: \"The run's status\"\nstatus: active\n"
      "summary: \"The status document of the run in progress, served where the runner writes it.\"\nnature: empsychon\n"
      "identity:\n  status: confirmed\n  anchors:\n    - { key: instance_id, value: \"instance:suite-status\", class: logical, establishing: true }\n"
      "provenance: { src: observed, by: keeper, as_of: now }\nowned_by: { legal: { owner: { bean: keeper } } }\n"
      "responsibility: { legal: { holder: { bean: keeper } } }\ninstance_of: { bean: suite-py }\nlives_in: { bean: runner }\n"
      "knowledge:\n  - { scheme: technology, code: http, rel: uses }\n---\nThe status.\n")
R.put("mappings/suite-run.md", "---\nmapping: suite-run\nkind: procedure\n"
      "summary: \"A run of the suites, one after another, each a step.\"\n"
      "provenance: { src: asserted-by-human, by: keeper, as_of: now }\nsteps:\n"
      + "".join("  - \"the %s suite runs\"\n" % s for s, _d, _v in RUN) + "---\nA run of the suites.\n")
R.put("beans/results-page.md", """---
bean: results-page
genos: service
title: "daftar's suites, drawn"
status: active
summary: "The run in progress and the runs across commits."
nature: lekton
identity:
  status: confirmed
  anchors:
    - { key: service_id, value: "service:results-page", class: logical, establishing: true }
provenance: { src: asserted-by-human, by: keeper, as_of: now }
owned_by: { legal: { owner: { bean: keeper } } }
responsibility: { legal: { holder: { bean: keeper } } }
view:
  drawings: file:bin/drawings.py
  reference:
    - { being: runner, system: ipv4, what: "runs the suites" }
view_monitors:
  - { monitor: suite-status }
views:
  run:
    draws: { mapping: suite-run }
    purpose: "Every suite passes before a part is committed."
    outcome: "A green run, closed and pinned to its commit."
    stages: [ { label: "Run each suite", doer: "the runner", beings: [ { being: runner } ] } ]
    questions: [ { lens: operate, ask: "How far is the run, and will it finish in the hour?" } ]
    archetype: race
    blind: [ { what: "a suite's own checks while it runs", why: "the runner writes its status between suites" } ]
    step_at: suites-done
    elapsed: suites-elapsed
    eta: suites-left
    deadline: { of: time, measure: { count: 1, unit: hour } }
  graph:
    draws: { bean: daftar }
    purpose: "Shows how long each suite takes, commit after commit."
    outcome: "A suite that slows is seen the run it slows."
    stages: [ { label: "Keep each closing run", doer: "the keeper" } ]
    questions: [ { lens: operate, ask: "Which suite grew slower?" } ]
    archetype: table
    blind: [ { what: "runs that were not closing runs", why: "they are held off git" } ]
    series: { bean: daftar, field: suite-seconds }
    columns:
      - { label: at, path: at }
""" + "".join("      - { label: %s, path: %s }\n" % (s, s) for s, _d, _v in RUN) + """view_bindings:
  suites-done: { view: run, element: runner, live: live-value, label: "suites done", query: [ { technology: http, says: "/done" } ] }
  suites-elapsed: { view: run, element: runner, live: live-value, label: "running for", unit: second, query: [ { technology: http, says: "/elapsed" } ] }
  suites-left: { view: run, element: runner, live: live-value, label: "still needs", unit: second, query: [ { technology: http, says: "/left" } ] }
---
daftar's own suites, drawn.
""")
R.put("bin/drawings.py", '''"""The results page's drawings."""
from view_kit import node, store, figure


def run():
    b = [node(20, 20, 200, 48, "Runner", "runs the suites", bean="runner", eid="runner")]
    return ("The run", figure(260, 90, "".join(b), "the run"), "The <b>suites</b>, one after another.", "A green run.")


def graph():
    b = [store(20, 20, 200, 60, "daftar", "the code", bean="daftar")]
    return ("The runs", figure(260, 100, "".join(b), "the runs"), "Each <b>suite</b>'s seconds, commit after commit.", "No slow suite unseen.")


COMPOSERS = {"run": run, "graph": graph}
''')
_k = R.get("beans/keeper.md")
R.put("beans/keeper.md", _k.replace("\n---\n", """
selections:
  all: { what: "everything the garden keeps", steps: [ { id: a, op: select } ] }
  watchers: { what: "who watches the runs", steps: [ { id: p, op: select, genos: person } ] }
grants:
  watchers-read: { act: read, over: all, audience: { selection: watchers }, why: "the runs are public" }
---
""", 1))
R.put("beans/p-0b5e0001.md", person("p-0b5e0001", "a watcher of the runs").replace("rosa (gardener)", "keeper"))
# the closing run: each suite's verdict an observation, pinned to the garden's commit the run was read at (a pin names a
# commit of THIS garden: the codebase's own commit the suites ran against is said in the note, as built)
PIN = R.head()[:12]
_d = R.get("beans/daftar.md")
R.put("beans/daftar.md", _d.replace("\n---\n", "\nobservations:\n" + "".join(
    "  run-%s: { property: { scheme: daftar-suites, code: %s }, at: \"2026-09-26 10:00+03:00\", code: { scheme: daftar-suites, code: %s }, "
    "by: runner, pin: { commit: %s, at: now }, note: \"the suite run against daftar f0e1d2c\" }\n" % (s, s, v, PIN) for s, _d2, v in RUN)
    + "---\n", 1))
rc, out = R.save("keeper", "daftar's suites as observations and a series, and their page",
                 "- action: [[daftar]] holds each suite's verdict of the closing run of daftar f0e1d2c as an observation pinned to "
                 + PIN + ", and the runs across commits as the series suite-seconds; [[runner]], [[suite-py]], [[suite-status]], [[suite-run]], "
                 "[[results-page]] and [[p-0b5e0001]] recorded; RULE-CHANGE: VOCAB.md holds extracts/daftar-suites.tsv, the garden's scheme of its suites.")
check("RESULTS: the codebase, each suite's verdict an observation of it, the runs across commits a series on it (a channel per "
      "suite), the scheme of its suites the garden holds as an extract, and the page; all pass the gate",
      rc == 0 and " 0 error(s), 1 warning(s)" in out and "position 'inline' is declared vacant" in out, out[-2500:])
_bl = R.get("beans/daftar.md")
check("RESULTS: ...each verdict pinned to the garden's commit, its `at` written `now` committed as the save's own reading",
      rc == 0 and ("pin: { commit: %s, at: now }" % PIN) not in _bl and re.search(r"pin: \{ commit: %s, at: \"?20\d\d-" % PIN, _bl) is not None,
      out[-1500:] + str(re.findall(r"pin: \{[^}]*\}", _bl)[:1]))
_o, _rc = R.dmview("check")
check("RESULTS: the page — a race of the run and a table of the series — agrees with its drawings", _rc == 0, _o[-1500:])
_status = {"total": 3, "done": 2, "passed": 2, "failed": 0, "elapsed": 99.5, "left": 44.5, "suites": {"save": 38.2, "view": 61.3}}


class Status(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        b = json.dumps(_status).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(b)


_sp2 = free_port()
_ssrv = ThreadingHTTPServer(("127.0.0.1", _sp2), Status)
threading.Thread(target=_ssrv.serve_forever, daemon=True).start()
CFG2 = os.path.join(T, "host2", "serve.json")
for _u, _b in (("watcher", "p-0b5e0001"), ("nobody", "keeper")):
    R.dmview("serve-init", "--config", CFG2, "--user", _u, "--orgs", "*", "--bean", _b)
H2 = json.load(open(CFG2))
H2["monitors"] = {"suite-status": {"url": "http://127.0.0.1:%d/status.json" % _sp2}}
del H2["users"]["nobody"]
json.dump(H2, open(CFG2, "w"))
_out = run(PY, "-c", """
import json, sys
sys.path.insert(0, %r)
import view_model as vm
vm.init(%r)
import view_serve as vs
h = vs.Host(%r)
p = h.scoped_payload("watcher")
print(json.dumps({"may": h.may("watcher")[0], "run": h.values("watcher", "run"), "table": p["views"]["graph"]["operate"]["table"]}))
""" % (os.path.join(R.g, "assets", "view", "lib"), R.g, CFG2), cwd=R.g)
try:
    _res = json.loads(_out.stdout.strip().splitlines()[-1])
except Exception:
    _res = {}
_rv = json.dumps(_res.get("run"))
_out5 = run(PY, "-c", """
import sys, time
sys.path.insert(0, %r)
import view_model as vm
vm.init(%r)
import view_serve as vs
h = vs.Host(%r)
today = time.strftime('%%Y-%%m-%%d', time.gmtime())
h.refresh(force=True, reexec=False)
h.beans['keeper']['grants']['watchers-read']['during'] = {'to': today}
first = h.may('watcher')[0]
_real = time.time
time.time = lambda: _real() + 2 * 86400
later = h.may('watcher')[0]
print(first, later)
""" % (os.path.join(R.g, "assets", "view", "lib"), R.g, CFG2), cwd=R.g)
check("a grant whose `during` ends today opens the page today, and the day after it does not: an answer the host keeps "
      "holds for the day it was asked on, not until the next commit",
      _out5.stdout.strip().splitlines()[-1:] == ["True False"], _out5.stdout[-400:] + _out5.stderr[-900:])
check("RESULTS: behind the view guard, the watcher (granted the garden to read) is sent the race's values, read by the http "
      "adapter from the runner's status document: two suites done, 99.5 s run, 44.5 s left",
      _res.get("may") is True and "2.0" in _rv and "99.5" in _rv and "44.5" in _rv, _out.stdout[-600:] + _out.stderr[-900:])
_tb = _res.get("table") or {}
check("RESULTS: ...and the run graph: the series as a table, a line per commit's run and a column per suite",
      _tb.get("columns") == ["at"] + [s for s, _d, _v in RUN] and len(_tb.get("rows") or []) == 2
      and [str(c) for c in _tb["rows"][1]["cells"][1:]] == [str(d) for _s, d, _v in RUN], _tb)
_ssrv.shutdown()

check("NOTHING above ended in a traceback: every case is a refusal or a pass", not TRACES, "\n----\n".join(TRACES)[-2500:])
shutil.rmtree(T, ignore_errors=True)
print("\nviewcap: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
