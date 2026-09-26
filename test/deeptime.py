#!/usr/bin/env python3
"""Where and when as one mechanism (std-vocab 24.0, PLACE): a position stated from another being, and read AT a time; a
being set in place for a window; deep time as an offset from a datum, crosswalked by computing; the ICS chart's units
as cells, and the golden spikes that fix their bases; a garden's own tabulated places with an overlay; a boundary marked
in a being, held at both ends; a stance on a code within a place.

Every fixture is INVENTED — a moor with its marks and stones, a transplanted sapling, a lake core, an island's parishes,
a quarry section with a local stage, a seed library — except the ICS chart and its GSSPs, which are the published data
the law ships (CC BY 4.0, International Commission on Stratigraphy).
Run: python3 test/deeptime.py   (0 = green)
"""
import os, re, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS = []
PY = sys.executable


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-3000:]))
    if not cond:
        FAILS.append(name)


def run(*a, cwd):
    return subprocess.run(list(a), capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd,
                          env=dict(os.environ, PYTHONIOENCODING="utf-8"))


T = tempfile.mkdtemp(prefix="dmdeep-")
G = os.path.join(T, "g")
r = run(PY, os.path.join(ROOT, "seed", "germinate.py"), G, "--gardener", "keeper", cwd=ROOT)
check("a garden germinates, kept by keeper — the ICS chart and its GSSPs pass the gate as the law ships them",
      r.returncode == 0, r.stdout + r.stderr)
run("git", "config", "user.name", "keeper (test)", cwd=G)
run("git", "config", "user.email", "keeper@example.org", cwd=G)


