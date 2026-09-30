#!/usr/bin/env python3
"""Sequence (std-vocab `series`, `courses`, `moves`, `items`): what a line held at each position, and where a case stands
on a walk.

Grows a garden with seed/germinate.py and writes into it INVENTED fixtures that use every term this adds — a water
heater on a bench logged each minute (flow, water drawn, outlet temperature as a position, power as a state), a moth's
night read against the rooted beings it rested on, a birch's dendrometer and its rings along the radius it lends, a
rock core's strata along its depth, a tree's year as a walk that takes and gives, a literary agent placing a
manuscript (a walk with a way out, a pause that resumes and a final end, a case with a course and its moves) and the
checklist of a manuscript's parts. Nothing here is a person's health or anyone's estate. Then it holds:

  +  the fixtures commit through the hook with 0 errors, the moves one save at a time, each moment stamped by the save
  +  bin/dmseq.py reads them: positions written in the line's own form, a value between rows on a straight line and
     printed to its uncertainty's digits, a state held, a region's value said as what it is, a gap with its reason, a
     cell set aside with its judge, nothing extrapolated — and where a course stands, since when, and who acts next
  +  bin/dmparse.py's table writer writes back what its reader read, byte for byte, and the merge and the proposals
     write a table as a block, where PyYAML alone writes one escaped line
  +  a merge compares every {count, unit} by exact conversion, a series' cells included: a length in millimetres and
     the same in metres are one value, and what is written is each side's own spelling
  -  and every bad write is refused BY NAME: an undeclared step key, a step's reasons that are no list, a pause with a
     way on, a series with a grid and a span, a channel holding two kinds, a mean at a point, a line between codes, an
     empty cell, a header that misses a channel, a cell that is no count, a bare `<` with no limit, a monotone channel
     going back, an exclusion at no row, a stride that is not whole, a unit that does not measure the line, a row past
     the span, a part no series claims, a part rewritten, a held series that says more than where, a move to no step,
     a move the walk does not offer, a move after a final end, a pause not returned from, a reason the step does not
     list, a moment going back, a moment typed rather than stamped, and a checklist naming a bean that is not here.

Run: python3 test/sequence.py   (0 = green)
"""
import os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS, PASSED = [], []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-900:]))
    (PASSED if cond else FAILS).append(name)


def run(*a, cwd):
    return subprocess.run(list(a), capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd,
                          env=dict(os.environ, PYTHONIOENCODING="utf-8"))


T = tempfile.mkdtemp(prefix="dmseq-")
G = os.path.join(T, "g")
r = run(sys.executable, os.path.join(ROOT, "seed", "germinate.py"), G, "--gardener", "keeper", cwd=ROOT)
check("a garden germinates from this release", r.returncode == 0, r.stdout + r.stderr)
run("git", "config", "user.name", "keeper (test)", cwd=G)
run("git", "config", "user.email", "keeper@example.org", cwd=G)
PY = sys.executable


def gate():
    r = run(PY, "bin/dmcheck.py", "--all", cwd=G)
    return r.returncode, r.stdout + r.stderr


def write(rel, text, newline="\n"):
    p = os.path.join(G, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline=newline) as fh:
        fh.write(text)


def read(rel):
    return open(os.path.join(G, *rel.split("/")), encoding="utf-8").read()


def save(what, names, rule_change=False):
    """Journal (the heading and every `now` read from the clock), stage everything, commit through the hook."""
    body = "- action: " + ("RULE-CHANGE (VOCAB.md) " if rule_change else "") + " ".join(f"[[{n}]]" for n in names)
    run(PY, "bin/dmjournal.py", "keeper (test)", what, "--body", body, cwd=G)
    run("git", "add", "-A", cwd=G)
    r = run("git", "commit", "-qm", what, cwd=G)
    return r.returncode, r.stdout + r.stderr


def restore():
    run("git", "reset", "-q", "--hard", cwd=G)
    run("git", "clean", "-qfd", cwd=G)


# ============================================================================ the fixtures, invented
T_ = "\t"
HEAD = ('---\nbean: {id}\ngenos: {genos}\ntitle: "{title}"\nstatus: active\nsummary: "{summary}"\nnature: {nature}\n'
        'identity:\n  status: confirmed\n  anchors:\n    - {{ key: {akey}, value: "{aval}", class: {acls}, establishing: true }}\n'
        'provenance: {{ src: observed, by: "keeper", as_of: now }}\n')
OWN = "owned_by: { legal: { owner: { bean: keeper } } }\nresponsibility: { legal: { holder: { bean: keeper } } }\n"


def bean(id, genos, nature, title, summary, akey, aval, acls, rest, body, own=OWN):
    return HEAD.format(id=id, genos=genos, nature=nature, title=title, summary=summary, akey=akey, aval=aval,
                       acls=acls) + own + rest + "---\n" + body + "\n"


def table(*lines, indent=6):
    return "".join(" " * indent + T_.join(l) + "\n" for l in lines)


HEATER_ROWS = (("flow", "drawn", "outlet", "heating"), ("0", "0", "14.0", "100"), ("4.2", "4.1", "18.5", "100"),
               ("6.0", "6.05", "31.25", "<"), ("5.8", "?", "44.0", "80"), ("-", "5.9", "#", "80"),
               ("<0.1", "0", "52.5", "0"))
HEATER = bean("heater-rig", "host", "soma", "heater-rig — a water heater on the test bench",
              "An invented bench rig: a small water heater whose flow, draw, outlet temperature and power are logged each minute.",
              "serial", "WH-BENCH-0003", "hardware", """series:
  run-3:
    grid: { of: time, in: gregorian-civil, every: { count: 1, unit: minute }, from: "2026-03-02 09:00+01:00" }
    unit: minute
    placement: following
    holds:
      - { name: flow, quantity: volume-flow, unit: litre-per-minute, stands_for: point, between: linear, u: { count: "0.05", unit: litre-per-minute }, persists: offset }
      - { name: drawn, quantity: volume, unit: litre, stands_for: sum }
      - { name: outlet, system: water-celsius, prefix: "C:", stands_for: point }
      - { name: heating, quantity: ratio, unit: percent, stands_for: state, limits: { below: "5" }, accuracy: { count: "2", unit: percent, kind: bound } }
    rows: |
""" + table(*HEATER_ROWS) + """    excluded:
      - { at: 3, channel: flow, by: keeper, why: "air in the flow sensor after the tank was refilled" }
""", "A water heater kept on a bench for trials; nothing here is anyone's health or home.")
MOTH = bean("moth-7", "organism", "soma", "moth-7 — a tagged moth", "An invented moth carrying a light tag for one night.",
            "organism_id", "organism:moth-7", "logical", """series:
  night-1:
    span: { of: time, from: "2026-06-12 21:00+02:00" }
    unit: second
    holds:
      - { name: fix, system: geographic, prefix: "EPSG:4326;", stands_for: point }
      - { name: perch, system: local-frame, stands_for: state }
    rows: |
""" + table(("at", "fix", "perch"), ("0", "46.5021,11.3402", "lime-3#crown"), ("45", "46.5023,11.3405", "lime-3#crown"),
            ("130", "46.5030,11.3411", "lavender-bed#north-row"), ("610", "?", "_")), "A moth, tagged for one night.")
