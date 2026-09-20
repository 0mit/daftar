#!/usr/bin/env python3
"""Figures (std-vocab 9.2, "T0"): the square of opposition and the sequence.

Grows a garden with seed/germinate.sh and checks that its gate reads every aspect through the `figures`
registry: a sequence must state each restriction with a value the figure offers, a figure the gate has no
check for is refused, and the cycle check follows the `walk` aspect's `acyclic` restriction rather than a
key named in code.
"""
import os, sys, subprocess, tempfile, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS = []

def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:600]))
    if not cond:
        FAILS.append(name)

def run(*a, cwd=None):
    return subprocess.run(list(a), capture_output=True, text=True, cwd=cwd)

T = tempfile.mkdtemp(prefix="dmfig-")
G = os.path.join(T, "g")
r = run("sh", os.path.join(ROOT, "seed", "germinate.sh"), G, cwd=ROOT)
check("a garden germinates", r.returncode == 0, r.stdout + r.stderr)
VOC = os.path.join(G, "seed", "std-vocab.md")
ORIG = open(VOC).read()

def gate():
    r = run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G)
    return r.stdout + r.stderr

def mutate(old, new):
    assert ORIG.count(old) == 1, old
    open(VOC, "w").write(ORIG.replace(old, new))

out = gate()
check("the standard's figures and aspects pass as declared", "0 error" in out, out[-1500:])

mutate("  - aspect: place\n", "  - aspect: place\n    positions: [{ position: here, complement: there }]\n")
out = gate()
check("a sequence that declares positions is refused", "a sequence declares no `positions`" in out, out[-900:])

mutate("    ends: bounded\n    domain: { systems: place }\n", "    domain: { systems: place }\n")
out = gate()
check("a sequence that leaves a restriction unstated is refused", "must state `ends`" in out, out[-900:])

mutate("    figure: sequence\n    lines: open\n    metered: none\n    order: partial\n    acyclic: true\n    ends: bounded\n    domain: { systems: place }", "    figure: sequence\n    lines: 0\n    metered: none\n    order: partial\n    acyclic: true\n    ends: bounded\n    domain: { systems: place }")
out = gate()
check("a line count that is not one or more is refused", "lines '0' must be a positive integer" in out, out[-900:])

mutate("    metered: time\n", "    metered: weight\n")
out = gate()
check("a measure that is not a unit dimension is refused", "metered 'weight' is neither" in out, out[-900:])

open(VOC, "w").write(ORIG.replace("    figure: sequence\n    lines: 1\n    metered: time\n", "    figure: spiral\n    lines: 1\n    metered: time\n", 1))
out = gate()
check("a figure the registry does not declare is refused", "figure 'spiral' is not declared in `figures`" in out, out[-900:])

open(VOC, "w").write(ORIG.replace("  - figure: sequence\n", "  - figure: spiral\n    requires: []\n  - figure: sequence\n", 1)
                     .replace("    figure: sequence\n    lines: 1\n    metered: time\n", "    figure: spiral\n    lines: 1\n    metered: time\n", 1))
out = gate()
check("a declared figure the gate has no check for is refused, not passed unexamined", "the gate has no check for figure 'spiral'" in out, out[-900:])

# the cycle check follows the walk aspect's restriction
open(VOC, "w").write(ORIG)
def bean(name, body):
    open(os.path.join(G, "beans", name + ".md"), "w").write("---\n" + body + "---\n\n" + name + "\n")
OWN = 'owned_by: { legal: { owner: { bean: someone } } }\nresponsibility: { legal: { holder: { bean: someone } } }\n'
bean("someone", 'bean: someone\nkind: person\ntitle: "a person"\nstatus: active\nsummary: "p"\nnature: living\n'
     'identity: { status: confirmed, anchors: [ { key: email, value: "a@example.org", class: logical, establishing: true } ] }\n'
     'provenance: { src: asserted-by-human, by: t, as_of: 2026-01-01 }\nowned_by: { legal: { crown: love } }\nresponsibility: { legal: { self: true } }\n')
for a, b in (("part-a", "part-b"), ("part-b", "part-a")):
    bean(a, f'bean: {a}\nkind: product\ntitle: "{a}"\nstatus: active\nsummary: "x"\nnature: metaphysical\n'
         f'identity: {{ status: confirmed, anchors: [ {{ key: product_id, value: "product:{a}", class: logical, establishing: true }} ] }}\n'
         f'provenance: {{ src: asserted-by-human, by: t, as_of: 2026-01-01 }}\n' + OWN + f'part_of: {{ bean: {b} }}\n')
