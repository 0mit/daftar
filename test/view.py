#!/usr/bin/env python3
"""The `view` profile and its asset in a garden of the core (v1 part 12: today's suite, ported): a page of drawings,
judged by the core's gate, drawn by `assets/view`, and closed by default.

A garden of the core is grown here (test/grow.py) taking the profile; its page, its beings and its procedure are
invented — a grain co-operative's silo and its drying run — written in statements, each drawing a `draw` of the page's
bean, and every one of them passes the core's gate. Then:

  part 1, the law  the page passes with 0 errors; each write the core refuses is refused by name (a value no drawing of
                   the page holds, a drawing the page does not name, a garden that does not take the profile — the rule
                   `profile` naming it, a page's visibility other than public or private); what today's gate refused of
                   a page's form that the core does not judge yet — a value's unit, a technology outside the catalogue,
                   a threshold's quantity, a deadline's and a repetition's form, a frame that is no line, a signal
                   nobody published — is test/ported.yaml's
  part 2, the asset  the asset's own checks, its report, its import, its bundle and its served page, over the page as
                   statements (view_core.py reads each being for it)
"""
import os, re, shutil, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "test"))
import grow  # noqa: E402
FAILS, TRACES = [], []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:900]))
    if not cond:
        FAILS.append(name)


def run(*a, cwd=None, env=None):
    return subprocess.run(list(a), capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd,
                          env=dict(os.environ, **(env or {})))


def said(out, rule, *words):
    """The core's findings that name every one of the words — `<rule>  <where>: <what>`, one a line, every one an
    error; `rule` None for any rule: a refusal is read by what it names."""
    return [ln for ln in out.splitlines() if (rule is None or ln.split(" ", 1)[0] == rule) and all(w in ln for w in words)
            and not ln.startswith("core check")]


T = tempfile.mkdtemp(prefix="dmview-")
G = os.path.join(T, "garden-grain")