LIME = bean("lime-3", "organism", "soma", "lime-3 — a lime tree", "An invented lime tree at the edge of the plot.",
            "organism_id", "organism:lime-3", "logical", "", "A lime tree.")
LAVENDER = bean("lavender-bed", "organism", "soma", "lavender-bed — a bed of lavender", "An invented lavender bed.",
                "organism_id", "organism:lavender-bed", "logical", "", "A bed of lavender.")
BIRCH = bean("birch-2", "organism", "soma", "birch-2 — a birch with a dendrometer",
             "An invented birch whose stem radius is logged hourly.", "organism_id", "organism:birch-2", "logical", """lines:
  radius: { zero: "the pith, at breast height", toward: "out to the bark, facing north" }
series:
  stem-radius:
    grid: { of: time, in: gregorian-civil, every: { count: 1, unit: hour }, from: "2026-05-01 00:00+02:00" }
    unit: hour
    holds:
      - { name: radius-change, quantity: length, unit: millimetre, stands_for: point, between: linear, u: { count: "0.002", unit: millimetre } }
    rows: |
""" + table(("radius-change",), ("0",), ("0.004",), ("0.011",), ("0.009",), ("0.015",)) + """  rings:
    span: { of: place, in: along, from: "birch-2/radius+0", measure: { count: 60, unit: millimetre } }
    unit: millimetre
    placement: bounds
    holds:
      - { name: latewood, quantity: ratio, unit: percent, stands_for: mean }
""", "A birch with a band dendrometer.")
RINGS = T_.join(("from", "to", "latewood")) + "\n" + "".join(T_.join(r) + "\n" for r in (
    ("0", "4", "31"), ("4", "7", "28"), ("7", "11", "35"), ("11", "13", "_"), ("13", "16", "30")))
CORE = bean("core-b", "material", "soma", "core-b — a rock core", "An invented rock core, three metres long.",
            "serial", "CORE-B-0001", "hardware", """lines:
  depth: { zero: "the top of the core as it was taken", toward: "down the hole" }
series:
  strata:
    span: { of: place, in: along, from: "core-b/depth+0", measure: { count: 3, unit: metre } }
    unit: millimetre
    placement: bounds
    holds:
      - { name: porosity, quantity: ratio, unit: percent, stands_for: mean }
      - { name: drilled, system: unix-epoch, from: "1767225600000", unit: minute, stands_for: max, monotone: increasing }
    rows: |
""" + table(("from", "to", "porosity", "drilled"), ("0", "420", "12.5", "35"), ("420", "1150", "9.25", "80"),
            ("1150", "1600", "_", "112"), ("1600", "2900", "14", "190")), "A rock core.")
SEASON = """---
mapping: birch-season
kind: procedure
summary: "An invented tree's year as a walk: bud to leaf-fall and round again, until it is felled."
steps:
  - { id: bud-break, do: "the buds open", usually: { of: time, measure: { count: 10, unit: day } }, next: [ { to: leaf-out } ] }
  - id: leaf-out
    do: "the leaves unfold and begin to feed the tree"
    takes: [ { code: tree-inputs:water, amount: { count: 40, unit: litre } }, { code: tree-inputs:carbon-dioxide } ]
    gives: [ { code: tree-inputs:sugar }, { code: tree-inputs:oxygen } ]
    usually: { of: time, in: gregorian-civil, level: month, count: 4 }
    next: [ { to: leaf-fall } ]
  - { id: leaf-fall, do: "the leaves colour and fall", next: [ { to: dormant } ] }
  - { id: dormant, do: "the tree rests through the cold", next: [ { to: bud-break } ] }
  - { id: felled, do: "the tree is cut down", exit: true, final: true, reasons: [storm, disease] }
---
A tree's year, invented.
"""
TREE_INPUTS = "code\tname\nwater\twater\ncarbon-dioxide\tcarbon dioxide\nsugar\tsugar\noxygen\toxygen\n"
WALK = """---
mapping: walk-placing
kind: procedure
summary: "An invented agency's walk for placing a manuscript with a publisher."
steps:
  - { id: submitted, do: "the manuscript is sent to the house", by: agent, usually: { of: time, measure: { count: 30, unit: day } }, next: [ { to: read } ] }
  - id: read
    do: "an editor reads it"
    by: publisher
    usually: { of: time, in: gregorian-civil, level: month, count: 2 }
    next: [ { to: offered, when: "the house wants it" }, { to: declined, when: "it does not" } ]
  - { id: offered, do: "the house offers terms", by: agent, next: [ { to: contracted } ] }
  - { id: contracted, do: "both sign", by: author, final: true }
  - { id: declined, do: "the house says no", reasons: [list-full, not-for-us] }
  - { id: on-hold, do: "the placing waits", resumes: true, reasons: [author-revising, house-reorganising] }
  - { id: withdrawn, do: "the manuscript is taken back", exit: true, reasons: [author-withdrew, sold-elsewhere] }
---
The agency's walk.
"""


def person(id, name):
    return bean(id, "person", "soma", f"{id} — {name}", f"{name}, invented.", "identifier", f"person:{id}", "logical", "",
                f"{name}, invented.", own="owned_by: { legal: { crown: agape } }\nresponsibility: { legal: { self: true } }\n"
                ).replace("owned_by:", "consent: { bean: harbour-tale }\nowned_by:", 1)   # kept by name on their word (F2)


LARK = bean("lark-press", "org", "lekton", "lark-press — a publisher", "An invented small publishing house.",
            "identifier", "org:lark-press", "logical", "", "A publisher.")