out = gate()
check("a cycle on a walked relation is refused while `walk` says acyclic", "cycle" in out.lower() and "0 error" not in out, out[-900:])

mutate("    order: partial\n    acyclic: true\n    ends: open\n    term_key: dag",
       "    order: partial\n    acyclic: false\n    ends: open\n    term_key: dag")
out = gate()
check("the same cycle is not refused once `walk` declares acyclic: false — the restriction is data, not code",
      "cycle" not in out.lower(), out[-900:])

open(VOC, "w").write(ORIG)
r = run(sys.executable, os.path.join(G, "bin", "dmrules.py"), cwd=G)
check("dmrules shows the sequences and what walks them",
      "time         sequence" in r.stdout and "walked by:" in r.stdout and "on the 'walk' sequence" in r.stdout, r.stdout[-1500:] + r.stderr)

# ---- T4 (10.1): routines. `steps` is a walk on the `routine` sequence, with CLOSED neighbourhoods.
open(VOC, "w").write(ORIG)
for f in ("part-a", "part-b"):
    os.remove(os.path.join(G, "beans", f + ".md"))
def routine(steps_yaml):
    open(os.path.join(G, "mappings", "rehearse.md"), "w").write(
        "---\nmapping: rehearse\nkind: procedure\nsummary: \"a rehearsal with a retry\"\nsteps:\n" + steps_yaml + "---\nA routine.\n")
    return gate()
os.makedirs(os.path.join(G, "mappings"), exist_ok=True)
GOOD = ("  - { id: copy, do: \"copy the database\", next: [ { to: verify } ] }\n"
        "  - { id: verify, do: \"compare row counts\", next: [ { to: done, when: \"counts match\" }, { to: copy, when: \"they differ: copy again\" } ] }\n"
        "  - { id: done, do: \"report\" }\n")
out = routine(GOOD)
check("T4: a routine with a branch and a LOOP passes — `routine` is not acyclic", "0 error" in out, out[-900:])
out = routine("  - \"copy\"\n  - \"verify\"\n")
check("T4: prose steps stay legal, read in list order", "0 error" in out, out[-900:])
out = routine(GOOD.replace("{ to: done, when", "{ to: finished, when"))
check("T4: a branch to a step that does not exist is refused", "names no step of this routine" in out, out[-900:])
out = routine(GOOD + "  - { id: orphan, do: \"never reached\" }\n")
check("T4: a step nothing reaches is refused", "orphan: no step reaches it" in out, out[-900:])
out = routine(GOOD.replace("{ to: done, when: \"counts match\" }", "{ to: done }"))
check("T4: a branch that does not say when it is taken is refused", "names no `when`" in out, out[-900:])
out = routine(GOOD.replace("  - { id: done, do: \"report\" }\n", "  - { id: done, do: \"report\", next: [ { to: copy } ] }\n"))
check("T4: a routine that never ends is refused", "no step ends the routine" in out, out[-900:])
out = routine(GOOD + "  - \"a prose line\"\n")
check("T4: prose and step entries mixed in one routine are refused", "mixes prose lines and step entries" in out, out[-900:])
open(VOC, "w").write(ORIG.replace("    order: partial\n    acyclic: false\n    ends: bounded\n", "    order: partial\n    acyclic: true\n    ends: bounded\n", 1))
out = routine(GOOD)
check("T4: the same loop is refused once `routine` declares acyclic — the restriction is data", "loops, and 'routine' declares acyclic" in out, out[-900:])
open(VOC, "w").write(ORIG)

# ---------------------------------------------------------------- the schema language describes itself (11.3)
# Four constructs were interpreted by the gate and declared nowhere. The check runs both ways on purpose:
# the standard as shipped must be silent, and a construct one letter short must be NAMED, because until 11.3
# it passed while enforcing nothing.
out = gate()
check("11.3: every construct the standard's terms use is declared in schema_language",
      "is not declared in schema_language" not in out, out[-900:])
mutate("    context_keys: [\"capabilities\"]\n    schema:\n      shape: open_map_of_entries\n      key_form: kebab\n", "    context_keys: [\"capabilities\"]\n    schema:\n      shape: open_map_of_entries\n      key_forms: kebab\n")
out = gate()
check("11.3: a misspelt construct is named instead of silently enforcing nothing",
      "capabilities: schema key `key_forms` is not declared in schema_language" in out, out[-900:])
check("12.0: ...as an ERROR — a rule that enforces nothing is refused, not remarked on", "ERROR VOCAB capabilities: schema key" in out, out[-600:])
mutate('  path:                 "<dotted path>', '  path_:                "<dotted path>')
out = gate()
check("11.3: withdrawing a declaration the terms rely on is noticed too",
      "schema key `path` is not declared in schema_language" in out, out[-900:])