def write(rel, text):
    p = os.path.join(G, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def read(rel):
    return open(os.path.join(G, *rel.split("/")), encoding="utf-8").read()


def gate():
    r = run(PY, "bin/dmcheck.py", "--all", cwd=G)
    return r.stdout + r.stderr


def ok(out):
    return re.search(r" 0 error\(s\)", out) is not None


def save(what, names, rule_change=False):
    body = "- action: " + ("RULE-CHANGE (VOCAB.md) " if rule_change else "") + " ".join(f"[[{n}]]" for n in names)
    r = run(PY, "bin/dmsave.py", "keeper (test)", what, "--body", body, cwd=G)
    return r.returncode, r.stdout + r.stderr


def restore():
    run("git", "reset", "-q", "--hard", cwd=G)
    run("git", "clean", "-qfd", cwd=G)


def tool(*a):
    r = run(PY, *a, cwd=G)
    return r.returncode, r.stdout + r.stderr


def refused(name, rel, old, new, *want):
    text = read(rel)
    assert old in text, (rel, old)
    write(rel, text.replace(old, new, 1))
    out = gate()
    check(name, not ok(out) and all(w in out for w in want), out[-2000:])
    restore()


OWN = "owned_by: { legal: { owner: { bean: keeper } } }\nresponsibility: { legal: { holder: { bean: keeper } } }\n"


def bean(id, genos, nature, summary, rest, akey="serial", acls="hardware", status="confirmed"):
    return (f"---\nbean: {id}\ngenos: {genos}\ntitle: \"{id}\"\nstatus: active\nsummary: \"{summary}\"\nnature: {nature}\n{OWN}"
            f"identity: {{ status: {status}, anchors: [ {{ key: {akey}, value: \"{id.upper()}-1\", class: {acls}, "
            f"establishing: true }} ] }}\nprovenance: {{ src: observed, by: keeper, as_of: now }}\n{rest}---\n{id}, invented.\n")


def placed(*entries):
    return "located_at:\n" + "".join(f"  - {{ {e} }}\n" for e in entries)


# ---------------------------------------------------------------- the garden's own systems (N24, the local stage)
VOCAB_EXTRA = """local_gene:
  - { genos: material, of_nature: soma, meaning: "a thing of matter in the field — a mark, a stone, a core, invented" }
  - { genos: organism, of_nature: empsychon, meaning: "a living thing, invented" }
registry_additions:
  anchor_systems:
    - system: parish
      dimension: place
      resolves_through: geographic
      levels: [ { level: district }, { level: parish } ]
      neighbours: counted
      cells_in: { registry: parishes, take: code }
      overlay: { registry: parish-renames }
      meaning: "a parish of an invented island, as its council tabulates them"
      pattern: '^parish:[A-Z]+(-[0-9]+)?$'
      form_note: "`parish:<code>` — `parish:NORTH-1`"
      example: "parish:NORTH-1"
      establishes: false
      why: "a parish says roughly where, never what"
    - system: quarry-stage
      dimension: time
      levels: [ { level: stage } ]
      neighbours: counted
      restrictions: { lines: 1, order: partial }
      cells_in: { registry: quarry-stages, take: unit }
      boundaries_in: { registry: quarry-stage-bases, take: boundary }
      same_ground_as: [bp-1950]
      crosswalk: table
      meaning: "the stages an invented quarry's survey names in its own section"
      pattern: '^qs:[A-Z][a-z]+$'
      form_note: "`qs:<stage>`"
      example: "qs:Lower"
      establishes: false
      why: "a stage says roughly when, never what"
registry_files:
  - { registry: parishes, file: extracts/parishes.tsv, key: code }
  - { registry: parish-renames, file: extracts/parish-renames.tsv, key: code }
  - { registry: parish-adjacent, file: extracts/parish-adjacent.tsv, key: from }
  - { registry: quarry-stages, file: extracts/quarry-stages.tsv, key: unit }
  - { registry: quarry-stage-bases, file: extracts/quarry-stage-bases.tsv, key: boundary }
"""
_v = read("VOCAB.md")
for _k in ("local_gene", "registry_additions", "registry_files"):
    _v = re.sub(rf"(?m)^{_k}: (\[\]|\{{\}}).*\n", "", _v)
_h, _sep, _rest = _v.partition("\n---\n")
write("VOCAB.md", _h + "\n" + VOCAB_EXTRA + _sep + _rest)
write("extracts/parishes.tsv", "code\tparent\tlevel\tname\tpoint\n"
      "NORTH\t\tdistrict\tthe north\tEPSG:4326;10.2,20.2\nNORTH-1\tNORTH\tparish\tHigh Moor\tEPSG:4326;10.21,20.19\n"
      "NORTH-2\tNORTH\tparish\tLow Moor\tEPSG:4326;10.19,20.22\nSOUTH\t\tdistrict\tthe south\tEPSG:4326;10.0,20.2\n")
write("extracts/parish-renames.tsv", "code\tparent\tlevel\tname\tpoint\tsource\n"
      "NORTH-2\tNORTH\tparish\tLow Moor and Fen\tEPSG:4326;10.19,20.22\tthe council's order of 2026, invented\n")
write("extracts/parish-adjacent.tsv", "from\tto\trel\nNORTH-1\tNORTH-2\tadjacent\n")
write("extracts/quarry-stages.tsv", "unit\tparent\trank\tbegins_ma\tbegins_margin_ma\tends_ma\tends_margin_ma\tname_en\n"
      "Upper\t\tstage\t0.0031\t\t0.0012\t\tthe upper stage\nLower\t\tstage\t0.0052\t0.0001\t0.0031\t\tthe lower stage\n")
write("extracts/quarry-stage-bases.tsv", "boundary\tfixing\tat\tlevel\tbeing\tlocation\tstatus\tcite\n"
      "Upper\tmarked\tEPSG:4326;10.3,20.1\tthe first ash band, 2.35 m up the face\tsection-q\tthe north face\tratified\tthe survey, invented\n"
      "Lower\tdeclared\t\t\t\tdefined by its age\tproposed\tthe survey, invented\n")

# ---------------------------------------------------------------- the beings
write("beans/marker-a.md", bean("marker-a", "material", "soma", "a survey mark set in the moor, invented",
                                placed('system: geographic, openness: elsewhere, at: "EPSG:4326;10.1,20.2@2026.4", mobility: fixed')))
write("beans/stone-d.md", bean("stone-d", "material", "soma", "a boulder, taped from the mark, invented",
                               placed('system: relative, openness: elsewhere, at: "marker-a+3.2,-1.5", mobility: fixed')))
write("beans/stone-e.md", bean("stone-e", "material", "soma", "a boulder with a receiver's coordinate only, invented",
                               placed('system: geographic, openness: elsewhere, at: "EPSG:4326;10.1004,20.2003@2026.4", mobility: fixed')))
write("beans/sapling.md", bean("sapling", "organism", "empsychon", "a rowan sapling, transplanted in March, invented",
                               placed('system: relative, openness: elsewhere, at: "marker-a+40,0", mobility: fixed, during: { of: time, from: "2025-10-01", to: "2026-03-01" }',
                                      'system: relative, openness: elsewhere, at: "marker-a+1,1", mobility: fixed, during: { of: time, from: "2026-03-01" }'),
                               status="provisional"))
write("beans/walker.md", bean("walker", "material", "soma", "a survey pole carried across the moor, invented",
                              placed('system: relative, openness: elsewhere, at: "marker-a+0.5,0.5", mobility: free')))
write("beans/core-e.md", bean("core-e", "material", "soma", "a lake core, dated by radiocarbon, invented", """lines:
  depth: { zero: "the sediment top as the core was taken", toward: "down the core" }
located_at:
  - { system: parish, openness: elsewhere, at: "parish:NORTH-2" }
timing:
  base-laid: { system: ics-chronostrat, at: "ics:Meghalayan", unit: annus }
series:
  ages:
    span: { of: place, in: along, from: "core-e/depth+0", measure: { count: 2, unit: metre } }
    unit: millimetre
    placement: point
    holds:
      - { name: age, system: bp-1950, from: "bp1950:0a", unit: annus, stands_for: point, monotone: increasing }
    rows: |
      at\tage
      100\t850
      700\t2400
      1300\t3930
      1900\t5100
"""))
write("beans/section-q.md", bean("section-q", "material", "soma", "a quarry face, logged bed by bed, invented", """lines:
  height: { zero: "the quarry floor at the foot of the north face", toward: "up the face" }
located_at:
  - { system: geographic, openness: elsewhere, at: "EPSG:4326;10.3,20.1", mobility: fixed }
fixes:
  base-upper: { system: quarry-stage, boundary: Upper, level: "section-q/height+2.35" }
"""))
write("beans/seed-library.md", bean("seed-library", "material", "soma", "an island's seed library, invented", """capabilities:
  share-farmed-crops:
    why: "the island's council forbids moving crop seed off the island, so a pest cannot travel with it"
    permission: forbidden
    code: { scheme: isced-f-2013, code: "0811" }
    within: { system: iso-3166, at: ZZ }
"""))
NAMES = ["marker-a", "stone-d", "stone-e", "sapling", "walker", "core-e", "section-q", "seed-library",
         "parishes", "parish-renames", "parish-adjacent", "quarry-stages", "quarry-stage-bases"]
out = gate()
check("the moor, the core, the parishes, the quarry and the seed library pass the gate", ok(out), out[-3000:])
rc, out = save("an invented moor, a lake core, an island's parishes, a quarry section and a seed library", NAMES, True)
check("...and commit through the hook", rc == 0, out[-2500:])

# ---------------------------------------------------------------- L-1 a position from another being, read at a time
rc, out = tool("bin/dmgeo.py", "stone-d+0,0")
check("L-1 a relative position resolves through the being it is stated from (stone-d, itself from marker-a)",
      rc == 0 and re.search(r"EPSG:4326;10\.0999865\d*,20\.200029\d*@2026\.4", out), out)
rc, out = tool("bin/dmwhere.py", "EPSG:4326;10.1,20.2@2026.4")
check("...the beings nearest the mark are the fixed ones, nearest first; the pole that moves is not among them",
      rc == 0 and re.search(r"sapling ≈ 1\.\d m, stone-d ≈ 3\.5 m, stone-e ≈ 5\d\.\d m", out) and "walker" not in out, out)
rc, out = tool("bin/dmwhere.py", "EPSG:4326;10.1,20.2@2026.4", "--at", "2026-01-15")
check("...read AT a time: in January the sapling stood 40 m away, before it was moved",
      rc == 0 and re.search(r"stone-d ≈ 3\.5 m.*sapling ≈ 40\.0 m", out), out)
refused("...a position from a being the garden does not hold is refused", "beans/stone-d.md",
        '"marker-a+3.2,-1.5"', '"ghost+1,1"', "is stated from ghost, which is no bean of this garden")
refused("...a position from a being placed nowhere is refused", "beans/marker-a.md",
        'system: geographic, openness: elsewhere, at: "EPSG:4326;10.1,20.2@2026.4", mobility: fixed',
        'system: physical, openness: elsewhere, at: "in the peat"', "which holds no geographic position to resolve through")
refused("...two beings stated from each other resolve nowhere", "beans/marker-a.md",
        'system: geographic, openness: elsewhere, at: "EPSG:4326;10.1,20.2@2026.4"',
        'system: relative, openness: elsewhere, at: "stone-d+1,1"', "returns to itself")
refused("...`mobility` is fixed or free", "beans/stone-d.md", "mobility: fixed", "mobility: rooted", "mobility")
rc, out = tool("bin/dmreview.py", "--places")
check("L-1 dmreview --places names the fixed being with a coordinate and no position from another fixed being",
      "PLACES  stone-e:" in out and "PLACES  marker-a:" in out and "PLACES  section-q:" in out
      and "PLACES  stone-d:" not in out and "PLACES  sapling:" not in out and "3 of 5 fixed being(s)" in out, out)

# ---------------------------------------------------------------- L-2 deep time: offsets from datums, cells, spikes
rc, out = tool("bin/dmwhere.py", "bp1950:3.93ka")
check("L-2 bp1950:3.93ka is IN the Meghalayan ⊂ Holocene ⊂ Quaternary …, and the spike that fixes its base is named",
      rc == 0 and re.search(r"Meghalayan\s+age", out) and "Holocene" in out and "Mawmluh Cave" in out
      and "EPSG:4326;25.262222,91.715" in out, out)
rc, out = tool("bin/dmwhere.py", "b2k:4.25ka")
check("...b2k is crosswalked to bp-1950 by COMPUTING from the two datums (4250 − 50 = 4200 a), and an age on a "
      "boundary is in both cells beside it", rc == 0 and "4200 a before the datum of bp-1950" in out
      and "Northgrippian" in out and out.count("ON ITS") == 2, out)
rc, out = tool("bin/dmwhere.py", "ics:Meghalayan")
check("...a cell reads its ancestry and the point that marks its base, with the paper that fixed it",
      rc == 0 and "Holocene ⊂ Quaternary ⊂ Cenozoic ⊂ Phanerozoic" in out and "doi.org" in out, out)
rc, out = tool("bin/dmknowledge.py", "at", "bp1950:3.93ka")
check("...and the finder's `at` is the same reader", rc == 0 and "Mawmluh Cave" in out, out)
refused("L-2 a unit the chart does not have is refused by name", "beans/core-e.md",
        '"ics:Meghalayan"', '"ics:Megalayan"', "Megalayan is no unit of ics-chart")
refused("...a tie that runs backward down the core is refused", "beans/core-e.md",
        "      1300\t3930\n", "      1300\t2100\n", "`age` goes back")
refused("...an age in a symbol the system does not name is refused by its form", "beans/core-e.md",
        '"bp1950:0a"', '"bp1950:0yr"', "bp1950:0yr")

# ---------------------------------------------------------------- L-3 a garden's tabulated places, with an overlay
rc, out = tool("bin/dmwhere.py", "parish:NORTH-2")
check("L-3 a parish reads its district, and the overlay's row wins, with its source",
      rc == 0 and "NORTH" in out and "the council's order of 2026" in out, out)
refused("...an unknown parish is refused", "beans/core-e.md", '"parish:NORTH-2"', '"parish:WEST-9"',
        "WEST-9 is no code of parish-renames or parishes")
refused("...an overlay row with no source is refused", "extracts/parish-renames.tsv",
        "\tthe council's order of 2026, invented\n", "\t\n", "says no `source`")

# ---------------------------------------------------------------- a path: an offset from a datum a host defines
sys.path.insert(0, os.path.join(G, "bin"))
import dmwhere  # noqa: E402
ROOTS = {"tree": {"system": "unix-filesystem", "at": "host-a:/srv/tree"}, "rocks_db": {"system": "unix-filesystem",
                                                                                        "at": "host-a:/srv/rocks"}}
check("HOST the systems a host's datum anchors are read from the law (`datum: host`), never listed by a tool",
      dmwhere.host_bound(G) == {"unix-filesystem", "windows-filesystem", "git-object-graph"}, dmwhere.host_bound(G))
check("...`root:<name>/<rel>` is an offset from the root this host defines",
      dmwhere.on_host("root:tree/a/b", ROOTS) == (os.path.join("/srv/tree", "a/b"), None, None))
check("...`<root>@<object>` is an object reachable from that root, by the same resolver",
      dmwhere.on_host("rocks_db@abc1234", ROOTS) == ("/srv/rocks", "abc1234", None))
check("...`<host>:<path>` is an offset from the host itself: here only on that host, and elsewhere an answer",
      dmwhere.on_host("host-a:/srv", {}, {"host-a"})[0] == "/srv"
      and dmwhere.on_host("host-b:/srv", {}, {"host-a"})[:2] == (None, None))
try:
    dmwhere.on_host("EPSG:4326;10.1,20.2", ROOTS)
    check("...a coordinate is no offset from a host, and is never read as a path on a host called EPSG", False)
except ValueError:
    check("...a coordinate is no offset from a host, and is never read as a path on a host called EPSG", True)
rc, out = tool("bin/dmwhere.py", "root:tree/a")
check("...a root this host does not define is an answer, not a failure (the one spelling crosses filesystems)",
      rc == 0 and "declares no root 'tree'" in out, out)

# ---------------------------------------------------------------- the fixing of a boundary, held at both ends
refused("GSSP a boundary the table says is marked in a being whose `fixes` do not say so is refused",
        "beans/section-q.md", "fixes:\n  base-upper: { system: quarry-stage, boundary: Upper, level: \"section-q/height+2.35\" }\n",
        "", "whose `fixes` do not say so")
refused("...a being that marks a boundary its table DECLARES as a value is refused", "beans/section-q.md",
        "boundary: Upper", "boundary: Lower", "is fixed `declared`")
refused("...a mark along another being's line is refused", "beans/section-q.md",
        '"section-q/height+2.35"', '"core-e/depth+2.35"', "along another being")
refused("...a boundary's fixing is a position of the aspect `fixing`", "extracts/quarry-stage-bases.tsv",
        "Lower\tdeclared", "Lower\tguessed", "no position of the aspect `fixing`")
refused("...a boundary of no cell is refused", "extracts/quarry-stage-bases.tsv",
        "Lower\tdeclared", "Middle\tdeclared", "is the base of no cell")

# ---------------------------------------------------------------- the law's own rows, held
refused("LAW a time system's unit symbol names a unit of duration", "VOCAB.md",
        "      restrictions: { lines: 1, order: partial }\n      cells_in: { registry: quarry-stages",
        "      restrictions: { lines: 1, order: partial }\n      unit_symbols: { m: metre }\n      cells_in: { registry: quarry-stages",
        "unit_symbols.m names 'metre'")
refused("...a datum is `being` or {system, at, sense}", "VOCAB.md",
        "      cells_in: { registry: quarry-stages", "      datum: { system: gregorian-civil, at: \"1950\", sense: under }\n"
        "      cells_in: { registry: quarry-stages", "`datum` is `being`")

refused("...`datum: host` is a place a host defines, never a time", "VOCAB.md",
        "      cells_in: { registry: quarry-stages", "      datum: host\n      cells_in: { registry: quarry-stages",
        "`datum: host` is a place a host defines")

# ---------------------------------------------------------------- where a value may come from (the origin, Body 2)
def with_term(attr):
    """VOCAB.md with one invented local term whose one attribute is `attr`, and what the gate says of it."""
    term = ("local_terms:\n  - term: survey\n    meaning: \"when a section was last walked, invented\"\n"
            "    context_keys: [survey]\n    schema:\n      shape: mapping\n      attrs:\n"
            f"        walked: {{ {attr}, meaning: \"the day it was walked\" }}\n"
            "    merge: { cardinality: single, order: none }\n")
    text = read("VOCAB.md")
    assert "local_terms: []" in text
    write("VOCAB.md", re.sub(r"local_terms: \[\][^\n]*\n", lambda _m: term, text, count=1))
    out = gate()
    restore()
    return out


out = with_term("in: { type: date }, origin: observed")
check("ORIGIN a garden's own date read from the world states `origin: observed`, and the gate takes it", ok(out), out[-1500:])
for name, attr, want in (
        ("...an origin its domain already gives is refused: one is stated only where the domain's is wrong",
         "in: { type: date }, origin: said", "which its domain already gives"),
        ("...an origin that is no row of `origins` is refused", "in: { type: date }, origin: guessed",
         "is not a row of `origins`"),
        ("...an origin the save writes from the clock, on a position that holds neither a day nor a moment",
         "in: prose, origin: stamped", "type it `date` or `moment`")):
    out = with_term(attr)
    check(name, not ok(out) and want in out and "RULE-CHANGE" in out, out[-1500:])

# ---------------------------------------------------------------- L-4 a stance on a code, within a place
refused("L-4 a stance's code is a code of its scheme", "beans/seed-library.md", 'code: "0811"', 'code: "0817"', "'0817' is not a declared isced-f-2013")
refused("...and its place is in its system's form", "beans/seed-library.md", "at: ZZ", "at: Zz", "Zz")

print(f"deeptime: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