CASE = bean("harbour-tale", "contract", "lekton", "harbour-tale — placing a manuscript",
            "Rhea places Wren's manuscript with Lark Press.", "identifier", "contract:harbour-tale", "logical", """parties:
  author: { who: { bean: wren }, role: author, accepted: 2026-09-01 }
  agent: { who: { bean: rhea }, role: agent, accepted: 2026-09-01 }
  publisher: { who: { bean: lark-press }, role: publisher }
words: { form: spoken }
courses:
  lark: { walk: { mapping: walk-placing }, note: "placing with Lark Press" }
selections:
  translation-rights: { what: "whether the house asks for translation rights", steps: [ { id: asked, op: select, genos: contract } ] }
  rights-papers: { what: "the papers that show which translation rights are free", steps: [ { id: papers, op: select, genos: document } ] }
""", "The placing of a manuscript.", own="owned_by: { legal: { crown: agape } }\nresponsibility: { legal: { parties: true } }\n")
CHECKLIST = """---
mapping: manuscript-parts
kind: checklist
summary: "What a publisher asks to see with a manuscript: invented."
items:
  - { id: synopsis, do: "a one-page synopsis", by: author }
  - { id: three-chapters, do: "the first three chapters", by: author, one_of: sample }
  - { id: full-text, do: "the whole manuscript", by: author, one_of: sample }
  - { id: cover-letter, do: "a letter introducing the book", by: agent }
  - { id: rights-list, do: "which translation rights are free", by: agent, needed_when: "harbour-tale:translation-rights", met_by: "harbour-tale:rights-papers" }
---
A checklist, invented.
"""

# THE GARDEN'S OWN LAW: two gene proved locally first (D29), a name for an organism, and the rows the law lacks — only
# those: where a later release carries a row itself, the garden adds none of it (the gate refuses a copy).
LAW = read("seed/std-vocab.md")


def lacks(key, name):
    return not re.search(r"(?m)^\s*- \{ ?%s: %s[ ,}]|^\s*- %s: %s\s*$" % (key, re.escape(name), key, re.escape(name)), LAW)


adds = []
if lacks("dimension", "temperature"):
    adds.append("  dimensions:\n    - { dimension: temperature, meaning: \"how hot: a garden's own row until the law has one\" }\n")
if lacks("quantity", "volume-flow"):
    adds.append("  quantities:\n    - { quantity: volume-flow, of: { length: 3, time: -1 } }\n")
if lacks("unit", "litre-per-minute"):
    adds.append("  units:\n    - { unit: litre-per-minute, quantity: volume-flow, factor: [1, 60000], meaning: \"a litre each minute\" }\n")
adds.append("""  anchor_systems:
    - system: water-celsius
      dimension: temperature
      neighbours: metered
      restrictions: { lines: 1, metered: temperature }
      meaning: "a water temperature on the Celsius scale, as this bench writes one: a position, not a quantity"
      pattern: '^C:-?(0|[1-9][0-9]{0,3})(\\.[0-9]{1,3})?$'
      form_note: "`C:<degrees>` — `C:55.2`"
      example: "C:55.2"
      establishes: false
      why: "a temperature says how hot, never which being"
  knowledge_schemes:
    - { scheme: tree-inputs, classifies: "what a tree takes in and gives out, as this garden names it", publisher: "this garden", url: "lists/tree-inputs.tsv", levels: [ { level: input } ], neighbours: none, sources: "lists/tree-inputs.tsv" }
""")
VOCAB_EXTRA = """local_gene:
  - { genos: organism, of_nature: soma, level: organism, establishing_anchor_family: [logical], meaning: "a living thing that is not a person: a tree, a moth" }
  - { genos: material, of_nature: soma, level: material, meaning: "a body of matter taken and kept: a core, a sample" }
local_terms:
  - term: organism_id
    meaning: "the logical identity of an organism: a name the garden mints once (`organism:<name>`)"
    context_keys: [organism_id]
    enforced_by: none
    anchor: { class: logical, establishing: true, minted: true }
    merge: { cardinality: single, order: none }
registry_files:
  - { registry: tree-inputs, file: lists/tree-inputs.tsv, key: code }
registry_additions:
""" + "".join(adds)
_v = read("VOCAB.md")
for _k in ("local_gene", "local_terms", "registry_files", "registry_additions"):
    _v = re.sub(rf"(?m)^{_k}: (\[\]|\{{\}}).*\n", "", _v)
_h, _sep, _rest = _v.partition("\n---\n")
write("VOCAB.md", _h + "\n" + VOCAB_EXTRA + _sep + _rest)
write("lists/tree-inputs.tsv", TREE_INPUTS)
DOCS = {"beans/heater-rig.md": HEATER, "beans/moth-7.md": MOTH, "beans/lime-3.md": LIME, "beans/lavender-bed.md": LAVENDER,
        "beans/birch-2.md": BIRCH, "beans/core-b.md": CORE, "beans/wren.md": person("wren", "an author"),
        "beans/rhea.md": person("rhea", "a literary agent"), "beans/lark-press.md": LARK, "beans/harbour-tale.md": CASE,
        "mappings/birch-season.md": SEASON, "mappings/walk-placing.md": WALK, "mappings/manuscript-parts.md": CHECKLIST}
for _p, _t in DOCS.items():
    write(_p, _t)
write("series/birch-2/rings/core-2026.tsv", RINGS)
rc, out = save("the invented fixtures", [os.path.basename(p)[:-3] for p in DOCS], rule_change=True)
check("the invented fixtures — a series of every shape, lines lent by beings, walks, a case with a course and a "
      "checklist — commit through the hook with 0 errors, a part of a series in its file beside them",
      rc == 0 and " 0 error(s)" in out, out)
check("...and every new term is used by them: series, lines, courses, items (and moves, below)",
      all(re.search(rf"(?m)^{t}:", "".join(DOCS.values())) for t in ("series", "lines", "courses", "items")))


# ============================================================================ the moves, one save at a time
def move(line, what="a move"):
    p = "beans/harbour-tale.md"
    head, sep, body = read(p).partition("\n---\n")
    head += ("" if "\nmoves:" in head else "\nmoves:") + "\n  - " + line
    write(p, head + sep + body)
    return save(what, ["harbour-tale"])


MOVES = ['{ course: lark, at: now, step: submitted, by: rhea, why: "sent with the first three chapters" }',
         '{ course: lark, at: now, step: on-hold, by: rhea, reason: author-revising }',
         '{ course: lark, at: now, step: submitted, by: rhea, why: "the revised chapters went back" }',
         '{ course: lark, at: now, step: read, by: lark-press }']
_res = [move(m) for m in MOVES[:2]]
# A STEP VISITED AGAIN IS VISITED AT A LATER MOMENT: a move is stamped to the minute, and the return to `submitted` is
# made once the clock has left the minute the first was made in, as a person's second visit is
import time
_first = re.findall(r'at: "([^"]+)"', read("beans/harbour-tale.md").split("moves:", 1)[-1])[0]
while time.strftime("%H:%M") == _first[11:16]:
    time.sleep(1)