BEANS = {
    "grain-coop": '''bean: grain-coop
kind: org
title: The grain co-operative
summary: The co-operative that stores and dries its members' grain.
statements:
  - say: {by: tessa, at: now, note: tessa (gardener)}
  - own: {id: own, of: self, by: tessa}
''',
    "hill-farm": '''bean: hill-farm
kind: org
title: The hill farm
summary: A member farm that keeps a pump of its own.
statements:
  - say: {by: tessa, at: now, note: tessa (gardener)}
  - own: {id: own, of: self, by: tessa}
''',
    "silo-controller": '''bean: silo-controller
kind: host
title: The silo controller
summary: The machine that reads the silo's fill and runs its fans.
statements:
  - read: {by: tessa, at: now, note: tessa (gardener)}
  - name: {id: serial, by: anchor-serial, of: self, as: SN-SILO-0417}
  - own: {id: own, of: self, by: grain-coop}
  - answer: {id: answer-law, by: tessa, of: self, as: law}
  - be: {id: at-1, by: self, at: 192.0.2.40, as: location, placed: {openness: here, observed: '2026-10-02'}}
  - serve: {id: serves-http, by: self, at: [192.0.2.40, 'tcp-port:80'], through: http}
  - serve: {id: serves-http-2, by: self, at: [192.0.2.40, 'tcp-port:443'], through: http}
details:
  endpoints:
    serves-http:
      exposure: lan
      observed: '2026-10-02'
    serves-http-2:
      confidentiality: encrypted
      exposure: lan
      observed: '2026-10-02'
  provides_habitat: linux-baremetal
  processes:
  - proc: fan-driver
    user: silo
    role: switches the fans
    config: fans.conf
    rail: air
  - proc: fill-reader
    user: silo
    role: reads the level sensor
    config: sensor.conf
    rail: fill
  pipes:
  - from: level sensor
    to: fill-reader
    channel: serial
    at: /dev/ttyS1
    config: sensor 9600 baud
    rail: fill
  - from: fill-reader
    to: exporter
    channel: file
    at: /run/silo/fill
    config: every 30 seconds
    rail: fill
''',
    "dryer-controller": '''bean: dryer-controller
kind: host
title: The dryer controller
summary: The machine that runs the grain dryer's burner and its batches.
statements:
  - read: {by: tessa, at: now, note: tessa (gardener)}
  - name: {id: serial, by: anchor-serial, of: self, as: SN-DRY-0981}
  - own: {id: own, of: self, by: grain-coop}
  - answer: {id: answer-law, by: tessa, of: self, as: law}
  - be: {id: at-1, by: self, at: 192.0.2.41, as: location, placed: {openness: here, observed: '2026-10-02'}}
  - serve: {id: serves-ssh, by: self, at: [192.0.2.41, 'tcp-port:22'], through: ssh}
details:
  endpoints:
    serves-ssh:
      exposure: lan
      observed: '2026-10-02'
''',
    "field-radio": '''bean: field-radio
kind: host
title: The field radio
summary: Tessa's own radio link from the silo to the barn.
statements:
  - read: {by: tessa, at: now, note: tessa (gardener)}
  - name: {id: serial, by: anchor-serial, of: self, as: SN-RADIO-2210}
  - own: {id: own, of: self, by: tessa}
  - be: {id: at-1, by: self, at: 192.0.2.60, as: location, placed: {openness: here, observed: '2026-10-02'}}
''',
    "hill-pump": '''bean: hill-pump
kind: host
title: The hill farm's pump
summary: The hill farm's own irrigation pump controller.
statements:
  - read: {by: tessa, at: now, note: tessa (gardener)}
  - name: {id: serial, by: anchor-serial, of: self, as: SN-PUMP-3302}
  - own: {id: own, of: self, by: hill-farm}
  - answer: {id: answer-law, by: tessa, of: self, as: law}
  - be: {id: at-1, by: self, at: 192.0.2.70, as: location, placed: {openness: here, observed: '2026-10-02'}}
''',
    "prometheus": '''bean: prometheus
kind: product
title: Prometheus
summary: The monitoring system the co-operative runs, recorded so its copy has a type to be an instance of.
statements:
  - say: {by: tessa, at: now, note: tessa (gardener)}
  - name: {id: identifier, by: anchor-identifier, of: self, as: 'technology:prometheus'}
  - own: {id: own, of: self, by: {someone: org}, note: the Prometheus authors}
  - answer: {id: answer-law, by: tessa, of: self, as: law}
''',
    "yard-monitor": '''bean: yard-monitor
kind: instance
title: The yard-monitor
summary: 'The co-operative''s running monitor: it probes the controllers and keeps their readings.'
statements:
  - read: {by: tessa, at: now, note: tessa (gardener)}
  - own: {id: own, of: self, from: silo-controller}
  - be: {id: at-1, by: self, at: 'silo-controller:/srv/yard-monitor', as: location, placed: {openness: here, observed: '2026-10-02'}}
  - be: {id: lives-in, by: self, at: silo-controller, as: habitat}
  - run: {id: instance-of, by: self, of: prometheus}
  - need: {id: reaches-silo-web, by: self, of: [silo-controller], through: http}
  - need: {id: reaches-dryer-shell, by: self, of: [dryer-controller], through: ssh}
  - need: {id: reaches-radio-ping, by: self, of: [field-radio], through: icmp}
  - need: {id: reaches-pump-ping, by: self, of: [hill-pump], through: icmp}
  - need: {id: reaches-pump-snmp, by: self, of: [hill-pump], through: snmp}
  - use: {id: uses-technology-prometheus, by: self, of: 'technology:prometheus'}
  - do: {id: does-monitoring, by: self, as: monitoring}
details:
  responsibility:
    from:
      bean: silo-controller
  monitoring:
    alerts:
    - name: SiloNearlyFull
      expr: silo_fill_ratio > 0.9
      for: 15m
      severity: warning
      summary: the silo is over nine tenths full
    alerting:
      email_to: keeper@example.org
      email_from: yard-monitor@example.org
      smarthost: host.docker.internal:25
    snmp:
      env_file: snmp.env
      auths:
        yard:
          community_env: SNMP_YARD_COMMUNITY
          version: '2'
      modules:
        hill-pump:
        - modules:
          - if_mib
          auth: yard
        - modules:
          - ip_mib
          auth: yard
          org: grain-coop
    filesystems:
    - being: silo-controller
      user: reader
      path: /data
    grafana_plugins:
    - marcusolsson-dynamictext-panel@6.3.0
''',
    "grain-page": '''bean: grain-page
kind: service
title: The silo and the dryer, drawn
summary: 'The co-operative''s page of drawings: the silo filling, and the night''s drying run.'
statements:
  - say: {by: tessa, at: now, note: tessa (gardener)}
  - own: {id: own, of: self, by: grain-coop}
  - answer: {id: answer-law, by: tessa, of: self, as: law}
  - be: {id: at-1, by: self, at: 'uri:https://grain.example.org/page/', as: location, placed: {openness: here}}
  - draw: {id: silo, by: self, of: [silo-controller], drawing: {purpose: Keeps room in the silo for the rest of the harvest., outcome: The silo never fills before the last load is in., stages: [{label: Read the fill, doer: 'the level sensor, every half minute', beings: [{being: silo-controller}], uses: [{technology: prometheus}]}, {label: Warn before full, doer: the yard-monitor}, {label: Send loads elsewhere, doer: the yard crew}], questions: [{lens: orient, ask: 'What keeps the silo from overflowing?'}, {lens: operate, ask: 'Is there room for tomorrow''s loads?'}], processes: {bean: silo-controller, field: processes}, pipes: {bean: silo-controller, field: pipes}, actions: [{element: start-fans, tool: start-fans, confirm: 'Start the silo fans now?'}, {element: radio-reset, tool: radio-reset, confirm: 'Reset the field radio?', acts_on: field-radio}, {element: pump-stop, tool: pump-stop, confirm: 'Stop the hill pump?', acts_on: hill-pump}], archetype: reservoir, blind: [{what: the grain's moisture inside the silo, why: no probe reaches inside}], notes: [{note: 'at nine tenths full, send the next loads to the hill farm'}], fill: silo-fill, thresholds: [{fullness: {count: '90', unit: '%'}, label: divert the next loads}, {fullness: {count: '98', unit: '%'}, label: stop filling}], forecast: silo-full-in, parts: [{bind: silo-up}, {bind: grain-temperature}], correlate: [{traces: [{bind: silo-fill}, {bind: grain-temperature}], span: {of: time, measure: {count: '12', unit: h}}, every: {of: time, every: {count: '5', unit: min}}}], values: {silo-fill: {element: silo, live: live-value, label: silo fill, unit: '%', warn: '80', crit: '90', query: [{technology: prometheus, says: 'silo_fill_ratio{$F} * 100'}]}, silo-full-in: {element: silo, live: live-value, label: until full, unit: d, query: [{technology: prometheus, says: 'silo_days_to_full{$F}'}]}, silo-up: {element: silo-controller, live: live-state}, radio-up: {element: field-radio, live: live-state}, pump-up: {element: hill-pump, live: live-state}, grain-temperature: {element: silo, live: live-value, label: grain temperature (°C), warn: '30', crit: '38', query: [{technology: prometheus, says: 'silo_grain_celsius{$F}'}]}}}}
  - draw: {id: drying, by: self, of: [drying-run], drawing: {purpose: Dries each night's harvest before the morning's loads arrive., outcome: The batch is unloaded before six in the morning., stages: [{label: Load the dryer, doer: the yard crew}, {label: Heat and cool, doer: the dryer controller, beings: [{being: dryer-controller}]}, {label: Unload to the silo, doer: the auger}], questions: [{lens: operate, ask: 'Will the batch be out before six?'}], archetype: race, blind: [{what: the burner's fuel, why: the tank has no gauge}], step_at: drying-step, elapsed: drying-elapsed, eta: drying-left, deadline: {of: time, measure: {count: '7', unit: h}}, checkpoints: [{after: {of: time, measure: {count: '3', unit: h}}, label: heating should be done}], numbers: [{bind: drying-batches}], correlate: [{traces: [{bind: grain-temperature}], band: drying-step, relate: {across: grain-temperature, measure: drying-left, bins: '4', at_step: '2', keep: positive}}], values: {drying-step: {element: dryer, live: live-value, label: step, query: [{technology: prometheus, says: 'dryer_step{$F}'}]}, drying-elapsed: {element: dryer, live: live-value, label: running for, unit: s, query: [{technology: prometheus, says: 'dryer_elapsed_seconds{$F}'}]}, drying-left: {element: dryer, live: live-value, label: still needs, unit: s, query: [{technology: prometheus, says: 'dryer_remaining_seconds{$F}'}]}, drying-batches: {element: dryer, live: live-series, label: batches tonight, query: [{technology: prometheus, says: 'dryer_batches{$F}', items_by: bay}], item_names: {a: the east bay, b: the west bay}}}}}
  - draw: {id: page, by: self, of: [silo, drying], page: {drawings: 'file:bin/drawings.py', opens_on: grain-coop, glossary: {dryer: the machine that takes the water out of the harvest before it is stored}, reference: [{being: silo-controller, system: ipv4, what: reads the fill and runs the fans}, {being: dryer-controller, system: ipv4, what: runs the dryer's batches}, {being: field-radio, system: ipv4, what: carries the readings to the barn}, {being: hill-pump, system: ipv4, what: the hill farm's pump}], fields: [{kind: host, fact: summary, shown_from: understand}, {kind: host, fact: be.location, shown_from: inspect}], monitors: [{monitor: yard-monitor, settings: {bean: yard-monitor, field: monitoring}}]}}
''',
}
MAPPINGS = {
    "drying-run": '''bean: drying-run
kind: procedure
summary: 'How a night''s harvest is dried: loaded, heated, cooled and unloaded to the silo before the morning.'
statements:
  - say: {by: tessa, at: now, note: tessa (gardener)}
details:
  steps:
  - the yard crew loads the dryer from the evening's trailers
  - the dryer-controller heats the batch until the grain reads dry
  - the dryer-controller cools the batch with outside air
  - the auger unloads the batch into the silo, where the silo-controller reads the fill
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
    r = run(sys.executable, os.path.join(G, "core", "check.py"), ".", cwd=G)
    out = r.stdout + r.stderr
    if "Traceback" in out:
        TRACES.append(out[-800:])
    return out, r.returncode


def last(out):
    return (out.strip().splitlines() or [""])[-1]


def in_drawing(page, did, add):
    """The page with `add`, a fragment of a flow mapping, written first in the form of its drawing `did`."""
    head = f"  - draw: {{id: {did}, "
    i = page.index(head)
    j = page.index("drawing: {", i) + len("drawing: {")
    return page[:j] + add + ", " + page[j:]


# A RELEASE OF THE CORE, made of this tree as seed/LANGUAGE ships it — every profile's asset among it — and tagged, so
# the garden grown from it records a release its upgrade can be run at (`--extend`, `--retract`).
REL = grow.release(os.path.join(T, "release"))
TAG = "v1.0.0"

# THE GARDEN IS GROWN WITH THE PROFILES IT TAKES: `--profile` writes them in VOCAB.md, and the asset arrives with them.
r = grow.garden(REL, G, "tessa", "--profile", "network", "--profile", "knowledge", "--profile", "view")
check("a garden of the core germinates with --profile network, knowledge and view, kept by tessa: VOCAB.md takes the "
      "three, and assets/view/ arrived with the language",
      r.returncode == 0 and os.path.isfile(os.path.join(G, "beans", "tessa.md"))
      and "profiles: [network, knowledge, view]" in open(os.path.join(G, "VOCAB.md"), encoding="utf-8").read()
      and os.path.isfile(os.path.join(G, "assets", "view", "bin", "view.py")), r.out)
if r.returncode != 0:
    shutil.rmtree(T, ignore_errors=True)
    print("\nview: %d failed" % len(FAILS))
    sys.exit(1)
run("git", "config", "user.name", "tessa", cwd=G)
run("git", "config", "user.email", "tessa@example.org", cwd=G)
_v = get("VOCAB.md")
put("VOCAB.md", _v.replace("namespaces: []\n", "kinds:\n  - { kind: procedure, nature: sayable }\nnamespaces:\n"
                           "  - { namespace: anchor-identifier, once: 'true' }\n  - { namespace: anchor-serial, once: 'true' }\n", 1))
for _id, _t in BEANS.items():
    put(f"beans/{_id}.md", "---\n" + _t + "---\n" + _id + ", as the co-operative records it.\n")
for _id, _t in MAPPINGS.items():
    put(f"mappings/{_id}.md", "---\n" + _t + "---\nThe drying run.\n")
put("bin/drawings.py", DRAWINGS)
r = run(sys.executable, os.path.join(G, "bin", "save.py"), "tessa", "the co-operative's page of drawings",
        "--body", "- action: " + ", ".join(f"[[{b}]]" for b in list(BEANS) + list(MAPPINGS)) +
        " recorded, and bin/drawings.py, the drawings. RULE-CHANGE: VOCAB.md holds the procedure and the namespaces "
        "the serials and identifiers are given in.", cwd=G)
check("the page, its beings and its procedure are saved through the core's gate, with 0 errors",
      r.returncode == 0 and "— 0 error(s)" in (r.stdout + r.stderr), (r.stdout + r.stderr)[-1500:])
SAVED = {rel: get(rel) for rel in ["beans/grain-page.md", "beans/yard-monitor.md", "beans/silo-controller.md", "VOCAB.md"]}


def restore():
    run("git", "checkout", "--", ".", cwd=G)


# ------------------------------------------------------------------ part 1: the law
out, rc = gate()
check("the whole garden passes the core's gate: 0 errors", rc == 0 and last(out).endswith("— 0 error(s)"), out[-800:])

PAGE = SAVED["beans/grain-page.md"]
REFUSED = [
    ("a fill no value of the page gives", "beans/grain-page.md", "fill: silo-fill,", "fill: silo-level,",
     ("grain-page", "silo-level", "no value of this page")),
    ("a drawing the page does not name", "beans/grain-page.md", "  - draw: {id: page, by: self, of: [silo, drying],",
     "  - draw: {id: page, by: self, of: [silo],", ("grain-page", "drying", "does not name")),
    ("a garden that does not take view", "VOCAB.md", "profiles: [network, knowledge, view]", "profiles: [network, knowledge]",
     ("grain-page", "view")),
]
for _name, _rel, _old, _new, _words in REFUSED:
    _orig = get(_rel)
    if _old not in _orig:
        check(f"REFUSED: {_name}", False, f"the probe could not be written: {_old!r} is not in {_rel}")
        continue
    put(_rel, _orig.replace(_old, _new, 1))
    out, rc = gate()
    check(f"REFUSED by name: {_name}", rc == 1 and bool(said(out, None, *_words)), said(out, None) or out[-700:])
    put(_rel, _orig)

# THE ONE THE GATE CANNOT REFUSE. The schema language has no "only on the bean that carries another term": a `views`
# entry written on a being passes the gate, and the asset refuses it, as test/assets.py finds it for every profile.
DMVIEW = os.path.join(G, "assets", "view", "bin", "view.py")


def dmview(*a, garden=None):
    r = run(sys.executable, DMVIEW, *a, *(("--garden", garden) if garden else ()), cwd=G)
    out = r.stdout + r.stderr
    if "Traceback" in out:
        TRACES.append(out[-800:])
    return out, r.returncode


_ctl = get("beans/silo-controller.md")
put("beans/silo-controller.md", _ctl.replace("statements:\n", "statements:\n  - draw: {id: stray, by: self, of: [silo-controller], "
                                             "drawing: {purpose: p, outcome: o, stages: [{label: a, doer: b}], questions: "
                                             "[{lens: orient, ask: q}], archetype: health-chain, blind: [{what: w}]}}\n", 1))
out, rc = gate()
check("a drawing written on a being that is no page is refused by the core's gate (rule `profile`): a drawing is a page's",
      rc == 1 and bool(said(out, "profile", "silo-controller", "a drawing is a page's")), out[-600:])
put("beans/silo-controller.md", _ctl)

# ------------------------------------------------------------------ part 2: the asset
# The code's own checks, ported from the tool it was, over this garden: its check, its report and the page the report
# carries, its import, its bundle, its served page — and what is new: the genos a being is read by, the organisation it
# belongs to (following `via`), closed by default; race and correlate; units read from the law; a second adapter beside
# the first; the opt-in act; the cookbook's recipe.
out, rc = dmview("check")
check("dmview check: the page and its drawings agree", rc == 0 and "the page and its drawings agree" in out, out[-800:])
_page = get("beans/grain-page.md")
for _bad in ("file:../drawings.py", "file:/tmp/drawings.py", "file:bin/../../drawings.py", "file:beans/grain-page.md"):
    put("beans/grain-page.md", _page.replace("drawings: 'file:bin/drawings.py'", f"drawings: '{_bad}'", 1))
    out, rc = dmview("check")
    check(f"the drawing module is code the host runs: `view.drawings: {_bad}`, outside the garden or no Python file, is "
          f"refused, and nothing of it runs", rc != 0 and "inside the garden" in out, out[-600:])
put("beans/grain-page.md", _page)
out, rc = dmview("elements", "silo")
check("dmview elements: ids are the slugs of labels, and each records the being it depicts",
      rc == 0 and re.search(r"(?m)^silo\s+store\s+silo-controller", out) and re.search(r"(?m)^start-fans\s+action", out), out)

DRAWINGS_T = get("bin/drawings.py")
SILO_FORM = "  - draw: {id: silo, by: self, of: [silo-controller], drawing: {"
MAPPING_T = get("mappings/drying-run.md")
YARD_T = get("beans/yard-monitor.md")
PAGE_T = get("beans/grain-page.md")
ASSET_REFUSED = [
    ("a binding on an element the drawing does not have", "beans/grain-page.md",
     "silo-up: {element: silo-controller,", "silo-up: {element: auger,", ("silo-up", "auger")),
    ("an action on an element that is not a button", "beans/grain-page.md",
     "{element: start-fans, tool: start-fans,", "{element: silo-controller, tool: start-fans,",
     ("start-fans", "not an action element")),
    ("`processes` without `pipes`", "beans/grain-page.md", ", pipes: {bean: silo-controller, field: pipes}", "",
     ("processes", "pair")),
    ("a race that draws a being, not a procedure", "beans/grain-page.md", "draw: {id: drying, by: self, of: [drying-run],",
     "draw: {id: drying, by: self, of: [dryer-controller],", ("race", "procedure")),
    ("a race whose procedure branches", "mappings/drying-run.md",
     "  steps:\n  - the yard crew loads the dryer from the evening's trailers\n  - the dryer-controller heats the batch until the grain reads dry\n",
     "  steps:\n  - { id: load, do: load, next: [ { to: heat, when: dry }, { to: cool, when: wet } ] }\n"
     "  - { id: heat, do: heat, next: [ { to: cool } ] }\n", ("branches", "load")),
    ("a drawing that shows an address", "bin/drawings.py", '"Silo controller", "reads the fill"',
     '"Silo controller", "reads 192.0.2.40"', ("shows 192.0.2.40", "no address")),
    ("a drawing the page does not list", "bin/drawings.py", 'COMPOSERS = {"silo": silo, "drying": drying}',
     'COMPOSERS = {"silo": silo, "drying": drying, "barn": drying}', ("barn", "does not list")),
    ("a drawing the module does not draw", "bin/drawings.py", 'COMPOSERS = {"silo": silo, "drying": drying}',
     'COMPOSERS = {"silo": silo}', ("drying", "no drawing")),
    ("a story longer than its lens holds", "beans/grain-page.md", "{label: Send loads elsewhere, doer: the yard crew}",
     ", ".join(["{label: Send loads elsewhere, doer: the yard crew}"] * 4), ("stages", "orient")),
    ("a fact on a card that is no fact a bean states", "beans/grain-page.md", "{kind: host, fact: summary,",
     "{kind: host, fact: summery,", ("summery",)),
    ("a monitor whose technology no adapter here reads", "beans/yard-monitor.md",
     "of: 'technology:prometheus'}", "of: 'technology:zabbix'}", ("yard-monitor", "zabbix", "no adapter")),
    ("a live-state on a being no monitor reaches", "beans/yard-monitor.md",
     "  - need: {id: reaches-radio-ping, by: self, of: [field-radio], through: icmp}\n", "", ("radio-up", "field-radio", "reaches")),
    ("a value no monitor of the page can compute", "beans/grain-page.md",
     "query: [{technology: prometheus, says: 'silo_days_to_full{$F}'}]", "query: [{technology: zabbix, says: silo.days}]",
     ("silo-full-in", "zabbix")),
    ("a page that states nowhere it is shown", "beans/grain-page.md",
     "  - be: {id: at-1, by: self, at: 'uri:https://grain.example.org/page/', as: location, placed: {openness: here}}\n", "",
     ("states nowhere it is shown", "uri")),
    ("a zoom from an element the drawing does not have", "beans/grain-page.md", SILO_FORM,
     SILO_FORM + "opens: [{element: auger, view: drying}], ", ("opens", "auger", "does not have")),
    ("a zoom into the drawing it is in", "beans/grain-page.md", SILO_FORM,
     SILO_FORM + "opens: [{element: silo, view: silo}], ", ("opens the drawing it is in",)),
    ("a story stage in more words than its lens holds a stage", "beans/grain-page.md",
     "{label: Send loads elsewhere, doer: the yard crew}",
     "{label: 'Send loads elsewhere, to the co-operative across the valley and the river', doer: the yard crew}",
     ("words", "orient")),
]
for _name, _rel, _old, _new, _words in ASSET_REFUSED:
    _orig = get(_rel)
    if _old not in _orig:
        check(f"dmview REFUSES: {_name}", False, f"the probe could not be written: {_old!r} is not in {_rel}")
        continue
    put(_rel, _orig.replace(_old, _new, 1))
    out, rc = dmview("check")
    check(f"dmview REFUSES by name: {_name}", rc == 2 and all(w in out for w in _words), out[-900:])
    put(_rel, _orig)

# ZOOM AND FRAME, AS THE GATE AND THE ASSET READ THEM
put("beans/grain-page.md", in_drawing(PAGE_T, "silo", "frame: place, opens: [{element: silo, view: drying}]"))
out, rc = dmview("check")
_g, _ = gate()
_rep, _ = dmview("report", "--out", os.path.join(T, "zoom.html"))
_html = open(os.path.join(T, "zoom.html"), encoding="utf-8").read() if os.path.isfile(os.path.join(T, "zoom.html")) else ""
check("a drawing laid out along place, whose silo opens the drying run, passes the gate and the asset, and the page "
      "carries the zoom", rc == 0 and " 0 error(s)" in _g and '"opens": [{"el": "silo", "view": "drying"}]' in _html,
      (out[-400:], _g[-400:], _rep[-300:]))
put("beans/grain-page.md", PAGE_T.replace("at: 'uri:https://grain.example.org/page/'", "at: 'uri:grain page'", 1))
_g, _rc = gate()
check("a page's place in `uri` is written as RFC 3986 writes it, or refused", _rc != 0 and "grain page" in _g, _g[-600:])
put("beans/grain-page.md", PAGE_T)

# A SIGNAL, BY ITS PUBLISHED NAME: the binding says what it measures, and the source adapter asks it in its own language
_sig = PAGE_T.replace("query: [{technology: prometheus, says: 'silo_days_to_full{$F}'}]", "signal: system.filesystem.utilization", 1)
put("beans/grain-page.md", _sig)
out, rc = dmview("check")
_g, _ = gate()
_rep, _ = dmview("report", "--out", os.path.join(T, "signal.html"))
_html = open(os.path.join(T, "signal.html"), encoding="utf-8").read() if os.path.isfile(os.path.join(T, "signal.html")) else ""
check("a binding that names a signal and no query passes the gate and the asset, and Prometheus is asked it by "
      "OpenTelemetry's name for it: avg(system_filesystem_utilization_ratio{…})",
      rc == 0 and " 0 error(s)" in _g and "avg(system_filesystem_utilization_ratio{" in _html, (out[-400:], _g[-300:]))
put("beans/grain-page.md", PAGE_T.replace(", query: [{technology: prometheus, says: 'silo_days_to_full{$F}'}]", "", 1))
out, rc = dmview("check")
check("...and a value with neither a query nor a signal is refused by the asset: nothing could ask it", rc != 0
      and "silo-full-in" in out, out[-600:])
put("beans/grain-page.md", PAGE_T)

import json
# THE SURFACES, AND WHAT EVERY ONE OF THEM MUST DO (the requirements a technology passes before daftar says it speaks it)
_conf = run(sys.executable, "-c", """
import json, os, re, sys
sys.path.insert(0, os.path.join(os.getcwd(), 'assets', 'view', 'lib')); sys.path.insert(0, os.path.join(os.getcwd(), 'bin'))
import view_model as vm, view_report
vm.init(os.getcwd())
p = view_report.payload()
ADDR = re.compile(r'(?<![\\w.])(?:\\d{1,3}\\.){3}\\d{1,3}(?![\\w.])')
out = {'where': p.get('where') or {}}
for code in vm.surfaces_here():
    s = vm.surface(code)
    docs = {k: s.render(p, key=k) for k in p['order']} if code == 'django' else {'*': s.render(p)}
    def has(doc, i):
        return ('data-el="%s"' % i) in doc or ('data-el=\\\\"%s\\\\"' % i) in doc
    missing = sorted({e['id'] for k, v in p['views'].items() for e in v['elements']
                      if not has(docs['*'] if code != 'django' else docs[k], e['id'])})
    given = set(ADDR.findall(json.dumps(p)))
    out[code] = {'technology': getattr(s, 'TECHNOLOGY', None), 'offline': getattr(s, 'OFFLINE', None), 'missing': missing,
                 'addresses': sorted(set(ADDR.findall(''.join(docs.values()))) - given)}
print('CONFORMANCE ' + json.dumps(out))
""", cwd=G)
try:
    _cj = json.loads(next(l for l in _conf.stdout.splitlines() if l.startswith('CONFORMANCE '))[len('CONFORMANCE '):])
except Exception:
    _cj = {}
_rows = {}
with open(os.path.join(ROOT, "seed", "knowledge", "technology-daftar.tsv"), encoding="utf-8") as _fh:
    _hdr = None
    for _ln in _fh:
        _c = _ln.rstrip("\n").split("\t")
        if _hdr is None:
            _hdr = _c
        else:
            _rows[_c[0]] = dict(zip(_hdr, _c))
_surf = sorted(k for k in _cj if k != "where")
check("every surface of the asset — %s — names the technology it speaks and says whether it works offline"
      % ", ".join(_surf), len(_surf) >= 3 and all(isinstance(_cj[k]["offline"], bool) and _cj[k]["technology"] == k for k in _surf),
      (_conf.stdout[-600:], _conf.stderr[-600:]))
check("...each carries every drawn element by the fact's id it stands for", all(not _cj[k]["missing"] for k in _surf),
      {k: _cj[k]["missing"][:5] for k in _surf})
check("...and none adds an address the scoped page it was given did not hold", all(not _cj[k]["addresses"] for k in _surf),
      {k: _cj[k]["addresses"] for k in _surf})
check("...and daftar says it speaks each only where the catalogue's row names this surface as its adapter",
      all((_rows.get(k) or {}).get("status") == "spoken" and (_rows.get(k) or {}).get("adapter") == f"assets/view/lib/surfaces/{k}.py"
          for k in _surf), {k: _rows.get(k) for k in _surf})
check("the page's own chain to the eye is engraved from its record: where it is shown",
      "grain.example.org" in str((_cj.get("where") or {}).get("svg", "")), str(_cj.get("where"))[:400])

# A DETAIL: a boundary opens as the region it draws, at a larger scale — the whole counts only what stands outside it
put("bin/drawings.py", DRAWINGS_T.replace('         node(20, 60, 180, 48, "Trailer", "brings a load", cls="ext"),',
    '         boundary(590, 40, 200, 180, "The controls", eid="controls"),\n         node(20, 60, 180, 48, "Trailer", "brings a load", cls="ext"),', 1)
    .replace("from view_kit import ", "from view_kit import boundary, ", 1))
put("beans/grain-page.md", in_drawing(PAGE_T, "silo", "opens: [{element: controls}]"))
out, rc = dmview("check")
_dt = run(sys.executable, "-c", """
import json, os, sys
sys.path.insert(0, os.path.join(os.getcwd(), 'assets', 'view', 'lib')); sys.path.insert(0, os.path.join(os.getcwd(), 'bin'))
import view_model as vm
vm.init(os.getcwd())
print('DETAILS ' + json.dumps({v['key']: v['details'] for v in vm.views()}))
""", cwd=G)
try:
    _dj = json.loads(next(l for l in _dt.stdout.splitlines() if l.startswith("DETAILS "))[len("DETAILS "):])
except Exception:
    _dj = {}
_d = (_dj.get("silo") or [{}])[0]
check("a boundary opens as a detail of its drawing: the region it draws, holding the parts inside it",
      rc == 0 and _d.get("el") == "controls" and {"silo-controller", "field-radio"} <= set(_d.get("inside") or []),
      (out[-400:], _dt.stdout[-300:], _dt.stderr[-300:]))
put("beans/grain-page.md", in_drawing(PAGE_T, "silo", "opens: [{element: trailer}]"))
out, rc = dmview("check")
check("...and a detail opened from a part that is no boundary is refused", rc != 0 and "a detail is the region a boundary draws" in out, out[-500:])
put("bin/drawings.py", DRAWINGS_T)
put("beans/grain-page.md", PAGE_T)

# CLOSED REGIONS: the flows between two closed regions are one line a pair, and a flow leaving one leaves from its edge
put("bin/drawings.py", DRAWINGS_T.replace('         node(20, 60, 180, 48, "Trailer", "brings a load", cls="ext"),',
    '         boundary(10, 40, 210, 90, "The yard", eid="yard"),\n'
    '         boundary(590, 40, 200, 180, "The controls", eid="controls"),\n'
    '         boundary(595, 150, 190, 64, "The radio", eid="radio"),\n'
    '         node(20, 60, 180, 48, "Trailer", "brings a load", cls="ext"),\n'
    '         flow(200, 100, 600, 100, "reports"), flow(600, 190, 200, 120, "answers"),', 1)
    .replace("from view_kit import ", "from view_kit import boundary, ", 1))
put("beans/grain-page.md", in_drawing(PAGE_T, "silo", "opens: [{element: yard}, {element: controls}, {element: radio}]"))
out, rc = dmview("check")
_cl = run(sys.executable, "-c", """
import json, os, sys
sys.path.insert(0, os.path.join(os.getcwd(), 'assets', 'view', 'lib')); sys.path.insert(0, os.path.join(os.getcwd(), 'bin'))
import view_model as vm
vm.init(os.getcwd())
v = next(v for v in vm.views() if v['key'] == 'silo')
print('CLOSED ' + json.dumps({'links': v['links'], 'details': v['details']}))
""", cwd=G)
try:
    _cj2 = json.loads(next(l for l in _cl.stdout.splitlines() if l.startswith("CLOSED "))[len("CLOSED "):])
except Exception:
    _cj2 = {"links": [], "details": []}
_L = {tuple(sorted((l["from"], l["to"]))): l for l in _cj2["links"]}
_yc = _L.get(("controls", "yard")) or {}
check("closed regions: the flows between two are ONE line, arrowed each way its flows go, saying how many it carries",
      rc == 0 and sorted(_yc.get("flows") or []) == ["answers", "reports"] and _yc.get("both") is True, (out[-400:], _cj2, _cl.stderr[-300:]))
_yg = next((l for l in _cj2["links"] if l["from"] == "yard" and l["to"] != "controls"), {})
check("...a flow leaving a closed region leaves from its edge, to the part it reaches, and keeps its words",
      _yg.get("flows") == ["unload"] and _yg.get("label") == "unload" and _yg.get("both") is False, _cj2["links"])
check("...a region inside a closed region is carried by it: no line reaches the inner one while the outer is closed",
      not any("radio" in (l["from"], l["to"]) for l in _cj2["links"])
      and "radio" in next((d["inside"] for d in _cj2["details"] if d["el"] == "controls"), []), _cj2)
check("...and a line is inside a region only when both its ends are: one leaving it is no part of its detail",
      not any(f in d["inside"] for d in _cj2["details"] for f in ("reports", "answers", "unload")), _cj2["details"])
put("bin/drawings.py", DRAWINGS_T)
put("beans/grain-page.md", PAGE_T)

# WHERE IT IS SHOWN: a URI is measured from no being; the one serving it says so in its own `endpoints`
put("beans/grain-page.md", PAGE_T.replace("  - be: {id: at-1, by: self, at: 'uri:https://grain.example.org/page/', as: location, placed: {openness: here}}\n",
    "  - be: {id: at-1, by: self, at: 'uri:https://grain.example.org/page/', as: location, placed: {openness: here}}\n"
    "  - be: {id: at-2, by: self, at: 'uri:https://192.0.2.40/page/', as: location, placed: {openness: here}}\n", 1))
out, rc = dmview("check")
_ws = run(sys.executable, "-c", """
import os, sys
sys.path.insert(0, os.path.join(os.getcwd(), 'assets', 'view', 'lib')); sys.path.insert(0, os.path.join(os.getcwd(), 'bin'))
import view_model as vm
vm.init(os.getcwd())
print('WHERE ' + vm.where_shown()[0])
""", cwd=G)
check("a page served at an address is answered by the being whose endpoints say so — on a public page the address "
      "drawn by its system alone", ">uri<" in _ws.stdout and "192.0.2.40" not in _ws.stdout and ">silo-controller<" in _ws.stdout,
      (_ws.stdout[-400:], _ws.stderr[-400:]))
check("...and one served where no being here says it answers is named, and not guessed",
      rc == 0 and "grain.example.org" in out and "no being here says it answers there" in out, out[-600:])
put("beans/grain-page.md", PAGE_T)

# THE SHEET: a title block of facts, clouds around what the last commit changed, and the garden's own palette
_sh = run(sys.executable, "-c", """
import json, os, sys
sys.path.insert(0, os.path.join(os.getcwd(), 'assets', 'view', 'lib')); sys.path.insert(0, os.path.join(os.getcwd(), 'bin'))
import view_model as vm
vm.init(os.getcwd())
vs = vm.views()
print('SHEET ' + json.dumps([{'key': v['key'], 'sheet': v['sheet'], 'changed': v['changed'], 'ids': [e['id'] for e in v['elements']]} for v in vs]))
""", cwd=G)
try:
    _sj = json.loads(next(l for l in _sh.stdout.splitlines() if l.startswith("SHEET "))[len("SHEET "):])
except Exception:
    _sj = []
check("every sheet's title block is made of facts the ledger holds: the page, the garden, the commit it is drawn from, "
      "and which sheet of how many", len(_sj) >= 2 and all(re.fullmatch(r"[0-9a-f]{12}", s["sheet"]["commit"])
      and s["sheet"]["of"] == len(_sj) and s["sheet"]["garden"] and s["sheet"]["shown"] for s in _sj)
      and [s["sheet"]["n"] for s in _sj] == list(range(1, len(_sj) + 1)), (_sh.stdout[-500:], _sh.stderr[-500:]))
check("...and a revision cloud is drawn only around a part the drawing draws", all(set(s["changed"]) <= set(s["ids"]) for s in _sj),
      [(s["key"], s["changed"]) for s in _sj])
put("drawings/palette.yaml", "modes:\n  night: { bg: \"#101418\", accent: \"#c9d38c\" }\n  day: { bg: \"#f4efe2\", accent: \"#5a6a26\" }\n"
    "  print: { bg: \"#ffffff\", fg: \"#000000\" }\n")
put("beans/grain-page.md", PAGE_T.replace("drawings: 'file:bin/drawings.py'", "drawings: 'file:bin/drawings.py', palette: 'file:drawings/palette.yaml'", 1))
out, rc = dmview("check")
_rep, _ = dmview("report", "--out", os.path.join(T, "palette.html"))
_html = open(os.path.join(T, "palette.html"), encoding="utf-8").read() if os.path.isfile(os.path.join(T, "palette.html")) else ""
check("a garden's own palette — its day, its night and paper — is drawn with: the grammar the asset's, the colours the garden's",
      rc == 0 and ".vw.light{--bg:#f4efe2;--accent:#5a6a26}" in _html and "@media print{.vw,.vw.light{--bg:#ffffff;--fg:#000000}}" in _html,
      (out[-400:], _rep[-300:]))
put("drawings/palette.yaml", "modes:\n  night: { accent: olive }\n  dusk: { bg: \"#000\" }\n")
out, rc = dmview("check")
check("...and a palette with a colour that is none, or a mode the sheet has not, is refused by name", rc != 0
      and "olive" in out and "dusk" in out, out[-600:])
put("beans/grain-page.md", PAGE_T)

# PIPES ALONE ARE WIRING: what a drawing draws may be joined by pipes and run no process of its own.
put("beans/grain-page.md", PAGE_T.replace("processes: {bean: silo-controller, field: processes}, ", "", 1))
out, rc = dmview("check")
check("dmview passes `pipes` without `processes`: pipes alone are wiring enough", rc == 0 and "processes" not in out, out[-700:])
put("beans/grain-page.md", PAGE_T)

# A REACH IT CANNOT PROBE IS SAID, NEVER DROPPED: a being with no endpoint of the protocol and no address to probe.
put("beans/yard-monitor.md", YARD_T.replace("  - need: {id: reaches-pump-snmp,", "  - need: {id: reaches-coop-web, by: self, of: [grain-coop], through: http}\n  - need: {id: reaches-pump-snmp,", 1))
out, rc = dmview("check")
check("dmview WARNS, and passes: a reach the adapter cannot probe (grain-coop over http: no endpoint, no address)",
      rc == 0 and "warn: monitor yard-monitor: reaches grain-coop over http, and does not probe it" in out, out[-700:])
put("beans/yard-monitor.md", YARD_T)

# --- the report, and the page it carries
out, rc = dmview("report")
check("dmview report without --out is refused, and writes nothing inside the garden unasked", rc == 2 and "--out" in out, out)
REPORT = os.path.join(T, "report.html")
out, rc = dmview("report", "--out", REPORT)
HTML = open(REPORT, encoding="utf-8").read() if os.path.isfile(REPORT) else ""
check("dmview report: one self-contained file with the runtime, the author mode and both drawings",
      rc == 0 and "viewMount" in HTML and "authbtn" in HTML and "The silo" in HTML and "The drying run" in HTML, out[-600:])
import json
_m = re.search(r'<script type="application/json" id="viewdata">(.*?)</script>', HTML, re.S)
P = json.loads(_m.group(1).replace("<\\/", "</")) if _m else {}
V = P.get("views") or {}
S_, D_ = V.get("silo") or {}, V.get("drying") or {}
check("the page opens on its organisation, and its lenses are the law's four, each with its form",
      P.get("opens_on") == "grain-coop" and [l["form"] for l in P.get("levels", [])] == ["story", "schematic", "health-chain", "anatomy"],
      (P.get("opens_on"), [l.get("form") for l in P.get("levels", [])]))
check("a being's organisation is read from its genos: grain-coop's own, hill-farm's, and none for tessa's radio",
      (P.get("beans") or {}).get("silo-controller", {}).get("org") == "grain-coop"
      and P["beans"]["hill-pump"]["org"] == "hill-farm" and P["beans"]["field-radio"]["org"] is None
      and P["beans"]["grain-coop"]["org"] == "grain-coop", {b: v.get("org") for b, v in (P.get("beans") or {}).items()})
check("...and a being owned `via` another is that other's: the monitor, via the silo controller, is grain-coop's",
      P["beans"]["yard-monitor"]["org"] == "grain-coop", P["beans"].get("yard-monitor"))
_ad = [x["address"] for x in (P.get("addresses") or {}).get("silo-controller", [])]
check("addresses: the one the page chooses first, then the being's own positions — from its record, never restated",
      _ad[:1] == ["192.0.2.40"] and (P["addresses"]["silo-controller"][0]["what"] or [None])[0] == "stands for it on this page", _ad)
check("the reference row shows the address the page chooses, stated by the being", [(r["being"], r["address"]) for r in P.get("reference", [])][:2]
      == [("silo-controller", "192.0.2.40"), ("dryer-controller", "192.0.2.41")], P.get("reference"))
check("no drawing carries an address: the kit never draws the one a node is given",
      not re.search(r"\b192\.0\.2\.\d+\b", S_.get("svg", "") + D_.get("svg", "")), "")
check("orient: the story resolves stage by stage, each technology to its own documentation",
      [s["label"] for s in (S_.get("story") or {}).get("stages", [])] == ["Read the fill", "Warn before full", "Send loads elsewhere"]
      and S_["story"]["stages"][0]["tech"][0].get("docs", "").startswith("https://prometheus.io"), S_.get("story"))
check("orient: the fields of knowledge the technologies stand in are read from the scheme the catalogue hangs from",
      [(f["scheme"], f["code"]) for f in S_["story"].get("fields", [])] == [("isced-f-2013", "0612")], S_["story"].get("fields"))
_b = {b["id"]: b for b in S_.get("binds", [])}
check("units are the law's: a percent is a ratio of 1/100, a day a duration of 86400, a temperature a bare number (°C in its label)",
      (_b.get("silo-fill") or {}).get("q") == "ratio" and _b["silo-fill"]["f"] == [1, 100]
      and _b["silo-full-in"]["q"] == "duration" and _b["silo-full-in"]["f"] == [86400, 1]
      and _b["grain-temperature"]["unit"] == "" and "°C" in _b["grain-temperature"]["name"], _b.get("silo-fill"))
check("...and the page hands the runtime each binding's limits as numbers, and the query that is its path",
      _b["silo-fill"]["warn"] == 80.0 and _b["silo-fill"]["crit"] == 90.0 and "silo_fill_ratio{$F}" in _b["silo-fill"]["source"]
      and _b["silo-up"]["source"].startswith('min(probe_success{name="silo-controller"'), _b.get("silo-up"))
_op = S_.get("operate") or {}
check("reservoir: the fill, its thresholds as percents of the whole, the forecast and the parts",
      _op.get("archetype") == "reservoir" and _op.get("fill") == "silo-fill" and [x["at"] for x in _op.get("thresholds", [])] == [90.0, 98.0]
      and _op.get("forecast") == "silo-full-in" and _op.get("parts") == ["silo-up", "grain-temperature"], _op)
check("correlate: a span of 12 hours at a point every 5 minutes, read as the drawing's history window",
      S_.get("window") == {"hours": 12.0, "step": 300} and _op["correlate"][0]["rows"] == ["silo-fill", "grain-temperature"], S_.get("window"))
_dp = D_.get("operate") or {}
check("race: the steps are the drawn procedure's own, the deadline 7 hours in seconds, the checkpoint 3 hours",
      _dp.get("archetype") == "race" and len(_dp.get("steps", [])) == 4 and _dp["steps"][0].startswith("the yard crew loads")
      and _dp.get("deadline") == 25200.0 and _dp.get("checkpoints") == [{"at": 10800.0, "label": "heating should be done"}]
      and _dp.get("step_at") == "drying-step" and _dp.get("elapsed") == "drying-elapsed" and _dp.get("eta") == "drying-left", _dp)
_dc = (_dp.get("correlate") or [{}])[0]
check("correlate on a race: the band's labels are the procedure's steps after 'not running', and relate at a step",
      _dc.get("band") == "drying-step" and _dc.get("bands", [])[0] == "not running" and len(_dc["bands"]) == 5
      and _dc.get("relate") == {"across": "grain-temperature", "measure": "drying-left", "bins": 4, "at_step": 2, "keep": "positive"}, _dc)
check("...and a value a shape reads from another drawing is carried beside the drawing's own",
      any(b["id"] == "grain-temperature" and b.get("elsewhere") for b in D_.get("binds", [])), [b["id"] for b in D_.get("binds", [])])
_t = S_.get("tiles", [])
check("operate, the fallback's tiles: a bound part is a tile; a part nothing measures is a BLIND SPOT, shown with why",
      any(x.get("el") == "silo-controller" and not x.get("blind") for x in _t)
      and any(x.get("el") == "trailer" and x.get("blind") and "nothing measures it" in x.get("why", "") for x in _t), _t)
check("operate: the alert rule that watches a metric the drawing reads is named, from the monitor's own settings",
      S_.get("alerts") == ["SiloNearlyFull"] and D_.get("alerts") == [], (S_.get("alerts"), D_.get("alerts")))
_w = S_.get("wiring") or {}
check("inspect: the wiring is read where the page points — pipes and processes of the silo controller, with their channel",
      [x["to"] for x in _w.get("pipes", [])] == ["fill-reader", "exporter"] and _w["pipes"][0]["channel"] == "serial"
      and [x["proc"] for x in _w.get("processes", [])] == ["fan-driver", "fill-reader"], _w)
check("inspect: a card per part, with its genos, organisation, anchors, addresses, provenance and the facts `fields` shows",
      {p["bean"] for p in S_.get("parts", [])} >= {"silo-controller", "field-radio", "hill-pump"}
      and next(p for p in S_["parts"] if p["bean"] == "silo-controller")["rows"][0][0] == "summary"
      and next(p for p in S_["parts"] if p["bean"] == "field-radio")["org"] is None, [(p["bean"], p["org"]) for p in S_.get("parts", [])])
check("inspect: the procedure's steps are bound to the parts they name", any("silo-controller" in s["parts"] for s in D_.get("steps", []))
      and any("dryer-controller" in s["parts"] for s in D_.get("steps", [])), D_.get("steps"))
check("the legend's meanings are the kit's for a drawing pattern and the law's for a kind of live value",
      any(l[0] == "live-state" and "whether the being answers" in l[1] for l in S_.get("legend", []))
      and any(l[0] == "store" and "cylinder" in l[1] for l in S_.get("legend", [])), S_.get("legend"))

# --- the runtime itself, where this machine can run it (a syntax check, and every drawing at every lens in a browser)
import shutil as _sh
_node = _sh.which("node")
if _node:
    r = run(_node, "--check", os.path.join(G, "assets", "view", "lib", "view_runtime.js"))
    check("the runtime parses (node --check)", r.returncode == 0, r.stdout + r.stderr)
else:
    print("NOTE  the runtime's syntax was not checked: no node on this machine")
_browser = next((b for b in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable") if _sh.which(b)), None)
DRIVE = """<script>
window.__errs = []; window.addEventListener('error', e => window.__errs.push(String(e.message)));
window.addEventListener('load', () => { const out = [];
 try { const tabs = [...document.querySelectorAll('.tab')].map(b => b.dataset.t), lens = [...document.querySelectorAll('#lens button')].map(b => b.dataset.l);
  for (const t of tabs) for (const l of lens) { document.querySelector('.tab[data-t="' + t + '"]').click(); document.querySelector('#lens button[data-l="' + l + '"]').click();
   out.push(t + '/' + l + ':' + (document.querySelector('#view').innerText || '').length); }
  document.querySelector('#authbtn').click(); out.push('author:' + (document.querySelector('#author').innerText || '').length);
 } catch (e) { window.__errs.push('driver: ' + e.message); }
 const pre = document.createElement('pre'); pre.id = '__result'; pre.textContent = JSON.stringify({errs: window.__errs, out}); document.body.appendChild(pre); });
</script>"""
if _browser and HTML:
    _dr = os.path.join(T, "drive.html")
    with open(_dr, "w", encoding="utf-8") as fh:
        fh.write(HTML.replace("<head>", "<head>" + DRIVE, 1))
    try:
        r = subprocess.run([_browser, "--headless=new", "--disable-gpu", "--no-sandbox", "--virtual-time-budget=5000",
                            "--dump-dom", "file://" + _dr], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90)
        _mm = re.search(r'<pre id="__result">(.*?)</pre>', r.stdout, re.S)
        import html as _html
        _res = json.loads(_html.unescape(_mm.group(1))) if _mm else {"errs": ["no result: " + (r.stderr or "")[-300:]], "out": []}
    except (OSError, subprocess.SubprocessError) as e:
        _res = {"errs": ["the browser did not run: %s" % e], "out": []}
    check("in a headless browser the runtime draws both drawings at all four lenses, the reference and the author mode, "
          "with no error", not _res["errs"] and len(_res["out"]) == 13 and all(int(x.rsplit(":", 1)[1]) > 40 for x in _res["out"]), _res)
else:
    print("NOTE  the runtime was not driven in a browser: none on this machine")

# --- import: an author-mode selection, written through dmsafe and journalled
SEL = {"order": ["silo", "drying"], "views": P["author"]["views"], "bindings": P["author"]["bindings"],
       "reference": P["author"]["reference"], "fields": P["author"]["fields"]}
_sp = os.path.join(T, "sel.json")
json.dump(SEL, open(_sp, "w", encoding="utf-8"))
_j0 = get("log/journal.md")
_h_imp = run("git", "rev-parse", "HEAD", cwd=G).stdout.strip()     # an import commits: each probe is undone to here
out, rc = dmview("import", _sp)
check("import: a selection that says what the page says writes nothing, and journals nothing",
      rc == 0 and "nothing to write" in out and get("beans/grain-page.md") == PAGE_T and get("log/journal.md") == _j0, out[-500:])
SEL2 = json.loads(json.dumps(SEL))
SEL2["order"] = ["drying", "silo"]
SEL2["views"]["silo"]["stages"][1]["label"] = "yes"
SEL2["views"]["silo"]["label"] = "The silo, filling"
SEL2["bindings"]["silo-load"] = {"view": "silo", "element": "silo", "live": "live-value", "label": "load", "unit": "percent",
                                 "warn": "70.5", "query": [{"technology": "prometheus", "says": "silo_load{$F}"}]}
json.dump(SEL2, open(_sp, "w", encoding="utf-8"))
out, rc = dmview("import", _sp, "--who", "tessa")
_pg = get("beans/grain-page.md")
_ga = gate()
check("import: a new order, a relabelled drawing, a YAML word as a label and a new binding are written through dmsafe, "
      "read back as intended, journalled naming the page, and pass the gate", rc == 0 and "of: [drying, silo]" in _pg
      and ("label: 'yes'" in _pg or 'label: "yes"' in _pg) and "silo-load:" in _pg and "[[grain-page]]" in get("log/journal.md")[len(_j0):]
      and _ga[1] == 0 and dmview("check")[1] == 0, out[-600:] + _ga[0][-400:])
run("git", "reset", "-q", "--hard", _h_imp, cwd=G)
SEL3 = json.loads(json.dumps(SEL))
SEL3["views"]["silo"]["actions"] = []
json.dump(SEL3, open(_sp, "w", encoding="utf-8"))
out, rc = dmview("import", _sp, "--who", "tessa")
check("import: an emptied list of actions is written as none, and the page still checks",
      rc == 0 and "start-fans" not in get("beans/grain-page.md") and dmview("check")[1] == 0, out[-500:])
run("git", "reset", "-q", "--hard", _h_imp, cwd=G)
SEL4 = json.loads(json.dumps(SEL))
SEL4["views"]["barn"] = {"label": "The barn"}
json.dump(SEL4, open(_sp, "w", encoding="utf-8"))
out, rc = dmview("import", _sp)
check("import: a selection naming a drawing the page does not have is refused, and nothing is written",
      rc != 0 and "barn" in out and get("beans/grain-page.md") == PAGE_T, out[-400:])
run("git", "reset", "-q", "--hard", _h_imp, cwd=G)

# --- the bundle, written by the monitor's adapter
out, rc = dmview("bundle")
check("bundle: --out is required", rc == 2 and "--out" in out, out)
BD = os.path.join(T, "bundle")
out, rc = dmview("bundle", "--out", BD)
_tj = lambda m: json.load(open(os.path.join(BD, "targets", m + ".json"))) if os.path.isfile(os.path.join(BD, "targets", m + ".json")) else []
_http, _tcp, _icmp, _tls = _tj("http"), _tj("tcp"), _tj("icmp"), _tj("tls")
check("bundle: the monitor's reaches become probes of each target's own endpoints — http on 80 and 443, ssh on 22 — and an "
      "address the page chooses for a ping", rc == 0 and sorted(x["targets"][0] for x in _http) == ["http://192.0.2.40:80/", "https://192.0.2.40:443/"]
      and [x["targets"][0] for x in _tcp] == ["192.0.2.41:22"] and sorted(x["targets"][0] for x in _icmp) == ["192.0.2.60", "192.0.2.70"],
      out[-500:] + str((_http, _tcp, _icmp)))
check("bundle: an encrypted http endpoint is a certificate to watch", [x["targets"][0] for x in _tls] == ["https://192.0.2.40:443/"], _tls)
_orgs = {x["labels"]["name"]: x["labels"].get("org") for x in _http + _tcp + _icmp}
check("bundle: each target labelled with its genos and the organisation read from its record — and a being with none carries "
      "no org label", _orgs == {"silo-controller": "grain-coop", "dryer-controller": "grain-coop", "field-radio": None,
                                "hill-pump": "hill-farm"} and all(x["labels"]["genos"] == "host" for x in _http + _tcp + _icmp), _orgs)
_py = open(os.path.join(BD, "prometheus.yml")).read() if os.path.isfile(os.path.join(BD, "prometheus.yml")) else ""
_comp = open(os.path.join(BD, "docker-compose.yml")).read() if os.path.isfile(os.path.join(BD, "docker-compose.yml")) else ""
_rf = open(os.path.join(BD, "textfile", "remote_fs.sh")).read() if os.path.isfile(os.path.join(BD, "textfile", "remote_fs.sh")) else ""
check("bundle: a filesystem read over ssh, from the monitor's settings, is labelled with ITS being, and runs where the "
      "monitor is located", 'name="silo-controller"' in _rf and 'org="grain-coop"' in _rf and "reader@192.0.2.40" in _rf
      and "df -kP /data" in _rf and "/srv/yard-monitor/textfile-out" in _rf and "/srv/yard-monitor/textfile-out:/textfile:ro" in _comp, _rf[:400])
check("bundle: a being reached over SNMP is read once per module set, each with its own organisation",
      "job_name: snmp-hill-pump-if-mib" in _py and "job_name: snmp-hill-pump-ip-mib" in _py
      and re.search(r"snmp-hill-pump-if-mib[\s\S]*?org: 'hill-farm'", _py) and re.search(r"snmp-hill-pump-ip-mib[\s\S]*?org: 'grain-coop'", _py), _py[-900:])
_auth = open(os.path.join(BD, "snmp-entry.sh")).read() if os.path.isfile(os.path.join(BD, "snmp-entry.sh")) else ""
check("bundle: the SNMP secret is only a ${VAR}: the container writes its auth file from the host's env file at start",
      '"${SNMP_YARD_COMMUNITY}"' in _auth and "cat > /tmp/auth.yml" in _auth and "entrypoint: ['/bin/sh', '/etc/snmp_exporter/entry.sh']" in _comp
      and "env_file: [snmp.env]" in _comp, _auth + _comp[-400:])
_envd = tempfile.mkdtemp(dir=T)
open(os.path.join(_envd, "entry.sh"), "w").write(_auth.replace("/tmp/auth.yml", os.path.join(_envd, "auth.yml"))
                                                  .replace("exec /bin/snmp_exporter", "cat %s; true; #" % os.path.join(_envd, "auth.yml")))
_sh1 = subprocess.run(["sh", os.path.join(_envd, "entry.sh")], capture_output=True, text=True, encoding="utf-8", env={"SNMP_YARD_COMMUNITY": "not-a-real-one", "PATH": "/usr/bin:/bin"})
_sh2 = subprocess.run(["sh", os.path.join(_envd, "entry.sh")], capture_output=True, env={"PATH": "/usr/bin:/bin"})
check("bundle: the entry script writes the auth file from the environment, and refuses when the variable is unset",
      'community: "not-a-real-one"' in _sh1.stdout and _sh2.returncode != 0, _sh1.stdout + _sh1.stderr)
import yaml
_rules = open(os.path.join(BD, "rules", "view.yml")).read() if os.path.isfile(os.path.join(BD, "rules", "view.yml")) else ""
_am = open(os.path.join(BD, "alertmanager.yml")).read() if os.path.isfile(os.path.join(BD, "alertmanager.yml")) else ""
check("bundle: the alert rules come from the monitor's settings and parse; the alert mail goes where they say, on no published port",
      "alert: SiloNearlyFull" in _rules and yaml.safe_load(_rules)["groups"][0]["rules"][0]["for"] == "15m"
      and "keeper@example.org" in _am and "9093:9093" not in _comp and "alertmanager:9093" in _py, _rules[:300])
try:
    _pyd = yaml.safe_load(_py)
except Exception as e:
    _pyd = {"error": str(e)}
check("bundle: prometheus.yml and the compose file are valid YAML, the node job honours a textfile value's own labels, and "
      "the compose project is the page's", isinstance(yaml.safe_load(_comp), dict) and isinstance(_pyd.get("scrape_configs"), list)
      and {"node", "blackbox-icmp", "blackbox-http"} <= {j["job_name"] for j in _pyd["scrape_configs"]} and "honor_labels: true" in _py
      and "name: grain-page" in _comp and 'garden: "garden-grain"' in _py, str(_pyd)[:300])
_dash = json.load(open(os.path.join(BD, "grafana", "dashboards", "view-silo.json"))) if os.path.isfile(os.path.join(BD, "grafana", "dashboards", "view-silo.json")) else {}
check("bundle: one page per drawing, the drawing mounted by the same runtime, its queries built with the page's scope variables",
      _dash.get("uid") == "view-silo" and "viewMount" in json.dumps(_dash) and 'org=~\\"$org\\"' in json.dumps(_dash)
      and os.path.isfile(os.path.join(BD, "grafana", "dashboards", "view-index.json")), str(_dash)[:300])

# --- a second adapter, beside the first: another technology the catalogue has, read by the adapter named for it
SIBLING = """TECHNOLOGY = "zabbix"


def describe(b):
    return "zabbix item " + str((b.get("query") or {}).get(TECHNOLOGY) or "")


def check_binding(b):
    return [] if (b.get("query") or {}).get(TECHNOLOGY) or b.get("live") == "live-state" else ["no zabbix item"]


def check_monitor(m):
    return [], []


def selector(scope):
    return "all" if scope is None else ",".join(scope.get("orgs") or [])


def values(url, binds, sel):
    return {b["id"]: 42.0 for b in binds}


def history(url, binds, sel, hours, step, now):
    return {b["id"]: [[now - step, 41.0], [now, 42.0]] for b in binds}


def alerts(settings, beans, binds):
    return []
"""
put("assets/view/lib/sources/zabbix.py", SIBLING)
put("beans/zabbix.md", "---\nbean: zabbix\nkind: product\ntitle: \"Zabbix\"\nsummary: \"A second monitoring system.\"\n"
    "statements:\n  - say: {by: tessa, at: now}\n  - name: {by: anchor-identifier, of: self, as: 'technology:zabbix'}\n"
    "  - own: {by: {someone: org}, of: self, note: its authors}\n  - answer: {by: tessa, of: self, as: law}\n"
    "---\nA second monitor's software.\n")
put("beans/radio-monitor.md", "---\nbean: radio-monitor\nkind: instance\ntitle: \"The radio monitor\"\n"
    "summary: \"Reads the field radio's signal.\"\nstatements:\n  - read: {by: tessa, at: now}\n  - own: {by: tessa, of: self}\n"
    "  - be: {by: self, at: silo-controller, as: habitat}\n  - run: {by: self, of: zabbix}\n"
    "  - use: {by: self, of: 'technology:zabbix'}\n  - need: {id: reaches-radio-agent, by: self, of: [field-radio], through: icmp}\n"
    "---\nThe radio monitor.\n")
put("beans/grain-page.md", PAGE_T.replace("statements:\n", "statements:\n  - say: {by: tessa, of: [silo, page], at: now}\n", 1)
    .replace("monitors: [{monitor: yard-monitor, settings: {bean: yard-monitor, field: monitoring}}]",
                                          "monitors: [{monitor: yard-monitor, settings: {bean: yard-monitor, field: monitoring}}, {monitor: radio-monitor}]", 1)
    .replace("radio-up: {element: field-radio, live: live-state}, ",
             "radio-up: {element: field-radio, live: live-state}, "
             "radio-signal: {element: field-radio, live: live-value, label: radio signal, query: [{technology: zabbix, says: radio.signal}]}, "
             "both-read: {element: silo, live: live-value, label: read twice, query: [{technology: zabbix, says: silo.load}, {technology: prometheus, says: 'silo_load{$F}'}]}, ", 1))
_ga = gate()
out, rc = dmview("check")
_r2 = os.path.join(T, "r2.html")
dmview("report", "--out", _r2)
_m2 = re.search(r'<script type="application/json" id="viewdata">(.*?)</script>', open(_r2, encoding="utf-8").read() if os.path.isfile(_r2) else "", re.S)
_b2 = {b["id"]: b for b in (json.loads(_m2.group(1).replace("<\\/", "</"))["views"]["silo"]["binds"] if _m2 else [])}
check("a second technology is a sibling: its adapter is chosen by the monitor's own record, and a binding in its language is "
      "computed by it, beside the first", _ga[1] == 0 and rc == 0 and (_b2.get("radio-signal") or {}).get("technology") == "zabbix"
      and _b2["radio-signal"]["monitor"] == "radio-monitor" and _b2["radio-signal"]["source"] == "zabbix item radio.signal"
      and _b2["silo-fill"]["technology"] == "prometheus", out[-500:] + _ga[0][-300:])
check("...and a binding in both languages is computed by the first monitor of the page whose technology it gives",
      (_b2.get("both-read") or {}).get("monitor") == "yard-monitor", _b2.get("both-read"))
SIBLING_PAGE = get("beans/grain-page.md")

# --- the served page: signed in, closed by default, and the one function that says who may see and do what
import socket, threading, time, urllib.parse, urllib.request, http.cookiejar
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler


class FakeMonitor(BaseHTTPRequestHandler):
    queries = []

    def log_message(self, *a):
        pass

    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get("query", [""])[0]
        FakeMonitor.queries.append(q)
        if "query_range" in self.path:
            res = [{"metric": {}, "values": [[1000, "1"], [1300, "2"]]}]
        elif "dryer_batches" in q:
            res = [{"metric": {"bay": "a"}, "value": [0, "3"]}, {"metric": {"bay": "b"}, "value": [0, "1"]}]
        else:
            res = [{"metric": {}, "value": [0, "1"]}]
        body = json.dumps({"status": "success", "data": {"resultType": "vector", "result": res}}).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)


def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


_sv = run(sys.executable, os.path.join(G, "bin", "save.py"), "tessa", "RULE-CHANGE: a second monitor, and its adapter",
          "--body", "- action: [[zabbix]], [[radio-monitor]] and [[grain-page]]: the radio read by a second technology; "
          "RULE-CHANGE: assets/view/lib/sources/zabbix.py added, a probe of a sibling adapter.", cwd=G)
check("...and the garden saves it, a RULE-CHANGE: an adapter added beside the release's is a change to the release's files",
      _sv.returncode == 0 and not run("git", "status", "--porcelain", cwd=G).stdout.strip(), (_sv.stdout + _sv.stderr)[-800:])
# THE LEDGER OPENS WHAT A VIEWER SEES (24.0, N33): each viewer is a person the garden holds, under an opaque id, and the
# gardener's grants open the co-operative's beings to them — to read, and to run each tool. The host's configuration
# only narrows what the grants open.
VIEWERS = {"alice": "p-a11ce000", "carol": "p-ca401000", "dave": "p-da4e0000"}
for _p in VIEWERS.values():
    put(f"beans/{_p}.md", f"""---
bean: {_p}
kind: person
title: "{_p}"
summary: "a viewer of the co-operative's page"
statements:
  - say: {{ by: tessa, at: now }}
  - own: {{ by: theone, of: self }}
---
A viewer.
""")
# A GRANT OF THE CORE NAMES WHAT IT OPENS: every being the co-operative keeps, to each viewer, to read and to run its
# tools (`enact`) — today's grant over a reading has no form in the core yet (test/ported.yaml)
_every = sorted(f[:-3] for d in ("beans", "mappings") for f in os.listdir(os.path.join(G, d)) if f.endswith(".md"))
_t = get("beans/tessa.md")
put("beans/tessa.md", _t.replace("\n---\n", "\n  - say: { by: tessa, of: [viewers-read, viewers-act], at: now }\n"
                                 "  - grant: { id: viewers-read, by: tessa, to: [%s], of: [%s], as: read, why: \"the page is the co-operative's to read\" }\n"
                                 "  - grant: { id: viewers-act, by: tessa, to: [%s], of: [%s], as: enact, why: \"a viewer may start the fans, reset the radio and stop the pump\" }\n"
                                 "---\n" % (", ".join(VIEWERS.values()), ", ".join(_every), ", ".join(VIEWERS.values()), ", ".join(_every)), 1))
_sv = run(sys.executable, os.path.join(G, "bin", "save.py"), "tessa", "the page's viewers, and what they are granted",
          "--body", "- action: " + ", ".join(f"[[{_p}]]" for _p in VIEWERS.values()) + " recorded; [[tessa]] grants them "
          "the co-operative's beings to read, and its three tools.", cwd=G)
check("the viewers and the gardener's grants to them are saved through the gate", _sv.returncode == 0,
      (_sv.stdout + _sv.stderr)[-1500:])
CFG = os.path.join(T, "host", "serve.json")
_pp = free_port()
mon = ThreadingHTTPServer(("127.0.0.1", _pp), FakeMonitor)
threading.Thread(target=mon.serve_forever, daemon=True).start()
for _u, _o in (("alice", ["--orgs", "grain-coop", "--bean", VIEWERS["alice"]]), ("carol", ["--orgs", "grain-coop", "--shared", "--bean", VIEWERS["carol"]]),
               ("dave", ["--orgs", "hill-farm", "--no-actions", "--bean", VIEWERS["dave"]]), ("root", ["--orgs", "*", "--bean", "tessa"])):
    out, rc = dmview("serve-init", "--config", CFG, "--user", _u, *_o)
check("serve-init: the password is written to a file of its own and never printed",
      rc == 0 and "password is in" in out and open(os.path.join(T, "host", "root.password")).read().strip() not in out, out)
C = json.load(open(CFG))
check("serve-init: the configuration and every password file are 0600, and no viewer is granted what no organisation owns "
      "unless said", oct(os.stat(CFG).st_mode & 0o777) == "0o600" and oct(os.stat(os.path.join(T, "host", "alice.password")).st_mode & 0o777) == "0o600"
      and C["users"]["alice"]["shared"] is False and C["users"]["carol"]["shared"] is True, C["users"].get("alice"))
check("serve-init: a viewer's own bean is recorded as `bean`, for the law's grants to be asked about that person",
      C["users"]["root"].get("bean") == "tessa" and C["users"]["alice"].get("bean") == VIEWERS["alice"], C["users"].get("root"))
_out, _rc = dmview("serve-init", "--config", os.path.join(T, "host", "nobody.json"), "--user", "eve", "--bean", "no-such-person")
check("...and a bean the garden does not hold is refused, and nothing is written",
      _rc != 0 and "no-such-person" in _out and not os.path.exists(os.path.join(T, "host", "nobody.json")), _out)
_sp_ = free_port()
C["listen"] = "127.0.0.1:%d" % _sp_
C["recheck_seconds"] = 1
C["monitors"] = {"yard-monitor": {"url": "http://127.0.0.1:%d" % _pp}, "radio-monitor": {"url": "http://127.0.0.1:1"}}
C["users"]["dave"]["beans"] = ["field-radio"]
C["tools"] = {"start-fans": {"argv": [sys.executable, "-c", "print('ran-for-real')"], "enabled": True, "timeout": 20},
              "radio-reset": {"argv": ["/bin/false"], "enabled": False}, "pump-stop": {"argv": ["/bin/false"], "enabled": False}}
json.dump(C, open(CFG, "w"))

# THE ONE FUNCTION, asked directly: may this viewer see this bean, or run this action.
sys.path.insert(0, os.path.join(G, "assets", "view", "lib"))
import view_model as _vm
_vm.init(G)
import view_serve as _vs
_H = _vs.Host(CFG)
_may = {(u, b): _H.may(u, b)[0] for u in ("alice", "carol", "dave", "root") for b in ("silo-controller", "yard-monitor", "field-radio", "hill-pump")}
check("Host.may, the one function: a scoped viewer sees what their organisations own, a being none can be derived for only "
      "through a grant (`shared`, or by name), another organisation's never; `*` sees all",
      _may == {("alice", "silo-controller"): True, ("alice", "yard-monitor"): True, ("alice", "field-radio"): False, ("alice", "hill-pump"): False,
               ("carol", "silo-controller"): True, ("carol", "yard-monitor"): True, ("carol", "field-radio"): True, ("carol", "hill-pump"): False,
               ("dave", "silo-controller"): False, ("dave", "yard-monitor"): False, ("dave", "field-radio"): True, ("dave", "hill-pump"): True,
               ("root", "silo-controller"): True, ("root", "yard-monitor"): True, ("root", "field-radio"): True, ("root", "hill-pump"): True},
      {k: v for k, v in _may.items()})
check("...and it says why, and refuses to act for a viewer who may view but not act",
      "no grant" in _H.may("alice", "field-radio")[1] and _H.may("dave", "hill-pump", act=True) == (False, "this viewer may view but not act"),
      (_H.may("alice", "field-radio"), _H.may("dave", "hill-pump", act=True)))

srv = subprocess.Popen([sys.executable, DMVIEW, "serve", "--config", CFG], cwd=G, stderr=subprocess.PIPE, text=True, encoding="utf-8")
BASE = "http://127.0.0.1:%d" % _sp_
for _ in range(80):
    try:
        urllib.request.urlopen(BASE + "/healthz", timeout=1); break
    except Exception:
        time.sleep(0.2)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def session(user):
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar), NoRedirect)
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


def post_(op, path, obj, csrf=None):
    req = urllib.request.Request(BASE + path, json.dumps(obj).encode(),
                                 {"Content-Type": "application/json", **({"X-View-CSRF": csrf} if csrf else {})})
    try:
        r = op.open(req); return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def page_of(op):
    st, pg = get_(op, "/")
    m = re.search(r'<script type="application/json" id="viewdata">(.*?)</script>', pg, re.S)
    return st, (json.loads(m.group(1).replace("<\\/", "</")) if m else {})


try:
    anon = urllib.request.build_opener(NoRedirect)
    st, _ = get_(anon, "/")
    check("serve: an anonymous visitor is sent to sign in", st in (302, 303), st)
    st, _ = get_(anon, "/api/values?m=silo")
    check("serve: the API refuses an anonymous visitor", st == 401, st)
    try:
        anon.open(BASE + "/login", urllib.parse.urlencode({"user": "alice", "password": "wrong"}).encode()); st = 200
    except urllib.error.HTTPError as e:
        st = e.code
    check("serve: a wrong password is refused", st == 401, st)
    alice = session("alice")
    st, PA = page_of(alice)
    check("serve: alice sees the served page, and the author mode is not sent to it", st == 200 and PA.get("live", {}).get("user") == "alice"
          and "author" not in PA, st)
    _ref = [r["being"] for r in PA.get("reference", [])]
    check("serve: CLOSED BY DEFAULT — alice (grain-coop) is sent grain-coop's parts, and neither tessa's radio (no organisation, "
          "no grant) nor the hill farm's pump", _ref == ["silo-controller", "dryer-controller"] and "field-radio" not in PA["beans"]
          and "hill-pump" not in PA["beans"] and "field-radio" not in PA.get("addresses", {}), (_ref, sorted(PA.get("beans", {}))))
    _sv = PA["views"]["silo"]
    check("serve: ...nor their part cards, their facts or their tiles, on any drawing",
          {p["bean"] for p in _sv["parts"]} == {"silo-controller"} and set(_sv["facts"]) == {"silo-controller"}
          and not any(t.get("bean") in ("field-radio", "hill-pump") for t in _sv["tiles"]), [p["bean"] for p in _sv["parts"]])
    carol = session("carol")
    st, PC = page_of(carol)
    check("serve: carol, granted what no organisation owns, sees the radio — and still not the hill farm's pump",
          "field-radio" in PC["beans"] and "hill-pump" not in PC["beans"], sorted(PC.get("beans", {})))
    dave = session("dave")
    st, PD = page_of(dave)
    check("serve: dave (hill-farm, and the radio by name) sees the pump and the radio, and is not sent the silo's drawing, which "
          "draws what grain-coop owns; the drying run, which draws a procedure, is sent",
          "hill-pump" in PD["beans"] and "field-radio" in PD["beans"] and "silo-controller" not in PD["beans"]
          and "silo" not in PD["views"] and "drying" in PD["views"] and PD["order"] == ["drying"], (sorted(PD.get("beans", {})), sorted(PD.get("views", {}))))
    FakeMonitor.queries.clear()
    st, vals = get_(alice, "/api/values?m=silo")
    VA = json.loads(vals).get("values", {}) if st == 200 else {}
    check("serve: values are read — a live-state, a value — from the monitor the host names", st == 200 and VA.get("silo-up") == 1.0
          and VA.get("silo-fill") == 1.0, vals[:300])
    check("serve: a being alice may not see is not asked about: its live-state is empty, and no query names it",
          VA.get("radio-up") is None and VA.get("pump-up") is None and not any("field-radio" in q or "hill-pump" in q for q in FakeMonitor.queries),
          FakeMonitor.queries)
    check("serve: every query built on the server carries alice's scope — her organisation only, nothing unowned",
          FakeMonitor.queries and all('org=~"(grain-coop)"' in q for q in FakeMonitor.queries if "$" not in q and "probe_success" not in q),
          FakeMonitor.queries)
    FakeMonitor.queries.clear()
    get_(carol, "/api/values?m=silo")
    check("serve: carol's queries carry her grant: her organisation, and the series of beings no organisation owns",
          any('org=~"(grain-coop|)"' in q for q in FakeMonitor.queries), FakeMonitor.queries)
    check("serve: the value of the second technology comes from its own adapter", VA.get("radio-signal") is None
          and json.loads(get_(carol, "/api/values?m=silo")[1])["values"].get("radio-signal") == 42.0, VA)
    st, vd = get_(alice, "/api/values?m=drying")
    check("serve: a live-series comes back as a named list, each item by the label its query names",
          st == 200 and json.loads(vd)["values"].get("drying-batches") == [{"name": "a", "value": 3.0}, {"name": "b", "value": 1.0}], vd[:300])
    st, hv = get_(alice, "/api/history?m=drying")
    check("serve: the history is read over the drawing's window, scoped like the values",
          st == 200 and json.loads(hv)["history"].get("grain-temperature") == [[1000, 1.0], [1300, 2.0]], hv[:300])
    st, _ = get_(dave, "/api/values?m=silo")
    check("serve: dave may not ask for the values of a drawing he is not sent", st == 404, st)
    csrf = PA["live"]["csrf"]
    st, j = post_(alice, "/api/action", {"m": "silo", "el": "start-fans"})
    check("serve: an action without the CSRF token is refused", st == 403, (st, j))
    st, j = post_(alice, "/api/action", {"m": "silo", "el": "start-fans"}, csrf)
    check("serve: an enabled tool runs (an argv, never a shell) and returns its output",
          st == 200 and j.get("mode") == "run" and "ran-for-real" in j.get("output", ""), (st, j))
    st, j = post_(alice, "/api/action", {"m": "silo", "el": "radio-reset"}, csrf)
    check("serve: CLOSED BY DEFAULT — an action on the radio, which no organisation owns, is refused to alice, and says why",
          st == 403 and "nothing no organisation owns" in j.get("error", ""), (st, j))
    st, j = post_(carol, "/api/action", {"m": "silo", "el": "radio-reset"}, PC["live"]["csrf"])
    check("serve: ...and runs for carol, granted it — as a DRY RUN, since the host has not enabled the tool",
          st == 200 and j.get("mode") == "dry-run" and "/bin/false" in j.get("message", ""), (st, j))
    st, j = post_(alice, "/api/action", {"m": "silo", "el": "pump-stop"}, csrf)
    check("serve: an action on another organisation's pump is refused", st == 403 and "hill-farm" in j.get("error", ""), (st, j))
    st, j = post_(alice, "/api/action", {"m": "silo", "el": "silo"}, csrf)
    check("serve: an element with no action declared on it is refused", st == 404, (st, j))
    st, j = post_(dave, "/api/action", {"m": "drying", "el": "dryer"}, PD["live"]["csrf"])
    st2, j2 = post_(dave, "/api/action", {"m": "silo", "el": "pump-stop"}, PD["live"]["csrf"])
    check("serve: a viewer who may not act is refused, and a drawing he is not sent has no actions for him", st == 404 and st2 == 404, (st, j, st2, j2))
    _log = [json.loads(l) for l in open(C["audit_log"])] if os.path.isfile(C["audit_log"]) else []
    _modes = [(e["user"], e["mode"]) for e in _log]
    check("serve: every attempt is audited, with the head of the ledger it was judged at",
          ("alice", "run") in _modes and ("carol", "dry-run") in _modes and ("alice", "refused") in _modes
          and all(e.get("head") for e in _log), _modes)
    check("serve: the audit log is 0600", oct(os.stat(C["audit_log"]).st_mode & 0o777) == "0o600")
    # A NEW RELEASE THAT CHECKS STARTS THE SERVER AGAIN ON IT: the release GARDEN.md records moves, and the server reloads.
    _rel0 = urllib.request.urlopen(BASE + "/healthz", timeout=3).headers.get("X-View-Release")
    _gm = get("GARDEN.md")
    put("GARDEN.md", _gm.replace('daftar_release: "%s"' % TAG, 'daftar_release: "v9.9.10"', 1))
    _rs = run(sys.executable, os.path.join(G, "bin", "save.py"), "tessa", "RULE-CHANGE: the release recorded moves",
              "--body", "- action: RULE-CHANGE: GARDEN.md records v9.9.10, a probe of the server's reload.", cwd=G)
    _rel1 = None
    for _ in range(40):
        time.sleep(0.5)
        try:
            _rel1 = urllib.request.urlopen(BASE + "/healthz", timeout=3).headers.get("X-View-Release")
        except Exception:
            _rel1 = None
        if _rel1 == "v9.9.10":
            break
    check("serve: a new release the garden records, which checks, starts the server again on it", _rs.returncode == 0
          and _rel0 == TAG and _rel1 == "v9.9.10", (_rel0, _rel1, (_rs.stdout + _rs.stderr)[-400:]))
finally:
    srv.terminate()
    mon.shutdown()
restore()

# ------------------------------------------------------------------ a private page: its drawings carry addresses
# The page says who reads it (`view.visibility`). Public, the default, is a page that may be published: no drawing shows
# an address, as every check above has held. Private is a page only its host's signed-in viewers read, a network map
# among them: each part shows its own address beside it, sent only to a viewer who may see that being, and a drawing's
# own text may carry one.
_page, _draw = get("beans/grain-page.md"), get("bin/drawings.py")
put("beans/grain-page.md", _page.replace("opens_on: grain-coop, ", "opens_on: grain-coop, visibility: secret, ", 1))
out, rc = gate()
check("the law: a page's visibility is public or private, and nothing else", rc != 0 and said(out, None, "visibility", "secret"),
      out[-600:])
put("beans/grain-page.md", _page.replace("opens_on: grain-coop, ", "opens_on: grain-coop, visibility: private, ", 1))
_d2 = (_draw.replace("from view_kit import", "from view_model import ip\nfrom view_kit import", 1)
       .replace('node(600, 60, 170, 48, "Silo controller", "reads the fill", bean="silo-controller")',
                'node(600, 60, 170, 52, "Silo controller", "reads 192.0.2.99", ip("silo-controller"), bean="silo-controller")', 1)
       .replace('node(400, 160, 170, 48, "Hill pump", "the hill farm\'s", bean="hill-pump")',
                'node(400, 160, 170, 48, "Hill pump", "the hill farm\'s", ip("hill-pump"), bean="hill-pump")', 1)
       .replace('node(600, 160, 170, 48, "Field radio", "carries the readings", bean="field-radio")',
                'node(600, 160, 90, 40, "Field radio", "carries the readings", ip("field-radio"), bean="field-radio")', 1))
check("(the drawing module now hands three parts their address, and writes one address in a role line)",
      _d2.count(', ip("') == 3 and "192.0.2.99" in _d2, "")
put("bin/drawings.py", _d2)
out, rc = gate()
_vout, _vrc = dmview("check")
check("a private page passes the gate and the asset, though a drawing's own text shows an address (192.0.2.99)",
      rc == 0 and _vrc == 0 and "192.0.2.99" not in _vout, out[-300:] + " | " + _vout[-700:])
check("...and an address that fits nowhere in its box is named, never dropped in silence: the card has it",
      "field-radio's address" in _vout and "fits nowhere" in _vout, _vout[-700:])
REPORT2 = os.path.join(T, "report-private.html")
out, rc = dmview("report", "--out", REPORT2)
H2 = open(REPORT2, encoding="utf-8").read() if os.path.isfile(REPORT2) else ""
_m2 = re.search(r'<script type="application/json" id="viewdata">(.*?)</script>', H2, re.S)
P2 = json.loads(_m2.group(1).replace("<\\/", "</")) if _m2 else {}
_svg = ((P2.get("views") or {}).get("silo") or {}).get("svg", "")
_a = lambda b: ((P2.get("addresses") or {}).get(b) or [{}])[0].get("address")
check("a private page's drawing shows each part's own address, the one its reference chooses, marked with the being: "
      "the pump's beside its name, the silo controller's on a line of its own, and nothing hides it at the understand lens",
      rc == 0 and _a("silo-controller") and _a("hill-pump")
      and 'data-addr-of="silo-controller">%s<' % _a("silo-controller") in _svg
      and 'data-addr-of="hill-pump">%s<' % _a("hill-pump") in _svg and ".lv-schematic .nip{display:none}" not in H2,
      (_a("silo-controller"), _a("hill-pump"), _svg[:400]))
check("...and the elements the runtime is handed carry no address: an address that did not fit stays with the check",
      not any("unfit_address" in e for v in (P2.get("views") or {}).values() for e in v.get("elements", [])), "")
_H2 = _vs.Host(CFG)
_H2.refresh(force=True, reexec=False)
_sv = lambda u: ((_H2.scoped_payload(u).get("views") or {}).get("silo") or {}).get("svg", "")
check("the host sends a part's address only to a viewer who may see that being: alice (grain-coop) is sent the silo "
      "controller's and not the hill farm's pump's, `*` both, and the drawing's own text reaches each of them",
      'data-addr-of="silo-controller">%s<' % _a("silo-controller") in _sv("alice") and 'data-addr-of="hill-pump"' not in _sv("alice")
      and 'data-addr-of="hill-pump">%s<' % _a("hill-pump") in _sv("root") and "192.0.2.99" in _sv("alice") + _sv("root"),
      _sv("alice")[:400])
restore()
# THE OPT-IN ACT (upgrade --extend and --retract, germinate --profile) AND THE COOKBOOK'S PAGE are test/core_view.py's
# in a garden of the core.

# --- the engraver: a drawing laid out from the facts it draws — the silo's drying run as parts and pipes, invented
sys.path.insert(0, os.path.join(ROOT, "assets", "view", "lib"))
import view_kit as _vk, view_engrave as _ve
_parts = [
    {"proc": "intake", "rail": "the run", "role": "takes the grain in", "user": "silo"},
    {"proc": "dryer", "rail": "the run", "role": "dries it to 14 %", "user": "silo"},
    {"proc": "moisture probe", "rail": "the run", "role": "reads the grain's moisture", "user": "probe"},
    {"proc": "bin", "rail": "the run", "role": "holds the dried grain", "user": "silo"},
    {"proc": "scheduler", "rail": "control", "role": "starts the dryer at night", "user": "coop"},
    {"proc": "old fan", "rail": "the run", "role": "retired", "user": "silo", "state": "retired"}]
_pipes = [
    {"from": "truck", "to": "intake", "channel": "grain", "rail": "the run"},
    {"from": "intake", "to": "dryer", "channel": "grain", "rail": "the run"},
    {"from": "dryer", "to": "moisture probe", "channel": "reading", "rail": "the run"},
    {"from": "dryer", "to": "bin", "channel": "grain", "rail": "the run"},
    {"from": "bin", "to": "log", "channel": "file", "rail": "the run"},
    {"from": "scheduler", "to": "dryer", "channel": "start", "rail": "control"},
    {"from": "old fan", "to": "dryer", "channel": "air", "rail": "the run", "state": "retired"},
    {"from": "intake :2", "to": "dryer", "channel": "grain", "rail": "the run"},
    {"from": "dryer", "to": "cooler", "channel": "grain", "rail": "the run"}]
_kw = dict(key="proc", rail="rail", of_bean="silo", parts_field="processes", pipes_field="pipes", sub="role",
           carries=lambda e: e.get("channel") == "grain")
def _eng(**kw):
    out = {}
    def fn():
        svg, out["rep"] = _ve.engrave(_parts, _pipes, aria="the drying run", **_kw, **kw)
        return ("run", svg, "", "")
    _t, svg, _c, _cl, els = _vk.compose(fn)
    return svg, {e["id"]: e for e in els}, out["rep"]
_s1, _e1, _r1 = _eng()
_s2, _e2, _r2 = _eng()
check("engrave: the same facts give the same drawing, byte for byte", _s1 == _s2 and _e1 == _e2)
check("engrave: a part's element is its fact — its id the fact's key, and `of` names the bean, the field and the key",
      _e1.get("dryer", {}).get("of") == {"bean": "silo", "field": "processes", "key": "dryer"}
      and _e1.get("moisture-probe", {}).get("of", {}).get("key") == "moisture probe", sorted(_e1)[:12])
check("engrave: an end no part states is drawn and listed, never guessed or dropped — outside where nothing feeds it, a "
      "store where it is given only files",
      _r1["implied"] == ["truck", "log", "intake :2", "cooler"] and _e1["truck"]["mods"] == ["external"]
      and _e1["intake-2"]["mods"] == ["external"] and _e1["log"]["pattern"] == "store"
      and _e1["cooler"]["mods"] == ["implied"], (_r1, _e1.get("truck"), _e1.get("log"), _e1.get("cooler")))
check("engrave: a part only called stands in its caller's column, in the lane above the work's path",
      _e1["moisture-probe"]["box"][0] == _e1["dryer"]["box"][0] and _e1["moisture-probe"]["box"][1] < _e1["dryer"]["box"][1],
      (_e1["moisture-probe"]["box"], _e1["dryer"]["box"]))
check("engrave: the work's path runs left to right, and a retired part is drawn disabled",
      _e1["truck"]["box"][0] < _e1["intake"]["box"][0] < _e1["dryer"]["box"][0] < _e1["bin"]["box"][0]
      and _e1["old-fan"]["mods"] == ["disabled"], {k: _e1[k]["box"] for k in ("truck", "intake", "dryer", "bin")})
check("engrave: a column is as wide as its longest name — a name is never cut",
      _e1["moisture-probe"]["box"][2] >= 24 + 6.8 * len("moisture probe") - 1 and _e1["dryer"]["box"][2] == _e1["moisture-probe"]["box"][2]
      and _e1["intake"]["box"][2] == _ve.W_NODE, {k: _e1[k]["box"] for k in ("intake", "dryer", "moisture-probe")})
def _chain():                                     # a line that skips a column runs clear of the part standing in its way
    def fn():
        svg, _r = _ve.engrave([{"p": "page", "r": "a"}, {"p": "the served page at a long address", "r": "b"},
                               {"p": "server", "r": "b"}, {"p": "machine", "r": "b"}, {"p": "a kept copy", "r": "c"}],
                              [{"from": "page", "to": "the served page at a long address", "r": "b"},
                               {"from": "page", "to": "a kept copy", "r": "c"},
                               {"from": "the served page at a long address", "to": "server", "r": "b"},
                               {"from": "server", "to": "machine", "r": "b"}, {"from": "a kept copy", "to": "machine", "r": "c"}],
                              key="p", rail="r", of_bean="x", parts_field="f", pipes_field="f")
        return ("c", svg, "", "")
    _t, svg, _c, _cl, els = _vk.compose(fn)
    return svg, {e["id"]: e for e in els}
_svc, _ec = _chain()
_kid = next(k for k, e in _ec.items() if (e.get("of") or {}).get("key") == "a kept copy→machine")
_pts = re.search(r'data-el="%s"[^>]*>\s*<polyline points="([^"]+)"' % re.escape(_kid), _svc)
_turn = float(_pts.group(1).split()[1].split(",")[0]) if _pts else -1
_sv = _ec["server"]["box"]
check("engrave: a line that skips a column turns beside its target, clear of the part standing in its way",
      _sv[0] + _sv[2] < _turn < _ec["machine"]["box"][0], (_turn, _sv, _ec["machine"]["box"], _kid))
_s3, _e3, _r3 = _eng(group=lambda p: p["user"])
check("engrave: a division draws the wholes — the silo's three parts one element that holds them, and an implied "
      "listener named after a part joins its whole",
      _e3.get("silo", {}).get("of", {}).get("holds") == ["intake", "dryer", "bin", "old fan", "intake :2"]
      and "intake-2" not in _e3, (_e3.get("silo"), sorted(_e3)))

check("NOTHING above ended in a traceback: every case is a refusal or a pass", not TRACES, TRACES[:2])
shutil.rmtree(T, ignore_errors=True)
print("\nview: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
