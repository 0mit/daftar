#!/usr/bin/env python3
"""The `view` profile and its asset: a page of drawings, checked as law, drawn by `assets/view`, and closed by default.

A garden is grown here and opted into the profile; its page, its beings and its procedure are invented — a grain
co-operative's silo and its drying run — and every one of them passes the gate. Then:

  part 1, the law  the page's records pass with 0 errors and 0 warnings; each write the law refuses is refused by name
                   (a unit the law has not got, a shape without what it answers with, a value no binding gives, a
                   binding on no drawing, an address restated on the page, a stored list of patterns, a length written
                   as a bare number, a stride on a walk with no meter, a repetition written as a length, a technology
                   outside the catalogue, a threshold in seconds, a page opening on a machine, a monitor the garden does
                   not hold, a pointer to a field nobody states, and a garden that does not extend the profile — whose
                   refusal names the profile and the one act that opts in); the one the gate cannot refuse — a view
                   written on a being — passes it, and is the asset's to refuse
"""
import os, re, shutil, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS, TRACES = [], []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:900]))
    if not cond:
        FAILS.append(name)


def run(*a, cwd=None, env=None):
    return subprocess.run(list(a), capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd,
                          env=dict(os.environ, **(env or {})))


def said(out, kind, *words):
    """The findings of one kind (ERROR, WARN) that name every one of the words: a refusal is read by what it names. A
    finding is its first line and the indented lines that go on from it (the gate sets the reason beneath)."""
    found = []
    for l in out.splitlines():
        if l.startswith(kind):
            found.append(l)
        elif found and found[-1] is not None and l[:1].isspace() and l.strip():
            found[-1] += "\n" + l
        else:
            found.append(None)
    return [f for f in found if f is not None and all(w in f for w in words)]


T = tempfile.mkdtemp(prefix="dmview-")
G = os.path.join(T, "garden-grain")