_res += [move(m) for m in MOVES[2:]]
check("four moves along the walk commit one save at a time: submitted, a pause, back to where it was, read",
      all(rc == 0 for rc, _ in _res), [o[-600:] for rc, o in _res if rc])
_moves = re.findall(r'at: "([^"]+)"', read("beans/harbour-tale.md").split("moves:", 1)[-1])
check("...each move's moment is the save's, stamped from the clock in the journal heading's own form — never typed",
      len(_moves) == 4 and all(re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}[+-]\d{2}:\d{2}", m) for m in _moves)
      and all(m in read("log/journal.md") for m in _moves), _moves)
check("the moves term is used too, and a gate run over the whole garden is clean",
      "moves:" in read("beans/harbour-tale.md") and " 0 error(s)" in gate()[1], gate()[1][-600:])

# ============================================================================ the reader
API = run(PY, "-c", """
import sys, json
sys.path.insert(0, 'bin')
import dmseq
from fractions import Fraction
out = {}
rs = dmseq.rows('.', 'heater-rig', 'run-3')
out['n'] = len(rs)
out['positions'] = [r['position'] for r in rs]
out['excluded'] = [r['n'] for r in rs if r['excluded']]
at = dmseq.read_at('.', 'heater-rig', 'run-3', '2026-03-02 09:01:30+01:00')
out['flow'] = str(at['flow']['value']); out['flow_how'] = at['flow']['how']
out['heating'] = at['heating']['value']; out['heating_how'] = at['heating']['how']
out['drawn'] = [at['drawn']['value'], at['drawn']['how']]
at2 = dmseq.read_at('.', 'heater-rig', 'run-3', '2026-03-02 09:03:30+01:00')
out['skip_excluded'] = at2['flow']['how']
out['beyond'] = dmseq.read_at('.', 'birch-2', 'stem-radius', 9)['radius-change']['how']
out['rings'] = [r['position'] for r in dmseq.rows('.', 'birch-2', 'rings')]
out['core'] = dmseq.read_at('.', 'core-b', 'strata', 'core-b/depth+1.3')['porosity']
out['core_region'] = dmseq.read_at('.', 'core-b', 'strata', 'core-b/depth+0.5')['porosity']
out['moth'] = dmseq.read_at('.', 'moth-7', 'night-1', 100)['perch']
w = dmseq.where('.', 'harbour-tale', 'lark')
out['where'] = [w['step'], w['by'], w['party'], w['moves']]
print(json.dumps(out, default=str))
""", cwd=G)
import json
try:
    A = json.loads(API.stdout.strip().splitlines()[-1])
except Exception:
    A = {}
check("dmseq.rows reads a grid's rows at their positions, written in the line's own form, the first at `from`",
      A.get("n") == 6 and A.get("positions", [None])[0] == "2026-03-02 09:00+01:00"
      and A["positions"][5] == "2026-03-02 09:05+01:00", API.stdout + API.stderr)
check("...and a cell set aside is shown on its row, with its judge", A.get("excluded") == [3], A.get("excluded"))
check("dmseq.read_at reads a point on the straight line between two rows, exactly (5.1 at half past the first minute)",
      A.get("flow") == "51/10" and A.get("flow_how", "").startswith("linear"), (A.get("flow"), A.get("flow_how")))
check("...a state held from the row before, and a sum over the minute that follows its row read inside that minute, "
      "said as the row's sum — never a share of it",
      A.get("heating") == "100" and A.get("heating_how", "").startswith("state")
      and A.get("drawn") == ["4.1", "over the row's region, as its sum"], A)
check("...an excluded cell is read by nothing: the line is not drawn through it", A.get("skip_excluded") == "not read", A)
check("...and nothing is read beyond the last row: never extrapolated", A.get("beyond") == "not read", A)
check("a listed series' regions along a line a being lends are written in metres, `<being>/<line>+<metres>`",
      A.get("rings", [None])[0] == ["birch-2/radius+0", "birch-2/radius+0.004"], A.get("rings"))
check("...a region's value is read inside it, said as its mean; a stretch with nothing there says so (`_`)",
      (A.get("core_region") or {}).get("value") == "9.25" and "mean" in (A.get("core_region") or {}).get("how", "")
      and (A.get("core") or {}).get("value") == "_", (A.get("core"), A.get("core_region")))
check("a moth's perch — a position in a local frame, a state — is held from its last fix",
      (A.get("moth") or {}).get("value") == "lime-3#crown", A.get("moth"))
check("dmseq.where reads where a course stands and who acts next, as a party of the case",
      A.get("where") == ["read", "publisher", "lark-press", 4], A.get("where"))
_show = run(PY, "bin/dmseq.py", "at", "heater-rig", "run-3", "2026-03-02 09:01:30+01:00", cwd=G).stdout
_exact = run(PY, "bin/dmseq.py", "at", "heater-rig", "run-3", "2026-03-02 09:01:30+01:00", "--exact", cwd=G).stdout
check("a value read between rows is printed to its uncertainty's digits (5.10 at u 0.05), exactly on request (5.1)",
      "flow: 5.10 litre-per-minute (u 0.05" in _show and "flow: 5.1 litre-per-minute (u 0.05)" in _exact, _show + _exact)
_shw = run(PY, "bin/dmseq.py", "show", "heater-rig", "run-3", cwd=G).stdout
check("dmseq show prints each row with the line of the table it came from, gaps with their reasons, and what was set "
      "aside, by whom and why",
      "[.rows line 5]" in _shw and "? (a reading was made, and it cannot be read here)" in _shw
      and "SET ASIDE by keeper: air in the flow sensor" in _shw and "< 5 percent (below a limit)" in _shw
      and "no leap second counted" in _shw, _shw[-1200:])
_tr = run(PY, "bin/dmseq.py", "course", "harbour-tale", cwd=G).stdout
check("dmseq course says the step, since when, how many moves, and who acts next",
      "at 'read' since" in _tr and "who acts next: publisher (lark-press)" in _tr and "4 move(s)" in _tr, _tr)
_chk = run(PY, "bin/dmseq.py", "check", cwd=G)
check("dmseq check judges every series as the gate does, and says so in one line", _chk.returncode == 0
      and "0 error(s) in the series" in _chk.stdout, _chk.stdout + _chk.stderr)
_ro = run(PY, "bin/dmseq.py", "rows", "core-b", "strata", cwd=G).stdout
check("dmseq rows prints the rows as one table, a region's two ends as two columns",
      _ro.splitlines()[0] == "from\tto\tdrilled\tporosity" and "core-b/depth+0.42\tcore-b/depth+1.15\t80\t9.25" in _ro, _ro)
