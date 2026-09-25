#!/usr/bin/env python3
"""The one reckoner (RECKON, 24.0; N1, N2, N9, S7, D38, step 10): a reading written as steps of the law's closed list of
operations, read each time by bin/dmreckon.py and never stored; a series read through it; a reading pinned to the commit
it was read at; an allowance counted within a window; a weighing whose weights are read and never written.

Grows a garden and commits invented fixtures through its hook: three candles burning down, a candle maker's book of
readings, the burning of pentacosane as a walk, a studio pass, a choir's weighing of its programme, and a wick
mechanism that is a test's and no one's knowledge.
"""
import io, os, re, shutil, subprocess, sys, tempfile, tokenize

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
FAILS = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:900]))
    if not cond:
        FAILS.append(name)


def run(*a, cwd=None):
    return subprocess.run(list(a), capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd)


T = tempfile.mkdtemp(prefix="dmreckon-")
G = os.path.join(T, "g")
r = run("sh", os.path.join(ROOT, "seed", "germinate.sh"), G, "--gardener", "keeper", cwd=ROOT)
check("a garden germinates from the release, and the law with RECKON's rows loads", r.returncode == 0 and "0 error" in r.stdout,
      r.stdout + r.stderr)


def write(rel, text):
    p = os.path.join(G, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def gate():
    r = run(PY, "bin/dmcheck.py", "--all", cwd=G)
    return r.stdout + r.stderr


def ok(out):
    return "0 error(s)" in out and "Traceback" not in out


def save(what, names, rule_change=False):
    body = "- action: " + ("RULE-CHANGE (VOCAB.md) " if rule_change else "") + " ".join(f"[[{n}]]" for n in names)
    r = run(PY, "bin/dmsave.py", "keeper (test)", what, "--body", body, cwd=G)
    return r.returncode, r.stdout + r.stderr


def restore():
    """Every file as the last commit holds it: a fixture a check rewrote is put back, stamped as it was saved."""
    run("git", "reset", "-q", "--hard", cwd=G)
    run("git", "clean", "-qfd", cwd=G)


def reckon(*a):
    r = run(PY, "bin/dmreckon.py", *a, cwd=G)
    return r.returncode, r.stdout + r.stderr


# ============================================================================ the fixtures, invented
T_ = "\t"
OWN = "owned_by: { legal: { owner: { bean: keeper } } }\nresponsibility: { legal: { holder: { bean: keeper } } }\n"


def candle(id, heights, u="0.2"):
    rows = "".join(f"      {h}\n" for h in ("height",) + tuple(heights))
    return f"""---
bean: {id}
genos: material
title: "{id} — a candle"
status: active
summary: "An invented pillar candle, its height read each hour as it burns."
nature: soma
identity:
  status: confirmed
  anchors:
    - {{ key: serial, value: "{id.upper()}-0001", class: hardware, establishing: true }}
provenance: {{ src: observed, by: "keeper", as_of: now }}
{OWN}series:
  burn:
    grid: {{ of: time, in: gregorian-civil, every: {{ count: 1, unit: hour }}, from: "2026-11-01 18:00+00:00" }}
    unit: hour
    holds:
      - {{ name: height, quantity: length, unit: millimetre, stands_for: point, between: linear, u: {{ count: "{u}", unit: millimetre }} }}
    rows: |
{rows}---
An invented candle.
"""


def worn(c):
    return f"""      - {{ id: first-{c}, op: window, series: "{c}:series.burn", by: first }}
      - {{ id: now-{c}, op: window, series: "{c}:series.burn", by: last }}
      - {{ id: gone-{c}, op: difference, of: first-{c}, with: now-{c} }}
      - {{ id: worn-{c}, op: divide, of: gone-{c}, with: first-{c} }}
"""


def book(extra_selections="", extra=""):
    return f"""---
bean: chandlery
genos: org
title: "the chandlery's book"
status: active
summary: "an invented candle maker's book of the readings it takes of its candles"
nature: lekton
{OWN}identity: {{ status: provisional, anchors: [] }}
provenance: {{ src: asserted-by-human, by: keeper, as_of: now }}
selections:
  alike:
    what: "whether candle a and candle b have burnt down by the same share, within one hundredth"
    steps:
{worn("candle-a")}{worn("candle-b")}      - {{ id: same, op: compare, of: worn-candle-a, with: worn-candle-b, is: equal, band: {{ count: "0.01", unit: one }} }}
  worn-a:
    what: "the share of candle a burnt away"
    steps:
{worn("candle-a")}  unlike:
    what: "whether candle a and candle c have burnt down by the same share"
    steps:
{worn("candle-a")}{worn("candle-c")}      - {{ id: same, op: compare, of: worn-candle-a, with: worn-candle-c, is: equal, band: {{ count: "0.01", unit: one }} }}
  burns-clean:
    what: "whether the burning of the candle's wax, as the walk writes it, conserves every element"
    steps:
      - {{ id: balanced, op: conservation, walk: "walk-burning:steps", scheme: substances }}
  slope-a:
    what: "how fast candle a burns down, fitted"
    steps:
      - {{ id: slope, op: trend, series: "candle-a:series.burn" }}
  rate-a:
    what: "how fast candle a burnt in its second and third hour"
    steps:
      - {{ id: rate, op: rate, series: "candle-a:series.burn", from: "2026-11-01 19:00+00:00", to: "2026-11-01 21:00+00:00" }}
  halfway-a:
    what: "candle a's height half an hour into its second hour"
    steps:
      - {{ id: h, op: at, series: "candle-a:series.burn", position: "2026-11-01 19:30+00:00" }}
  wick:
    what: "the burn rate of a wick, by the one mechanism valid for it"
    inputs:
      - {{ name: wick, origin: given, quantity: length }}
    steps:
      - {{ id: rate, op: choose, computes: burn-rate }}
  evenings:
    what: "the candles lit, grouped by the day they were lit on in Auckland"
    zone: Pacific/Auckland
    steps:
      - {{ id: lit, op: select, entries: "lightings.*" }}
      - {{ id: by-day, op: group, of: lit, path: at, level: day, system: gregory }}
      - {{ id: per-day, op: count, of: by-day }}
{extra_selections}lightings:
  first: {{ at: "2026-04-04T10:00Z" }}
  second: {{ at: "2026-04-04T13:30Z" }}
  third: {{ at: "2026-04-04T14:30Z" }}
{extra}---
The chandlery's book.
"""


LIGHTINGS_TERM = """  - term: lightings
    meaning: "when an invented chandlery lit a candle"
    context_keys: [lightings]
    schema:
      shape: open_map_of_entries
      attrs:
        at:  { required: true, in: { type: moment }, meaning: "the moment it was lit" }
        pin: { in: any, meaning: "the commit and moment a reading of it was read at (`pin_form`)" }
    merge: { cardinality: multi, order: by-key }
  - term: visits
    meaning: "the days an invented studio pass was used on"
    context_keys: [visits]
    schema:
      shape: open_map_of_entries
      attrs:
        day: { required: true, in: { type: date }, meaning: "the day" }
    merge: { cardinality: multi, order: by-key }
"""
WICK = """registry_additions:
  mechanisms:
    - mechanism: wick-demo
      computes: { property: { scheme: technology, code: burn-rate }, quantity: length, unit: millimetre }
      inputs: [ { name: wick, quantity: length, unit: millimetre } ]
      steps: [ { id: rate, op: multiply, of: wick, count: 2 } ]
      valid: { ranges: [ { input: wick, extent: { from: { count: 1, unit: millimetre }, to: { count: 5, unit: millimetre } } } ] }
      residual: { sigma: { count: "0.1", unit: one }, form: relative, persists: unknown }
      source: { cite: "a test's invention", locator: "test/reckon.py" }
      terms: "none: invented"
"""
BURNING = """---
mapping: walk-burning
kind: procedure
summary: "An invented walk: a candle's wax burnt in air."
steps:
  - id: burn
    do: "pentacosane burns in oxygen to carbon dioxide and water"
    takes: [ { scheme: substances, code: pentacosane, amount: { count: 1, unit: item } }, { scheme: substances, code: dioxygen, amount: { count: 38, unit: item } } ]
    gives: [ { scheme: substances, code: carbon-dioxide, amount: { count: 25, unit: item } }, { scheme: substances, code: water, amount: { count: %s, unit: item } } ]
    final: true
---
The burning of wax, invented.
"""
VOCAB_EXTRA = """local_gene:
  - { genos: material, of_nature: soma, meaning: "a body of matter kept and used: a candle" }
local_terms:
""" + LIGHTINGS_TERM + WICK
_v = open(os.path.join(G, "VOCAB.md"), encoding="utf-8").read()
for _k in ("local_gene", "local_terms", "registry_additions"):
    _v = re.sub(rf"(?m)^{_k}: (\[\]|\{{\}}).*\n", "", _v)
_h, _sep, _rest = _v.partition("\n---\n")
write("VOCAB.md", _h + "\n" + VOCAB_EXTRA + _sep + _rest)

A = ("200", "190", "180", "170", "160", "150")
B = ("240", "228", "216", "205", "193", "181")
C = ("200", "180", "160", "140", "120", "100")
write("beans/candle-a.md", candle("candle-a", A))
write("beans/candle-b.md", candle("candle-b", B))
write("beans/candle-c.md", candle("candle-c", C))
write("beans/chandlery.md", book())
write("mappings/walk-burning.md", BURNING % 26)
out = gate()
check("the fixtures — three candles, a book of readings, a walk that burns wax, a mechanism of a test's — pass the gate",
      ok(out), out[-1500:])
rc, out = save("the chandlery's candles and readings", ["candle-a", "candle-b", "candle-c", "chandlery", "walk-burning"], True)
check("...and commit through the hook", rc == 0, out[-1200:])
C1 = run("git", "rev-parse", "--short", "HEAD", cwd=G).stdout.strip()

# ============================================================================ R-1: the reckoner
rc, out = reckon("chandlery:worn-a")
check("candle a is a quarter burnt: (200 − 150) / 200, with its u and its lines",
      rc == 0 and re.search(r"= 0\.250\d* \(u 0\.00\d+\)", out) and "step gone-candle-a (difference)" in out
      and "candle-a:burn" in out, out)
rc, out = reckon("chandlery:worn-a", "--exact")
check("...exactly 1/4 when asked", rc == 0 and "= 0.25" in out, out)
rc, out = reckon("chandlery:alike")
check("two candles burnt within a hundredth of each other, the difference resolved by its u: TRUE", rc == 0 and "= true" in out, out)
rc, out = reckon("chandlery:unlike")
check("a candle burnt twice as far is not alike: FALSE", rc == 0 and "= false" in out, out)
write("beans/candle-a.md", candle("candle-a", A, u="1"))
write("beans/candle-b.md", candle("candle-b", B, u="1"))
rc, out = reckon("chandlery:alike")
check("...and read with a u too big to resolve the band: NOT KNOWN, said why, never rounded to either",
      rc == 0 and "= NOT KNOWN" in out and "cannot resolve it" in out, out)
restore()

# the grammar, judged by the gate
def refused_sel(name, steps, *needles):
    write("beans/chandlery.md", book(extra_selections=f"  bad:\n    what: \"a reading that is refused\"\n    steps:\n{steps}"))
    out = gate()
    check(name, not ok(out) and all(n in out for n in needles), out[-900:])


refused_sel("a step with `op: eval` is refused: the list is closed, and no string is evaluated",
            "      - { id: x, op: eval, of: \"1 + 1\" }\n", "`op: eval` is not an operation of the law")
refused_sel("a step naming a LATER step is refused: a reading never loops",
            "      - { id: n, op: count, of: later }\n      - { id: later, op: select, genos: person }\n",
            "`of: later` names no earlier step")
refused_sel("a key an operation does not take is refused, naming what it takes",
            "      - { id: n, op: select, genos: person, formula: \"x*2\" }\n", "`formula` is not what `select` takes")
refused_sel("a comparator the law does not list is refused",
            "      - { id: n, op: select, genos: person, where: [ { path: title, like: \"%a%\" } ] }\n",
            "names exactly one comparator of the law")
refused_sel("a group by a calendar level with no zone is refused",
            "      - { id: l, op: select, entries: \"lightings.*\" }\n      - { id: g, op: group, of: l, path: at, level: day }\n",
            "states `zone`")
restore()

rc, out = reckon("chandlery:evenings")
check("lightings grouped by day IN AUCKLAND: 10:00Z is the 4th there, 13:30Z and 14:30Z both the 5th, across the end of "
      "daylight time", rc == 0 and "2026-04-04: 1 item" in out and "2026-04-05: 2 item" in out, out)

# conservation (D38)
rc, out = reckon("chandlery:burns-clean")
check("C25H52 + 38 O2 → 25 CO2 + 26 H2O conserves every element and the charge", rc == 0 and "= true" in out, out)
write("mappings/walk-burning.md", BURNING % 25)
rc, out = reckon("chandlery:burns-clean")
check("...and with 25 water it does not, naming the element: hydrogen 52 in, 50 out",
      rc == 0 and "= false" in out and "H 52 in, 50 out" in out, out)
restore()

# the mechanism chosen by validity
rc, out = reckon("chandlery:wick", "--input", "wick=3 millimetre")
check("a mechanism is chosen where its `valid` covers the case: a 3 mm wick, 6 mm with a relative u of a tenth",
      rc == 0 and "chosen: wick-demo" in out and "= 6.0 millimetre (u 0.6 millimetre)" in out, out)
rc, out = reckon("chandlery:wick", "--input", "wick=9 millimetre")
check("...and refused for a case outside it, saying why, never guessed",
      rc != 0 and "no mechanism is valid" in out and "outside the range" in out, out)
rc, out = reckon("chandlery:wick")
check("a reading whose input is not given is refused, naming it", rc != 0 and "the input 'wick'" in out, out)

# ============================================================================ S7: a series read through the one list
rc, out = reckon("chandlery:halfway-a")
check("`at` reads between two rows as the channel says: 185 mm half an hour into the second hour",
      rc == 0 and "= 185.0 millimetre" in out and "linear, between two rows" in out, out)
rc, out = reckon("chandlery:rate-a")
rc, out = reckon("chandlery:rate-a", "--exact")
check("`rate`: −10 mm an hour over the second and third hours, in the law's coherent unit: −1/360000 m/s",
      rc == 0 and "= -1/360000 metre-per-second" in out, out)
rc, out = reckon("chandlery:slope-a")
check("`trend`: a fitted slope, marked ≈, never extrapolated", rc == 0 and "≈" in out, out)

# ============================================================================ the ad-hoc reading (N1)
write("adhoc.yaml", "what: \"how many candles there are\"\nsteps:\n  - { id: c, op: select, genos: material }\n"
                    "  - { id: n, op: count, of: c }\n")
rc, out = reckon("--ad-hoc", "adhoc.yaml")
check("an ad-hoc reading nobody committed is read, and said to be one: three candles",
      rc == 0 and "ad-hoc" in out and "= 3 item" in out, out)
write("adhoc.yaml", "steps:\n  - { id: c, op: eval, of: \"__import__('os')\" }\n")
rc, out = reckon("--ad-hoc", "adhoc.yaml")
check("...and an ad-hoc `eval` is refused before anything is read", rc != 0 and "not an operation of the law" in out, out)
os.remove(os.path.join(G, "adhoc.yaml"))

# ============================================================================ R-2: a reading pinned to its commit
write("beans/candle-a.md", candle("candle-a", A[:-1] + ("140",)))
rc, out = save("candle a read again", ["candle-a"])
check("a later reading of candle a commits", rc == 0, out[-600:])
rc, now = reckon("chandlery:worn-a", "--exact")
rc2, then = reckon("chandlery:worn-a", "--exact", "--at", C1, "--moment", "2026-01-02 09:00+00:00")
check("a reading pinned to the commit it was read at is unchanged by a later edit: 1/4 then, 3/10 now",
      rc == 0 and rc2 == 0 and "= 0.25" in then and "= 0.3" in now and f"read at {C1}" in then, then + now)
write("beans/chandlery.md", open(os.path.join(G, "beans", "chandlery.md"), encoding="utf-8").read().replace('  first: { at: "2026-04-04T10:00Z" }',
                                                     f'  first: {{ at: "2026-04-04T10:00Z", pin: {{ commit: \"{C1}\", at: "2026-01-02 09:00+00:00" }} }}'))
out = gate()
check("a pin naming a commit the garden has passes", ok(out), out[-900:])
restore()
write("beans/chandlery.md", open(os.path.join(G, "beans", "chandlery.md"), encoding="utf-8").read().replace('  first: { at: "2026-04-04T10:00Z" }',
                                                     '  first: { at: "2026-04-04T10:00Z", pin: { commit: deadbee, at: "2026-01-02 09:00+00:00" } }'))
assert "deadbee" in open(os.path.join(G, "beans", "chandlery.md"), encoding="utf-8").read(), "the pin fixture did not land"
out = gate()
check("a pin naming a commit that is not an ancestor of HEAD is refused by name",
      not ok(out) and "deadbee is not an ancestor of HEAD" in out, out[-900:])
restore()

# ============================================================================ R-3: an allowance within a window (N9)
PASS = """---
bean: studio-pass
genos: org
title: "studio-pass — twelve visits within any thirty days"
status: active
summary: "An invented pottery studio's pass: twelve visits within any thirty days."
nature: lekton
""" + OWN + """identity: { status: provisional, anchors: [] }
provenance: { src: asserted-by-human, by: keeper, as_of: now }
visits:
""" + "".join(f"  v{i:02d}: {{ day: 2026-10-{i + 1:02d} }}\n" for i in range(1, 14)) + """selections:
  used:
    what: "the visits within the thirty days that end on the day asked"
    inputs:
      - { name: day, origin: given, type: date }
    steps:
      - { id: all, op: select, entries: "visits.*" }
      - { id: used, op: used-within, of: all, path: day, within: { of: time, measure: { count: 30, unit: day } }, at: { input: day } }
---
An invented studio pass.
"""
write("beans/studio-pass.md", PASS)
out = gate()
check("a pass with thirteen visits and a reading of its use passes the gate", ok(out), out[-900:])
rc, out = reckon("studio-pass:used", "--input", "day=2026-10-30")
check("the thirteenth visit within thirty days is counted: 13 items used of an allowance of 12",
      rc == 0 and "= 13 item" in out and "2026-10-01 to 2026-10-30" in out, out)
rc, out = reckon("studio-pass:used", "--input", "day=2026-11-10")
check("...and a window that has slid on holds fewer", rc == 0 and "= 3 item" in out, out)

# ============================================================================ R-4: a weighing (step 10)
def choir(pairs, why=""):
    return """---
bean: choir-weighing
genos: org
title: "the choir's weighing"
status: active
summary: "an invented choir's weighing of what counts in choosing its programme"
nature: lekton
""" + OWN + """identity: { status: provisional, anchors: [] }
provenance: { src: asserted-by-human, by: keeper, as_of: now }
weighings:
  programme:
    for: improvements
    judge: keeper
    criteria:
      - { name: singable, what: "the choir can learn it in a term" }
      - { name: loved, what: "the audience knows and loves it" }
      - { name: new, what: "it is new to the choir" }
      - { name: cheap, what: "its scores cost little" }
    pairwise:
""" + "".join(f"      - {{ a: {a}, b: {b}, judged: \"{j}\" }}\n" for a, b, j in pairs) + why + """---
An invented choir.
"""


GOOD = (("singable", "loved", "2"), ("singable", "new", "3"), ("singable", "cheap", "5"),
        ("loved", "new", "2"), ("loved", "cheap", "3"), ("new", "cheap", "2"))
write("beans/choir-weighing.md", choir(GOOD))
out = gate()
check("a choir's weighing of four criteria, judged consistently, passes", ok(out), out[-900:])
rc, out = reckon("weigh", "choir-weighing:programme")
cr = re.search(r"CR ≈ ([0-9.]+)", out)
check("`weigh` prints each weight marked ≈ and a consistency ratio of about 0.02, and stores none",
      rc == 0 and cr and float(cr.group(1)) < 0.05 and "singable: ≈ 0." in out and "never stored" in out, out)
BAD = GOOD[:1] + (("singable", "new", "1/5"),) + GOOD[2:]
write("beans/choir-weighing.md", choir(BAD))
out = gate()
check("a reversed judgment makes it inconsistent (CR above 0.10), and it is refused without `why_inconsistent`",
      not ok(out) and "above 0.10" in out, out[-900:])
write("beans/choir-weighing.md", choir(BAD, "    why_inconsistent: \"the choir truly disagrees with itself, and says so\"\n"))
out = gate()
check("...and passes with the reason it stands", ok(out), out[-900:])
write("beans/choir-weighing.md", choir(GOOD[:-1]))
out = gate()
check("a pair left unjudged is refused, naming it", not ok(out) and "not judged: (new, cheap)" in out, out[-900:])

# ============================================================================ the ordering keys (the law's own readings)
write("items.tsv", "item\tweight\tfailed\tseconds\nslow-suite\t1\t1\t240\nquick-suite\t1\t1\t20\nnever-fails\t1\t0\t5\n")
rc, out = reckon("order", "tests", "items.tsv")
check("`order tests` puts the quick suite that failed first, the one that never failed last",
      rc == 0 and out.split("\n")[0].startswith("quick-suite") and out.strip().split("\n")[-1].startswith("never-fails"), out)
os.remove(os.path.join(G, "items.tsv"))

# ============================================================================ D41: the release's own weighing of its suites
sys.path.insert(0, os.path.join(ROOT, "bin"))
import dmparse, dmreckon  # noqa: E402
_w = dmparse.loads(open(os.path.join(ROOT, "test", "weighing.yaml"), encoding="utf-8").read())
_c, _wt, _l, _ci, _cr = dmreckon.weights(_w)
check("test/weighing.yaml is a weighing in the term's form, every pair judged once, consistent (CR under 0.10)",
      not dmreckon.check_weighing("test/weighing.yaml", _w) and _cr < dmreckon.Fraction(1, 10) and _w.get("for") == "tests",
      dmreckon.check_weighing("test/weighing.yaml", _w))

# ============================================================================ the source
def floats_in(text):
    found = []
    for t in tokenize.generate_tokens(io.StringIO(text).readline):
        if t.type == tokenize.NUMBER and not t.string.lower().startswith(("0x", "0o", "0b")) and re.search(r"[.eEjJ]", t.string):
            found.append(f"line {t.start[0]}: float literal {t.string}")
        elif t.type == tokenize.NAME and t.string in ("float", "eval", "exec"):
            found.append(f"line {t.start[0]}: {t.string}")
    return found


src = open(os.path.join(ROOT, "bin", "dmreckon.py"), encoding="utf-8").read()
_f = floats_in(src)
check("bin/dmreckon.py holds no float literal, no float, and no eval or exec: every count exact, no string evaluated", not _f, _f)
ops = re.findall(r"(?m)^  - \{ op: ([a-z-]+),|^  - op: ([a-z-]+)$", open(os.path.join(ROOT, "seed", "std-vocab.md"), encoding="utf-8").read())
ops = {a or b for a, b in ops}
missing = [o for o in ops if f"def op_{o.replace('-', '_')}(" not in src]
check("every operation of the law has its one reader in bin/dmreckon.py, and none more", len(ops) > 40 and not missing
      and len(re.findall(r"(?m)^    def op_", src)) == len(ops), (len(ops), missing))

shutil.rmtree(T, ignore_errors=True)
print(f"\nreckon: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