# ------------------------------------------------------------------ the garden, and what it keeps (all invented)
BEANS = {
    "grain-coop": '''bean: grain-coop
genos: org
title: "The grain co-operative"
status: active
summary: "The co-operative that stores and dries its members' grain."
nature: lekton
identity:
  status: confirmed
  anchors:
    - { key: org_id, value: "org:grain-coop", class: logical, establishing: true }
provenance: { src: asserted-by-human, by: "tessa (gardener)", as_of: now }
owned_by: { legal: { owner: { bean: tessa } } }
responsibility: { legal: { holder: { bean: tessa } } }
''',
    "hill-farm": '''bean: hill-farm
genos: org
title: "The hill farm"
status: active
summary: "A member farm that keeps a pump of its own."
nature: lekton
identity:
  status: confirmed
  anchors:
    - { key: org_id, value: "org:hill-farm", class: logical, establishing: true }
provenance: { src: asserted-by-human, by: "tessa (gardener)", as_of: now }
owned_by: { legal: { owner: { bean: tessa } } }
responsibility: { legal: { holder: { bean: tessa } } }
''',
    "silo-controller": '''bean: silo-controller
genos: host
title: "The silo controller"
status: active
summary: "The machine that reads the silo's fill and runs its fans."
nature: soma
identity:
  status: confirmed
  anchors:
    - { key: serial, value: "SN-SILO-0417", class: hardware, establishing: true }
provenance: { src: observed, by: "tessa (gardener)", as_of: now }
owned_by: { legal: { owner: { bean: grain-coop } } }
responsibility: { legal: { holder: { bean: tessa } } }
provides_habitat: linux-baremetal
located_at:
  - { system: ipv4, openness: here, at: 192.0.2.40, observed: now }
endpoints:
  - { protocol: http, system: ipv4, at: 192.0.2.40, port: "80", exposure: lan, observed: now }
details:
  processes:
    - { proc: "fan-driver", user: "silo", role: "switches the fans", config: "fans.conf", rail: air }
    - { proc: "fill-reader", user: "silo", role: "reads the level sensor", config: "sensor.conf", rail: fill }
  pipes:
    - { from: "level sensor", to: "fill-reader", kind: serial, at: "/dev/ttyS1", config: "sensor 9600 baud", rail: fill }
    - { from: "fill-reader", to: "exporter", kind: file, at: "/run/silo/fill", config: "every 30 seconds", rail: fill }
''',
    "dryer-controller": '''bean: dryer-controller
genos: host
title: "The dryer controller"
status: active
summary: "The machine that runs the grain dryer's burner and its batches."
nature: soma
identity:
  status: confirmed
  anchors:
    - { key: serial, value: "SN-DRY-0981", class: hardware, establishing: true }
provenance: { src: observed, by: "tessa (gardener)", as_of: now }
owned_by: { legal: { owner: { bean: grain-coop } } }
responsibility: { legal: { holder: { bean: tessa } } }
located_at:
  - { system: ipv4, openness: here, at: 192.0.2.41, observed: now }
endpoints:
  - { protocol: ssh, system: ipv4, at: 192.0.2.41, port: "22", exposure: lan, observed: now }
''',
    "field-radio": '''bean: field-radio
genos: host
title: "The field radio"
status: active
summary: "Tessa's own radio link from the silo to the barn."
nature: soma
identity:
  status: confirmed
  anchors:
    - { key: serial, value: "SN-RADIO-2210", class: hardware, establishing: true }
provenance: { src: observed, by: "tessa (gardener)", as_of: now }
owned_by: { legal: { owner: { bean: tessa } } }
responsibility: { legal: { holder: { bean: tessa } } }
located_at:
  - { system: ipv4, openness: here, at: 192.0.2.60, observed: now }
''',
    "hill-pump": '''bean: hill-pump
genos: host
title: "The hill farm's pump"
status: active
summary: "The hill farm's own irrigation pump controller."
nature: soma
identity:
  status: confirmed
  anchors:
    - { key: serial, value: "SN-PUMP-3302", class: hardware, establishing: true }
provenance: { src: observed, by: "tessa (gardener)", as_of: now }
owned_by: { legal: { owner: { bean: hill-farm } } }
responsibility: { legal: { holder: { bean: tessa } } }
located_at:
  - { system: ipv4, openness: here, at: 192.0.2.70, observed: now }
''',
    "prometheus": '''bean: prometheus
genos: product
title: "Prometheus"
status: active
summary: "The monitoring system the co-operative runs, recorded so its copy has a type to be an instance of."
nature: lekton
identity:
  status: confirmed
  anchors:
    - { key: technology, value: prometheus, class: logical, establishing: true }
provenance: { src: asserted-by-human, by: "tessa (gardener)", as_of: now }
owned_by: { legal: { external: "the Prometheus authors" } }
responsibility: { legal: { holder: { bean: tessa } } }
''',
    "watcher": '''bean: watcher
genos: instance
title: "The watcher"
status: active
summary: "The co-operative's running monitor: it probes the controllers and keeps their readings."
nature: empsychon
identity:
  status: confirmed
  anchors:
    - { key: instance_id, value: "instance:watcher", class: logical, establishing: true }
provenance: { src: observed, by: "tessa (gardener)", as_of: now }
owned_by: { via: { bean: silo-controller } }
responsibility: { via: { bean: silo-controller } }
instance_of: { bean: prometheus }
lives_in: { bean: silo-controller }
roles: [ { role: monitoring } ]
knowledge:
  - { scheme: technology, code: prometheus, rel: uses }
reaches:
  silo-web: { protocol: http, target: { bean: silo-controller } }
  dryer-shell: { protocol: ssh, target: { bean: dryer-controller } }
  radio-ping: { protocol: icmp, target: { bean: field-radio } }
  pump-ping: { protocol: icmp, target: { bean: hill-pump } }
details:
  alert_rules:
    - { name: SiloNearlyFull, expr: "silo_fill_ratio > 0.9", for: 15m, severity: warning, summary: "the silo is over nine tenths full" }
''',
    "grain-page": '''bean: grain-page
genos: service
title: "The silo and the dryer, drawn"
status: active
summary: "The co-operative's page of drawings: the silo filling, and the night's drying run."
nature: lekton
identity:
  status: confirmed
  anchors:
    - { key: service_id, value: "service:grain-page", class: logical, establishing: true }
provenance: { src: asserted-by-human, by: "tessa (gardener)", as_of: now }
owned_by: { legal: { owner: { bean: grain-coop } } }
responsibility: { legal: { holder: { bean: tessa } } }
view:
  drawings: file:bin/drawings.py
  opens_on: grain-coop
  glossary: { dryer: "the machine that takes the water out of the harvest before it is stored" }
  reference:
    - { being: silo-controller, system: ipv4, what: "reads the fill and runs the fans" }
    - { being: dryer-controller, system: ipv4, what: "runs the dryer's batches" }
    - { being: field-radio, system: ipv4, what: "carries the readings to the barn" }
    - { being: hill-pump, system: ipv4, what: "the hill farm's pump" }
  fields:
    - { genos: host, term: summary, shown_from: understand }
    - { genos: host, term: located_at, shown_from: inspect }
view_monitors:
  - { monitor: watcher, settings: { bean: watcher, field: alert_rules } }
views:
  silo:
    draws: { bean: silo-controller }
    purpose: "Keeps room in the silo for the rest of the harvest."
    outcome: "The silo never fills before the last load is in."
    stages:
      - { label: "Read the fill", doer: "the level sensor, every half minute", beings: [ { being: silo-controller } ], uses: [ { technology: prometheus } ] }
      - { label: "Warn before full", doer: "the watcher" }
      - { label: "Send loads elsewhere", doer: "the yard crew" }
    questions:
      - { lens: orient, ask: "What keeps the silo from overflowing?" }
      - { lens: operate, ask: "Is there room for tomorrow's loads?" }
    processes: { bean: silo-controller, field: processes }
    pipes: { bean: silo-controller, field: pipes }
    actions:
      - { element: start-fans, tool: start-fans, confirm: "Start the silo fans now?" }
      - { element: radio-reset, tool: radio-reset, confirm: "Reset the field radio?", acts_on: field-radio }
      - { element: pump-stop, tool: pump-stop, confirm: "Stop the hill pump?", acts_on: hill-pump }
    archetype: reservoir
    blind: [ { what: "the grain's moisture inside the silo", why: "no probe reaches inside" } ]
    notes: [ { note: "at nine tenths full, send the next loads to the hill farm" } ]
    fill: silo-fill
    thresholds:
      - { fullness: { count: 90, unit: percent }, label: "divert the next loads" }
      - { fullness: { count: 98, unit: percent }, label: "stop filling" }
    forecast: silo-full-in
    parts: [ { bind: silo-up }, { bind: grain-temperature } ]
    correlate:
      - rows: [ { bind: silo-fill }, { bind: grain-temperature } ]
        span: { of: time, measure: { count: 12, unit: hour } }
        every: { of: time, every: { count: 5, unit: minute } }
  drying:
    draws: { mapping: drying-run }
    purpose: "Dries each night's harvest before the morning's loads arrive."
    outcome: "The batch is unloaded before six in the morning."
    stages:
      - { label: "Load the dryer", doer: "the yard crew" }
      - { label: "Heat and cool", doer: "the dryer controller", beings: [ { being: dryer-controller } ] }
      - { label: "Unload to the silo", doer: "the auger" }
    questions: [ { lens: operate, ask: "Will the batch be out before six?" } ]
    archetype: race
    blind: [ { what: "the burner's fuel", why: "the tank has no gauge" } ]
    step_at: drying-step
    elapsed: drying-elapsed
    eta: drying-left
    deadline: { of: time, measure: { count: 7, unit: hour } }
    checkpoints: [ { after: { of: time, measure: { count: 3, unit: hour } }, label: "heating should be done" } ]
    numbers: [ { bind: drying-batches } ]
    correlate:
      - rows: [ { bind: grain-temperature } ]
        band: drying-step
        relate: { across: grain-temperature, measure: drying-left, bins: 4, at_step: 2, keep: positive }
view_bindings:
  silo-fill: { view: silo, element: silo, live: live-value, label: "silo fill", unit: percent, warn: 80, crit: 90, query: [ { technology: prometheus, says: "silo_fill_ratio{$F} * 100" } ] }
  silo-full-in: { view: silo, element: silo, live: live-value, label: "until full", unit: day, query: [ { technology: prometheus, says: "silo_days_to_full{$F}" } ] }
  silo-up: { view: silo, element: silo-controller, live: live-state }
  radio-up: { view: silo, element: field-radio, live: live-state }
  pump-up: { view: silo, element: hill-pump, live: live-state }
  grain-temperature: { view: silo, element: silo, live: live-value, label: "grain temperature (°C)", warn: 30, crit: 38, query: [ { technology: prometheus, says: "silo_grain_celsius{$F}" } ] }
  drying-step: { view: drying, element: dryer, live: live-value, label: "step", query: [ { technology: prometheus, says: "dryer_step{$F}" } ] }
  drying-elapsed: { view: drying, element: dryer, live: live-value, label: "running for", unit: second, query: [ { technology: prometheus, says: "dryer_elapsed_seconds{$F}" } ] }
  drying-left: { view: drying, element: dryer, live: live-value, label: "still needs", unit: second, query: [ { technology: prometheus, says: "dryer_remaining_seconds{$F}" } ] }
  drying-batches: { view: drying, element: dryer, live: live-series, label: "batches tonight", query: [ { technology: prometheus, says: "dryer_batches{$F}", items_by: bay } ], item_names: { a: "the east bay", b: "the west bay" } }
''',
}
MAPPINGS = {
    "drying-run": '''mapping: drying-run
kind: procedure
summary: "How a night's harvest is dried: loaded, heated, cooled and unloaded to the silo before the morning."
provenance: { src: asserted-by-human, by: "tessa (gardener)", as_of: now }
steps:
  - "the yard crew loads the dryer from the evening's trailers"
  - "the dryer-controller heats the batch until the grain reads dry"
  - "the dryer-controller cools the batch with outside air"
  - "the auger unloads the batch into the silo, where the silo-controller reads the fill"
''',
}
# THE GARDEN'S OWN DRAWINGS: code of the garden, named by the page and never part of the law. It draws with the asset's
# kit, so every element it draws is recorded — its pattern, its id, the being it depicts.
DRAWINGS = '''"""The co-operative's own drawings for its page (the garden's code, named by the page's `view.drawings`)."""
from view_kit import node, store, gate, flow, band, action_btn, figure


def silo():
    b = [band(20, 16, 700, "Grain arrives, is stored, and is watched"),
         node(20, 60, 180, 48, "Trailer", "brings a load", cls="ext"),
         gate(300, 84, "room left?", 120, 44),
         store(400, 50, 170, 70, "Silo", "the stored grain", bean="silo-controller", eid="silo"),
         node(600, 60, 170, 48, "Silo controller", "reads the fill", bean="silo-controller"),
         node(600, 160, 170, 48, "Field radio", "carries the readings", bean="field-radio"),
         node(400, 160, 170, 48, "Hill pump", "the hill farm's", bean="hill-pump"),
         flow(200, 84, 240, 84, "unload"), flow(360, 84, 400, 84, "yes", cls="accent"),
         action_btn(20, 160, 170, "Start fans", "starts the silo fans"),
         action_btn(20, 210, 170, "Radio reset", "resets the field radio"),
         action_btn(200, 210, 170, "Pump stop", "stops the hill pump")]
    return ("The silo", figure(800, 260, "".join(b), "the silo filling"),
            "A <b>trailer</b> unloads when the <b>gate</b> finds room; the <b>dryer</b> feeds it at night.",
            "Room for every load, every day of the harvest.")


def drying():
    b = [node(20, 40, 180, 48, "Yard crew", "loads the dryer", cls="ext"),
         node(280, 40, 200, 48, "Dryer", "heats, then cools", bean="dryer-controller", eid="dryer"),
         store(560, 30, 160, 70, "Silo", "takes the dry grain", bean="silo-controller"),
         flow(200, 64, 280, 64, "load"), flow(480, 64, 560, 64, "unload", cls="accent")]
    return ("The drying run", figure(760, 140, "".join(b), "the night's drying run"),
            "A batch is <b>loaded</b>, heated, cooled and unloaded before the morning.",
            "Dry grain in the silo before six.")


COMPOSERS = {"silo": silo, "drying": drying}
'''