_off = run(PY, "bin/dmseq.py", "show", "core-b", "strata", cwd=G).stdout
check("...and an offset channel is shown as the position it is: 35 minutes from its `from`",
      "drilled: 35 minute(s) from 1767225600000 = 1767227700000" in _off, _off[:600])

# two recordings of one line, compared row by row: agree, compatible within k·u (labelled, never merged), differ
_hr = read("beans/heater-rig.md")
write("beans/heater-rig.md", _hr.replace("  run-3:\n", '''  run-3-check:
    grid: { of: time, in: gregorian-civil, every: { count: 1, unit: minute }, from: "2026-03-02 09:00+01:00" }
    unit: minute
    holds:
      - { name: flow, quantity: volume-flow, unit: litre-per-minute, stands_for: point, u: { count: "0.05", unit: litre-per-minute } }
    rows: |
''' + table(("flow",), ("0",), ("4.25",), ("6.3",)) + "  run-3:\n", 1))
_cmp = run(PY, "bin/dmseq.py", "compare", "heater-rig", "run-3", "heater-rig", "run-3-check", cwd=G).stdout
check("dmseq compare labels two recordings row by row: agree, compatible within k·u at k = 2 — labelled, never merged — "
      "or differ, and a row one of them holds alone",
      "09:00+01:00 flow: agree" in _cmp and "09:01+01:00 flow: compatible within k·u (k = 2)" in _cmp
      and "09:02+01:00 flow: differ" in _cmp and "held by the first only" in _cmp, _cmp)
_long = "".join(f"      {i}\n" for i in range(101))
write("beans/heater-rig.md", _hr.replace("  run-3:\n", '''  run-3-long:
    grid: { of: time, in: gregorian-civil, every: { count: 1, unit: minute }, from: "2026-03-03 09:00+01:00" }
    unit: minute
    holds:
      - { name: drawn, quantity: volume, unit: litre, stands_for: point }
    rows: |
      drawn
''' + _long + "  run-3:\n", 1))
rc, out = gate()
check("an inline table of more than a hundred rows passes, and warns that its rows belong in the parts of a file",
      rc == 0 and "holds 101 rows, more than 100" in out, out[-700:])
write("beans/heater-rig.md", _hr)

# ============================================================================ refused by name
BASE = {p: read(p) for p in list(DOCS) + ["beans/harbour-tale.md"]}


def probe(path, old, new, count=1):
    t = BASE[path]
    assert t.count(old) >= 1, (path, old)
    write(path, t.replace(old, new, count))
    rc, out = gate()
    write(path, BASE[path])
    return rc, out


def refused(name, path, old, new, *said):
    rc, out = probe(path, old, new)
    check(name, rc != 0 and all(s in out for s in said), out[-900:])


refused("a step key the walk does not declare is refused by name (S2: steps are closed)", "mappings/walk-placing.md",
        '  - { id: offered, do: "the house offers terms", by: agent,',
        '  - { id: offered, do: "the house offers terms", by: agent, owner: rhea,',
        "carries `owner`, which the term `steps` does not declare")
refused("...a step's `reasons` that are not a list of kebab words", "mappings/walk-placing.md",
        "reasons: [list-full, not-for-us]", 'reasons: "list full"', "`reasons` is 'list full'")
refused("...a pause with a way on", "mappings/walk-placing.md", "resumes: true, reasons",
        "resumes: true, next: [ { to: read } ], reasons", "is a pause (`resumes`) with a `next`")
refused("...a final end with a way on", "mappings/walk-placing.md", '{ id: contracted, do: "both sign", by: author, final: true }',
        '{ id: contracted, do: "both sign", by: author, final: true, next: [ { to: read } ] }', "is `final` and names a `next`")
refused("...and `usually` in a form the walk does not read", "mappings/walk-placing.md",
        "usually: { of: time, in: gregorian-civil, level: month, count: 2 }",
        "usually: { of: time, in: gregorian-civil, level: fortnight, count: 2 }", "fortnight")
refused("...or `usually` with an end: how long a step takes has none", "mappings/walk-placing.md",
        "usually: { of: time, in: gregorian-civil, level: month, count: 2 }",
        'usually: { of: time, from: "2026-01-01", measure: { count: 2, unit: day } }', "how long a step takes has no ends")
refused("a channel stating both `u` and `accuracy` is refused by name", "beans/heater-rig.md", 'limits: { below: "5" }, accuracy: { count: "2", unit: percent, kind: bound } }',
        'limits: { below: "5" }, accuracy: { count: "2", unit: percent, kind: bound }, u: { count: "1", unit: percent } }',
        "states both `u` and `accuracy`")
refused("...an accuracy whose kind is no row of `accuracy_kinds`", "beans/heater-rig.md", 'limits: { below: "5" }, accuracy: { count: "2", unit: percent, kind: bound } }',
        'limits: { below: "5" }, accuracy: { count: "2", unit: percent, kind: bound } }'.replace("kind: bound", "kind: roughly"), "roughly")
refused("...an accuracy with no number", "beans/heater-rig.md", 'limits: { below: "5" }, accuracy: { count: "2", unit: percent, kind: bound } }', 'limits: { below: "5" }, accuracy: { count: "2", unit: percent, kind: bound } }'.replace('count: "2", ', ''), "count")
refused("...an accuracy in a unit of another quantity", "beans/heater-rig.md", 'limits: { below: "5" }, accuracy: { count: "2", unit: percent, kind: bound } }', 'limits: { below: "5" }, accuracy: { count: "2", unit: percent, kind: bound } }'.replace('unit: percent, kind', 'unit: litre, kind'),
        "measures volume")
refused("a series with both a grid and a span", "beans/heater-rig.md", "    unit: minute\n    placement: following",
        "    span: { of: time, from: \"2026-03-02 09:00+01:00\" }\n    unit: minute\n    placement: following",
        "states both a `grid` and a `span`")
refused("a channel holding a measured value and a code at once", "beans/heater-rig.md",
        "{ name: drawn, quantity: volume, unit: litre, stands_for: sum }",
        "{ name: drawn, quantity: volume, unit: litre, scheme: tree-inputs, stands_for: sum }",
        "holds quantity and scheme: a channel holds exactly one of")
refused("a mean read at a point: what a cell stands for needs a region", "beans/moth-7.md",
        "{ name: perch, system: local-frame, stands_for: state }", "{ name: perch, system: local-frame, stands_for: mean }",
        "'mean' is over a region")
refused("a line drawn between two positions of a system with no measure", "beans/moth-7.md",
        "{ name: fix, system: geographic, prefix: \"EPSG:4326;\", stands_for: point }",
        "{ name: fix, system: geographic, prefix: \"EPSG:4326;\", stands_for: point, between: linear }",
        "is linear where the channel holds no measure")