open(VOC, "w").write(ORIG)

# ---------------------------------------------------------------- structure before prose (12.0)
BEAN = os.path.join(G, "beans", "probe-host.md")
def bean(extra):
    open(BEAN, "w").write("""---
bean: probe-host
kind: host
title: "probe"
status: active
summary: "probe"
nature: physical
identity:
  status: confirmed
  anchors:
    - { key: serial, value: "SN-PROBE-1", class: hardware, establishing: true }
provenance: { src: observed, by: probe, as_of: 2026-09-20 }
owned_by: { legal: { external: "a provider" } }
responsibility: { legal: { external: "a provider" } }
""" + extra + "---\n\nprobe.\n")
    return gate()
out = bean("capabilities:\n  a-thing: { permission: forbidden, why: \"because\", note_to_self_this_matters: \"a sentence as a key\" }\n")
check("12.0: an attribute the term does not declare is refused — a sentence may not pose as a key",
      "carries `note_to_self_this_matters`, which the term `capabilities` does not declare" in out, out[-900:])
out = bean("capabilities:\n  a-thing: { permission: forbidden, why: \"because\", feasibility_why: \"x\", provenance: { src: inferred, by: p, as_of: 2026-09-20 } }\n")
check("12.0: declared prose attributes pass, and any entry may carry its own provenance",
      "does not declare" not in out, out[-900:])
out = bean("owns:\n  anything_at_all: \"owns is a free container by declaration\"\n")
check("12.0: a term that declares no attribute stays a free container", "does not declare" not in out, out[-900:])
os.remove(BEAN)

# ---------------------------------------------------------------- the attribute form (S1)
# The gate translates every term's schema into ONE record per attribute and interprets only that. These pin the
# form itself; that it reproduces the old gate byte for byte is proved in a garden, by test/diffgate.py.
import importlib.util, io, contextlib
_vp = os.path.join(G, "VOCAB.md"); _vs = open(_vp).read()
if "extends_profiles:" in _vs:
    _vs = (_vs.replace("extends_profiles: []", "extends_profiles: [network, domain]") if "extends_profiles: []" in _vs
           else _vs.replace("extends_profiles: [", "extends_profiles: [network, domain, ", 1))
else:
    _vs = _vs.replace("\n---", "\nextends_profiles: [network, domain]\n---", 1)
open(_vp, "w").write(_vs)
_cwd = os.getcwd(); os.chdir(G)
_spec = importlib.util.spec_from_file_location("dmcheck_probe", os.path.join(G, "bin", "dmcheck.py"))
_gate = importlib.util.module_from_spec(_spec)
_argv, sys.argv = sys.argv, ["dmcheck.py", "--all"]
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    try:
        _spec.loader.exec_module(_gate)
    except SystemExit:
        pass
sys.argv = _argv; os.chdir(_cwd)
_f = _gate.attribute_form("endpoints", _gate.SCHEMAS["endpoints"])
check("S1: one record per attribute — `at` says it is required and takes its form from the system beside it",
      _f["attrs"]["at"].get("required") is True and _f["attrs"]["at"]["system_from"]["keyed_by"] == "system"
      and "meaning" in _f["attrs"]["at"], str(_f["attrs"].get("at"))[:300])
check("S1: an aspect position is an attribute like any other", _f["attrs"]["permission"]["aspect"]["aspect"] == "capability")
check("S1: cross_aspect became cells", [c["origin"] for c in _f["cells"]] == ["in_breach"] * 3, str([c["when"] for c in _f["cells"]])[:300])
_f = _gate.attribute_form("analysis_cache", _gate.SCHEMAS["analysis_cache"])
check("S1: ...and so did entry_required_if and entry_expect_if — three constructs, one idea",
      sorted(c["origin"] for c in _f["cells"]) == ["expect_if", "required_if"], str(_f["cells"])[:300])
_f = _gate.attribute_form("registration", _gate.SCHEMAS["registration"])
check("S1: a mapping's own attributes take the same form, scoped to the value itself",
      _f["scope"] == "self" and _f["attrs"]["expires"].get("type") == "date" and _f["attrs"]["expires"].get("required") is True)
_untyped = sorted(n for n, a in _gate.attribute_form("endpoints", _gate.SCHEMAS["endpoints"])["attrs"].items()
                  if set(a) <= {"meaning", "scope"})
check("S1: the form makes an UNTYPED attribute visible — `via_link` has a meaning and no rule (`port` had none until 14.0)",
      _untyped == ["via_link"], str(_untyped))

shutil.rmtree(T, ignore_errors=True)
print("\nfigures: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