def put(rel, text):
    p = os.path.join(G, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def get(rel):
    with open(os.path.join(G, *rel.split("/")), encoding="utf-8") as fh:
        return fh.read()


def gate():
    r = run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G)
    out = r.stdout + r.stderr
    if "Traceback" in out:
        TRACES.append(out[-600:])
    return out, r.returncode


def last(out):
    return (out.strip().splitlines() or [""])[-1]


r = run(sys.executable, os.path.join(ROOT, "seed", "germinate.py"), G, "--gardener", "tessa", cwd=T)
check("a garden germinates, kept by tessa", r.returncode == 0 and os.path.isfile(os.path.join(G, "beans", "tessa.md")),
      r.stdout + r.stderr)
if r.returncode != 0:
    shutil.rmtree(T, ignore_errors=True)
    print("\nview: %d failed" % len(FAILS))
    sys.exit(1)
run("git", "config", "user.name", "tessa", cwd=G)
run("git", "config", "user.email", "tessa@example.org", cwd=G)
VOCAB0 = get("VOCAB.md")
put("VOCAB.md", VOCAB0.replace("local_terms: []", "extends_profiles: [network, knowledge, view]\nlocal_terms: []", 1))
for _id, _t in BEANS.items():
    put(f"beans/{_id}.md", "---\n" + _t + "---\n" + _id + ", as the co-operative records it.\n")