refused("an empty cell: a value nobody read is a gap token", "beans/birch-2.md", "      0.011\n", "      0.011\t\n",
        "is not a table in its one form", "empty cell")
refused("a header that does not name a channel", "beans/heater-rig.md", "      flow\tdrawn\toutlet\theating\n",
        "      flow\tdrawn\toutlet\tpower\n", "names the columns ['flow', 'drawn', 'outlet', 'power']")
refused("a cell that is no count: a comma for a decimal point", "beans/heater-rig.md", "      4.2\t4.1\t18.5\t100\n",
        "      4,2\t4.1\t18.5\t100\n", "column `flow` holds '4,2'")
refused("a bare `<` where the channel states no limit", "beans/heater-rig.md", "      <0.1\t0\t52.5\t0\n",
        "      <\t0\t52.5\t0\n", "a bare `<` stands for the channel's `limits`, and it states none")
refused("a position cell not in its system's one form", "beans/heater-rig.md", "      0\t0\t14.0\t100\n",
        "      0\t0\t14,0\t100\n", "'C:14,0' is not a position in the one form 'water-celsius' writes")
refused("a monotone channel going back", "beans/core-b.md", "      1150\t1600\t_\t112\n", "      1150\t1600\t_\t60\n",
        "`drilled` goes back (80 then 60), and the channel is increasing")
refused("an exclusion at no row", "beans/heater-rig.md", "- { at: 3, channel: flow,", "- { at: 30, channel: flow,",
        "sets aside a cell at 30, where no row is")
refused("a grid whose stride is no whole number of the unit held", "beans/heater-rig.md",
        "every: { count: 1, unit: minute }", "every: { count: 90, unit: second }", "strides 1.5 minutes")
refused("a unit that does not measure the line", "beans/heater-rig.md", "    unit: minute\n", "    unit: litre\n",
        "'litre' measures volume, and the line is metered in time")
refused("a listed row beyond the span's end", "beans/core-b.md", "      1600\t2900\t14\t190\n", "      1600\t3100\t14\t190\n",
        "beyond the span's end")
refused("a region that runs backwards", "beans/core-b.md", "      420\t1150\t9.25\t80\n", "      420\t400\t9.25\t80\n",
        "runs from 420 to 400")
refused("a held series that says more than where it is kept", "beans/heater-rig.md", "  run-3:\n",
        "  run-4: { held: \"root:bench-store/5f1c2a\", unit: minute }\n  run-3:\n", "holds ['unit'] beside `held`")
refused("a line along a being written with no distance", "beans/core-b.md", 'from: "core-b/depth+0"',
        'from: "core-b/depth"', "'core-b/depth' is not a position in the one form 'along' writes")
refused("a checklist naming a selection on a bean that is not here", "mappings/manuscript-parts.md",
        'met_by: "harbour-tale:rights-papers"', 'met_by: "nobody:rights-papers"',
        "names bean 'nobody', which this garden does not hold")
refused("...or a selection the bean does not declare", "mappings/manuscript-parts.md",
        'met_by: "harbour-tale:rights-papers"', 'met_by: "harbour-tale:rights-paper"', "is no key of `selections`")

# a part no series claims; a part rewritten
write("series/moth-7/night-2/a.tsv", "at\tfix\n0\t?\n")
rc, out = gate()
check("a part of a series the bean does not hold is refused by name", rc != 0
      and "series/moth-7/night-2/a.tsv: a part of the series 'night-2' of the bean 'moth-7', which holds no series by "
          "that name" in out, out[-700:])
os.remove(os.path.join(G, "series", "moth-7", "night-2", "a.tsv"))
write("series/birch-2/rings/core-2026.tsv", RINGS.replace("0\t4\t31\n", "0\t4\t32\n"))
rc, out = save("a part rewritten", ["birch-2"])
check("a part a commit already holds, rewritten, is refused at the commit — a part is written once", rc != 0
      and "series/birch-2/rings/core-2026.tsv: a series' part a commit already holds is changed" in out, out[-700:])
restore()
write("series/birch-2/rings/core-2026-b.tsv", "from\tto\tlatewood\n16\t19\t29\n")
rc, out = save("a new part", ["birch-2"])
check("...and a new part beside it is added, journalled as a change to its bean", rc == 0, out[-700:])
write("series/birch-2/rings/core-2026-c.tsv", "from\tto\tlatewood\n16\t19\t33\n")
rc, out = gate()
check("...while two parts that disagree at one position are refused: a position holds one row", rc != 0
      and "holds with other values" in out, out[-700:])
os.remove(os.path.join(G, "series", "birch-2", "rings", "core-2026-c.tsv"))
write("series/birch-2/rings/core-2026-b.tsv", "from\tto\tlatewood\n16\t19\t29\n")
rc, out = save("a part not in the commit", ["birch-2"])
restore()

# the moves
BASE["beans/harbour-tale.md"] = read("beans/harbour-tale.md")


def move_probe(line):
    p = "beans/harbour-tale.md"
    head, sep, body = BASE[p].partition("\n---\n")
    write(p, head + "\n  - " + line + sep + body)
    rc, out = gate()
    write(p, BASE[p])
    return rc, out


LAST = _moves[-1]
sys.path.insert(0, os.path.join(ROOT, "bin"))
import dmcal


def later(k):
    """LAST and k minutes: a moment typed for a probe the gate judges uncommitted, after every move written."""
    m = dmcal.moment(LAST)
    return dmcal.write_moment(m.ms + k * 60000, m.calendar, m.offset, "minute")


rc, out = move_probe(f'{{ course: lark, at: "{LAST}", step: read, by: rhea }}')
check("one move written twice — one course, one step, one moment — is refused by name: a merge keys a move by them",
      rc != 0 and "reaches 'read' at " in out and "as move 3 does" in out, out[-600:])
rc, out = move_probe(f'{{ course: lark, at: "{later(1)}", step: printed, by: rhea }}')
check("a move to a step the walk does not have is refused by name", rc != 0
      and "reaches 'printed', which is no step of the walk walk-placing" in out, out[-600:])
rc, out = move_probe(f'{{ course: lark, at: "{later(2)}", step: contracted, by: rhea }}')
check("a move the walk does not offer, with no `why`, is refused", rc != 0
      and "reaches 'contracted', a move the walk does not offer ('read' leads on to 'offered', 'declined' only)" in out, out[-600:])
rc, out = move_probe(f'{{ course: lark, at: "{later(3)}", step: contracted, by: rhea, why: "signed at the fair, unread" }}')
check("...and with its `why` it passes, and warns", rc == 0 and "a move the walk does not offer" in out
      and "its `why` says why" in out, out[-600:])