for _id, _t in MAPPINGS.items():
    put(f"mappings/{_id}.md", "---\n" + _t + "---\nThe drying run.\n")
put("bin/drawings.py", DRAWINGS)
r = run(sys.executable, os.path.join(G, "bin", "dmsave.py"), "tessa", "RULE-CHANGE: the co-operative's page of drawings",
        "--body", "- action: VOCAB.md extends network, knowledge and view; " +
        ", ".join(f"[[{b}]]" for b in list(BEANS) + list(MAPPINGS)) + " recorded, and bin/drawings.py, the drawings.",
        cwd=G)
check("the page, its beings and its procedure are saved through the gate, with 0 errors and 0 warnings",
      r.returncode == 0 and " 0 error(s), 0 warning(s)" in (r.stdout + r.stderr), (r.stdout + r.stderr)[-1500:])
SAVED = {rel: get(rel) for rel in ["beans/grain-page.md", "beans/watcher.md", "beans/silo-controller.md", "VOCAB.md"]}


def restore():
    run("git", "checkout", "--", ".", cwd=G)


# ------------------------------------------------------------------ part 1: the law
out, rc = gate()
check("the whole garden passes: 0 errors, 0 warnings — a second, a day and a percent occupied, no prediction warned of",
      rc == 0 and last(out).endswith("0 error(s), 0 warning(s)") and "prediction came true" not in out, out[-800:])

PAGE = SAVED["beans/grain-page.md"]
REFUSED = [
    ("a unit the law has not got (celsius)", "beans/grain-page.md",
     'label: "grain temperature (°C)", warn', 'label: "grain temperature", unit: celsius, warn',
     ("grain-page", "celsius", "units")),
    ("a reservoir with no thresholds", "beans/grain-page.md",
     "    thresholds:\n      - { fullness: { count: 90, unit: percent }, label: \"divert the next loads\" }\n"
     "      - { fullness: { count: 98, unit: percent }, label: \"stop filling\" }\n", "",
     ("grain-page", "reservoir", "thresholds")),
    ("a fill no binding gives", "beans/grain-page.md", "fill: silo-fill", "fill: silo-level",
     ("grain-page", "silo-level", "view_bindings")),
    ("a binding on a drawing the page has not got", "beans/grain-page.md", "silo-fill: { view: silo,",
     "silo-fill: { view: barn,", ("grain-page", "barn", "views")),
    ("an address restated on the page", "beans/grain-page.md", "{ being: silo-controller, system: ipv4, what",
     "{ being: silo-controller, system: ipv4, at: 192.0.2.40, what", ("grain-page", "view.reference", "`at`")),
    ("a stored list of patterns", "beans/grain-page.md", "unit: percent, warn: 80",
     "unit: percent, live_patterns: [live-value], warn: 80", ("grain-page", "live_patterns")),
    ("a deadline written as a bare quantity", "beans/grain-page.md",
     "deadline: { of: time, measure: { count: 7, unit: hour } }", "deadline: { count: 7, unit: hour }",
     ("grain-page", "deadline")),
    ("a stride on a walk with no meter (routine)", "beans/grain-page.md",
     "every: { of: time, every: { count: 5, unit: minute } }", "every: { of: routine, every: { count: 5, unit: minute } }",
     ("grain-page", "routine", "metered")),
    ("a repetition written as a length", "beans/grain-page.md",
     "every: { of: time, every: { count: 5, unit: minute } }", "every: { count: 5, unit: minute }",
     ("grain-page", "every")),
    ("a race with no step", "beans/grain-page.md", "    step_at: drying-step\n", "",
     ("grain-page", "race", "step_at")),
    ("a query in a technology outside the catalogue", "beans/grain-page.md",
     'technology: prometheus, says: "silo_fill_ratio', 'technology: silo-watch, says: "silo_fill_ratio',
     ("grain-page", "silo-watch", "technology")),
    ("a threshold in seconds", "beans/grain-page.md", "{ fullness: { count: 90, unit: percent }",
     "{ fullness: { count: 90, unit: second }", ("grain-page", "second", "ratio")),
    ("a page opening on a machine", "beans/grain-page.md", "opens_on: grain-coop", "opens_on: silo-controller",
     ("grain-page", "silo-controller", "org")),
    ("a monitor the garden does not hold", "beans/grain-page.md", "- { monitor: watcher,", "- { monitor: barn-watcher,",
     ("grain-page", "barn-watcher")),
    ("an inspect pointer to a field the being does not state", "beans/grain-page.md",
     "pipes: { bean: silo-controller, field: pipes }", "pipes: { bean: silo-controller, field: ducts }",
     ("grain-page", "ducts")),
    ("a monitor's settings pointing at a field it does not state", "beans/grain-page.md",
     "settings: { bean: watcher, field: alert_rules }", "settings: { bean: watcher, field: alarms }",
     ("grain-page", "alarms")),
    ("a garden that does not extend view", "VOCAB.md", "[network, knowledge, view]", "[network, knowledge]",
     ("grain-page", "view", "--extend view")),
]
for _name, _rel, _old, _new, _words in REFUSED:
    _orig = get(_rel)
    if _old not in _orig:
        check(f"REFUSED: {_name}", False, f"the probe could not be written: {_old!r} is not in {_rel}")
        continue
    put(_rel, _orig.replace(_old, _new, 1))
    out, rc = gate()
    check(f"REFUSED by name: {_name}", rc == 1 and bool(said(out, "ERROR", *_words)),
          said(out, "ERROR") or out[-700:])
    put(_rel, _orig)

# THE ONE THE GATE CANNOT REFUSE. The schema language has no "only on the bean that carries another term": a `views`
# entry written on a being passes the gate, and the asset refuses it (part 2), as test/assets.py does for every profile.
_ctl = get("beans/silo-controller.md")
put("beans/silo-controller.md", _ctl.replace("details:\n", "views:\n  stray:\n    draws: { bean: silo-controller }\n"
                                             "    purpose: p\n    outcome: o\n    stages: [ { label: a, doer: b } ]\n"
                                             "    questions: [ { lens: orient, ask: q } ]\n    archetype: health-chain\n"
                                             "    blind: [ { what: w } ]\ndetails:\n", 1))
out, rc = gate()
check("a view written on a being, not on the page, passes the gate: the schema language cannot say where a term sits",
      rc == 0, out[-600:])
put("beans/silo-controller.md", _ctl)

check("NOTHING above ended in a traceback: every case is a refusal or a pass", not TRACES, TRACES[:2])
shutil.rmtree(T, ignore_errors=True)
print("\nview: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