rc, out = move_probe(f'{{ course: lark, at: "{later(4)}", step: withdrawn, by: rhea, reason: sold-elsewhere }}')
check("a way out is reached from any step, with a reason from its own list", rc == 0, out[-600:])
rc, out = move_probe(f'{{ course: lark, at: "{later(5)}", step: withdrawn, by: rhea, reason: lost-interest }}')
check("...and a reason the step does not list is refused by name", rc != 0
      and "cites the reason 'lost-interest', which is not one of the step 'withdrawn''s" in out, out[-600:])
rc, out = move_probe(f'{{ course: lark, at: "{later(6)}", step: declined, by: lark-press, reason: list-full }}\n'
                     f'  - {{ course: lark, at: "{later(7)}", step: submitted, by: rhea, why: "sent again the next season" }}')
check("an end that is not final may be left: a declined manuscript is sent again", rc == 0, out[-600:])
rc, out = move_probe(f'{{ course: lark, at: "{later(8)}", step: offered, by: lark-press }}\n'
                     f'  - {{ course: lark, at: "{later(9)}", step: contracted, by: rhea }}\n'
                     f'  - {{ course: lark, at: "{later(10)}", step: read, by: rhea, why: "again" }}')
check("nothing follows a final end, `why` or no `why`", rc != 0 and "follows 'contracted', a final step" in out, out[-600:])
rc, out = move_probe(f'{{ course: lark, at: "{later(11)}", step: on-hold, by: rhea, reason: house-reorganising }}\n'
                     f'  - {{ course: lark, at: "{later(12)}", step: offered, by: lark-press }}')
check("after a pause the case returns to where it was, or takes a way out", rc != 0
      and "'on-hold' is a pause, and the move after it returns to 'read'" in out, out[-600:])
rc, out = move_probe('{ course: lark, at: "2020-01-01 10:00+00:00", step: offered, by: lark-press }')
check("a course's moments never go back", rc != 0 and "before the move it follows: a course's moments never go back" in out,
      out[-600:])
rc, out = move_probe('{ course: lark, at: "2026-13-01 10:00+00:00", step: offered, by: lark-press }')
check("a moment on a day no calendar has is refused", rc != 0 and "is no day of gregorian-civil" in out, out[-600:])
rc, out = move_probe('{ course: lark, at: "2026-12-01", step: offered, by: lark-press }')
check("...and a day with no clock reading is no moment: a move is held to the minute", rc != 0
      and "is written to the day, and `at` holds a position to the minute or finer" in out, out[-600:])
rc, out = move_probe('{ course: lark, at: now, step: offered, by: lark-press }')
check("`now` left unstamped is refused, with the save that stamps it", rc != 0 and ".at is `now`" in out
      and "the word the save writes the moment" in out and "bin/dmsave.py" in out, out[-600:])
rc, out = move_probe('{ course: lark, at: "' + later(1) + '", step: offered, by: nobody }')
check("a move by a bean that is not here is refused by name", rc != 0 and ".by 'nobody' is not the id of a bean" in out,
      out[-600:])
rc, out = move_probe('{ course: ghost, at: "' + later(1) + '", step: offered, by: rhea }')
check("a move along a course the bean does not have is refused by name", rc != 0 and "'ghost' is no key of `courses`" in out,
      out[-600:])
# typed, not stamped: a moment that is not the moment of the heading the commit adds
head, sep, body = BASE["beans/harbour-tale.md"].partition("\n---\n")
write("beans/harbour-tale.md", head + '\n  - { course: lark, at: "2030-01-01 10:00+00:00", step: offered, by: lark-press }' + sep + body)
rc, out = save("a typed moment", ["harbour-tale"])
check("a moment typed rather than stamped is refused at the commit: it is read from the clock, never typed", rc != 0
      and "is 2030-01-01 10:00+00:00, and it is read from the clock, never typed" in out, out[-700:])
restore()

# ============================================================================ S0: the table, written back as it was read
sys.path.insert(0, os.path.join(ROOT, "bin"))
import dmparse
_t = "".join(T_.join(l) + "\n" for l in HEATER_ROWS)
_h, _rows = dmparse.table_read(_t)
check("S0: dmparse's writer writes back what its reader read, byte for byte", dmparse.table_write(_h, _rows) == _t)
check("...and its reader refuses a table out of its form by name: a trailing tab, a carriage return, an empty line",
      "empty cell" in (dmparse.table_problems("a\tb\n1\t\n") or [""])[0]
      and "carriage return" in (dmparse.table_problems("a\tb\r\n1\t2\r\n") or [""])[0]
      and "is empty" in (dmparse.table_problems("a\n1\n\n2\n") or [""])[0], "")
import yaml
_doc = {"series": {"run-3": {"unit": "minute", "rows": _t}}}
_plain = yaml.safe_dump(_doc, allow_unicode=True, width=10 ** 6)
_ours = yaml.dump(_doc, Dumper=dmparse.table_dumper(yaml.SafeDumper), allow_unicode=True, width=10 ** 6)
check("S0: PyYAML alone writes a table as one escaped line; the table dumper writes it as a block, and it reads back the "
      "same", '\\t' in _plain and "rows: |\n" in _ours and "\t" in _ours and yaml.safe_load(_ours) == _doc
      and dmparse.loads(_ours) == _doc, _ours)
_mm = run(PY, "-c", "import sys; sys.path.insert(0, 'bin'); import dmmerge, dmpropose, yaml, json; "
          "t = json.loads(sys.argv[1]); d = {'series': {'run-3': {'rows': t}}}; "
          "print(yaml.dump(d, Dumper=dmmerge._IndentedDumper, width=10**6)); print('----'); print(dmpropose._dump(d))",
          json.dumps(_t), cwd=G)
check("...and the merge and the proposals write it through the dumper: a block, tabs and all",
      _mm.stdout.count("rows: |") == 2 and "\\t" not in _mm.stdout, _mm.stdout + _mm.stderr)

# a real merge of two branches that both change one series, differently — each notes its flow channel its own way, and
# one adds a run: the driver merges three ways, so the run added on one side is taken, and the member both changed is
# kept both ways for a person, rewritten as a block
run("git", "checkout", "-q", "-b", "ours", cwd=G)
_hb = read("beans/heater-rig.md")
write("beans/heater-rig.md", _hb.replace('persists: offset }', 'persists: offset, note: "calibrated before the run" }', 1))
save("a note on the flow channel", ["heater-rig"])
run("git", "checkout", "-q", "master", cwd=G)
write("beans/heater-rig.md", _hb.replace('persists: offset }', 'persists: offset, note: "calibrated after the run" }', 1).replace("  run-3:\n", "  run-2:\n    grid: { of: time, in: gregorian-civil, every: { count: 1, unit: minute }, from: \"2026-03-01 09:00+01:00\" }\n"
                                         "    unit: minute\n    holds:\n      - { name: flow, quantity: volume-flow, unit: litre-per-minute, stands_for: point }\n"
                                         "    rows: |\n" + table(("flow",), ("0",), ("3.9",)) + "  run-3:\n", 1))
save("the run before", ["heater-rig"])
_mg = run("git", "merge", "-q", "--no-edit", "ours", cwd=G)
_merged = read("beans/heater-rig.md")
check("S0: two branches that each change the series merge through the semantic driver — the member both changed kept "
      "both ways for a person — and every table in the merged bean is still a block of tabs, each side's as it wrote it, "
      "never one escaped line",
      _mg.returncode == 0 and _merged.count("rows: |") == 3 and "\\t" not in _merged and "merge_open: true" in _merged
      and "calibrated before the run" in _merged and "run-2:" in _merged and "series.run-3" in _merged,
      (_mg.stdout + _mg.stderr)[-500:] + _merged[-1500:])
rc, out = gate()
check("...and the merged garden passes its gate, the captured disagreement warned about for a person",
      rc == 0 and "left UNCLEAN by a semantic merge" in out, out[-600:])
run("git", "merge", "--abort", cwd=G)
run("git", "reset", "-q", "--hard", "ORIG_HEAD", cwd=G)
restore()

# ============================================================================ S5: every {count, unit} by exact conversion
_m5 = run(PY, "-c", """
import sys, json
sys.path.insert(0, 'bin')
import dmmerge as M
a = {'run': {'span': {'of': 'place', 'in': 'along', 'from': 'x/y+0'}, 'unit': 'millimetre',
             'holds': [{'name': 'depth', 'quantity': 'length', 'unit': 'millimetre', 'stands_for': 'point', 'u': {'count': 2, 'unit': 'millimetre'}}],
             'rows': 'at\\tdepth\\n0\\t1500\\n250\\t<5\\n'}}
b = {'run': {'span': {'of': 'place', 'in': 'along', 'from': 'x/y+0'}, 'unit': 'metre',
             'holds': [{'name': 'depth', 'quantity': 'length', 'unit': 'metre', 'stands_for': 'point', 'u': {'count': '0.002', 'unit': 'metre'}}],
             'rows': 'at\\tdepth\\n0.25\\t<0.005\\n0\\t1.5\\n'}}
c = json.loads(json.dumps(b)); c['run']['rows'] = 'at\\tdepth\\n0.25\\t<0.005\\n0\\t1.6\\n'
print(json.dumps([M.canon_value('series', a) == M.canon_value('series', b), M.canon_value('series', a) == M.canon_value('series', c),
                  M.canon_value('clauses', {'x': {'what': 'w', 'amount': {'count': 1500, 'unit': 'millimetre'}}})
                  == M.canon_value('clauses', {'x': {'what': 'w', 'amount': {'count': '1.5', 'unit': 'metre'}}}),
                  M.canon_value('clauses', {'x': {'what': 'w', 'amount': {'count': '90.00', 'unit': 'XTS'}}})
                  == M.canon_value('clauses', {'x': {'what': 'w', 'amount': {'count': 90, 'unit': 'XTS'}}})]))
""", cwd=G)
try:
    _r5 = json.loads(_m5.stdout.strip().splitlines()[-1])
except Exception:
    _r5 = []
check("S5: a series written in millimetres and the same in metres, rows in another order, is ONE series to a merge",
      _r5[:1] == [True], _m5.stdout + _m5.stderr)
check("...a cell that differs is a disagreement, and nothing is absorbed", _r5[1:2] == [False], _r5)
check("...every {count, unit} is compared by exact conversion (1500 millimetre is 1.5 metre), and a currency, which no "
      "factor joins, by its count alone", _r5[2:] == [True, True], _r5)
run("git", "checkout", "-q", "-b", "mm", cwd=G)
_h2 = read("mappings/birch-season.md")
write("mappings/birch-season.md", _h2.replace("amount: { count: 40, unit: litre }", "amount: { count: 40000, unit: litre }"))
save("the water in millilitres... no: in litres, differently", ["birch-season"])
run("git", "checkout", "-q", "master", cwd=G)
write("mappings/birch-season.md", _h2.replace("amount: { count: 40, unit: litre }", "amount: { count: \"0.05\", unit: cubic-metre }"))
save("the water in cubic metres, and more of it", ["birch-season"])
_mg = run("git", "merge", "-q", "--no-edit", "mm", cwd=G)
_ms = read("mappings/birch-season.md")
check("S5: two sides that disagree on an amount keep both, each as its side wrote it — never respelt in the coherent unit",
      _mg.returncode == 0 and "merge_open: true" in _ms and "40000" in _ms and "cubic-metre" in _ms
      and "unit: litre" in _ms and "0.05" in _ms, _ms[-900:] + _mg.stdout + _mg.stderr)
run("git", "reset", "-q", "--hard", "ORIG_HEAD", cwd=G)
restore()
run("git", "checkout", "-q", "-b", "eq", cwd=G)
write("mappings/birch-season.md", _h2.replace("amount: { count: 40, unit: litre }", "amount: { count: \"0.04\", unit: cubic-metre }"))
save("the same water, in cubic metres", ["birch-season"])
run("git", "checkout", "-q", "master", cwd=G)
_before = read("mappings/birch-season.md")
_mg = run("git", "merge", "-q", "--no-edit", "eq", cwd=G)
check("...and two sides that wrote one amount in two units merge with no disagreement (40 litre is 0.04 cubic-metre)",
      _mg.returncode == 0 and "merge_open" not in read("mappings/birch-season.md"), (_mg.stdout + _mg.stderr)[-500:])

# ============================================================================ below the day
import dmcal
_m = dmcal.moment("persian:1404-12-29 23:30+03:30")
check("a moment is counted below the day in any calendar, and written back in it: across a Persian new year",
      dmcal.write_moment(_m.ms + 3600000, _m.calendar, _m.offset, "minute") == "persian:1405-01-01 00:30+03:30")
check("...one moment written at two offsets is one moment", dmcal.moment("2026-09-25 10:00Z").ms
      == dmcal.moment("2026-09-25 13:30+03:30").ms)
try:
    dmcal.moment("2026-09-25 10:00")
    _no = False
except ValueError:
    _no = True
check("...and a clock reading with no offset names no moment", _no)

shutil.rmtree(T, ignore_errors=True)
print(f"\nsequence: {len(PASSED)} passed, {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
