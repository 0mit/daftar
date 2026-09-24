#!/usr/bin/env python3
"""A system knows its own shape (std-vocab 15.0): levels, nesting, neighbours, restrictions; registry links;
planes; and cells that see every attribute."""
import os, re, sys, subprocess, tempfile, shutil
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS = []

def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:700]))
    if not cond:
        FAILS.append(name)

def run(*a, cwd=None):
    return subprocess.run(list(a), capture_output=True, text=True, cwd=cwd)

T = tempfile.mkdtemp(prefix="dmshape-")
G = os.path.join(T, "g")
r = run("sh", os.path.join(ROOT, "seed", "germinate.sh"), G, "--gardener", "keeper", cwd=ROOT)
check("a garden germinates", r.returncode == 0, r.stdout + r.stderr)
v = os.path.join(G, "VOCAB.md"); s = open(v).read()
s = s.replace("\n---", "\nextends_profiles: [network]\n---", 1) if "extends_profiles:" not in s else s.replace("extends_profiles: [", "extends_profiles: [network, ", 1).replace("[network, ]", "[network]")
assert "network" in s.split("\n---")[0]
open(v, "w").write(s)
STD = os.path.join(G, "seed", "std-vocab.md"); ORIG = open(STD).read()

def gate():
    r = run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G)
    return r.stdout + r.stderr

def mutate(old, new):
    assert ORIG.count(old) == 1, old          # a mutation that matches nothing is a bug, not a pass
    open(STD, "w").write(ORIG.replace(old, new))

check("the standard's systems all state a shape the gate accepts", "0 error" in gate(), gate()[-900:])
mutate("    resolves_through: geographic\n    within: [iso-3166]\n    levels:", "    resolves_through: geographic\n    within: [atlantis]\n    levels:")
check("`within` must name a declared system", "`within` names 'atlantis'" in gate(), gate()[-600:])
mutate("    resolves_through: geographic\n    neighbours: metered\n    restrictions: { lines: 1, order: partial }\n    meaning: \"a calendar position", "    resolves_through: geographic\n    within: [unix-epoch]\n    neighbours: metered\n    restrictions: { lines: 1, order: partial }\n    meaning: \"a calendar position")
out = gate()
check("...nesting that does not loop is accepted", "nesting loops" not in out, out[-500:])
mutate("  - system: geographic\n    dimension: place\n", "  - system: geographic\n    dimension: place\n    resolves_through: gregorian-civil\n")
check("`within` and `resolves_through` are walked, so a loop is refused", "nesting loops" in gate(), gate()[-600:])
mutate("    levels: [ { level: year }, { level: month }, { level: day, unit: day }, { level: hour, unit: hour },\n", "    levels: [ { level: year }, { level: month, unit: month }, { level: day, unit: day }, { level: hour, unit: hour },\n")
check("a level is metric only in a real unit — A MONTH IS NOT A MEASURE, and the law can now say why",
      "level 'month' says it is metric in unit 'month'" in gate(), gate()[-600:])
mutate("    transport: tcp\n    within: [ipv4, ipv6]\n    neighbours: counted\n    restrictions: { lines: 1, order: total, ends: bounded }\n",
       "    transport: tcp\n    within: [ipv4, ipv6]\n    neighbours: counted\n    restrictions: { lines: 1, order: none, ends: bounded }\n")
_g = gate()
check("a system NARROWS its aspect and may not widen it", "WIDEN aspect 'place'" in _g and "order none" in _g, _g[-600:])
mutate("    restrictions: { lines: 3, metered: length }", "    restrictions: { lines: 3, metered: enthusiasm }")
check("a system is metered only in a dimension some unit measures", "metered 'enthusiasm' is no dimension" in gate(), gate()[-500:])
mutate("  - { protocol: ospf,  technology: ospf,", "  - { protocol: ospf,  technology: ospff,")
check("a registry LINK is resolved: a protocol names a real entry of the technology catalogue",
      "`technology` names 'ospff'" in gate(), gate()[-600:])
# A LINK MAY DECLARE ONE ROOT (21.0, `rooted`): every facet reaches `legal`. It was a sentence nothing checked.
mutate('  - { facet: technical,  depends_on: [legal],', '  - { facet: technical,  depends_on: [],')
out = gate()
check("a `rooted` link has ONE row that names no link: a second root is refused",
      "VOCAB facets: 2 rows name no `depends_on` (legal, technical)" in out, out[-600:])
mutate('  - { facet: technical,  depends_on: [legal],', '  - { facet: technical,  depends_on: [experience],')
out = gate()
check("...and a row that reaches the root through another passes", "0 error" in out, out[-600:])
assert ORIG.count('rooted: true, why: "a facet depends only') == 1
open(STD, "w").write(ORIG.replace('rooted: true, why: "a facet depends only', 'why: "a facet depends only')
                         .replace('  - { facet: technical,  depends_on: [legal],', '  - { facet: technical,  depends_on: [],'))
out = gate()
check("...while a link that declares no root asks nothing of its roots", "rows name no" not in out, out[-600:])
open(STD, "w").write(ORIG)

sv = yaml.safe_load(re.match(r'^---\n(.*?)\n---', ORIG, re.S).group(1))
tech = {l.split("\t")[0]: l.split("\t") for l in open(os.path.join(ROOT, "seed", "knowledge", "technology.tsv")).read().split("\n")[1:] if l}
isced = {l.split("\t")[0] for l in open(os.path.join(ROOT, "seed", "knowledge", "isced-f-2013.tsv")).read().split("\n")[1:] if l}
check("EVERY protocol is rooted in the tree of knowledge: protocol -> technology -> a UNESCO field that exists",
      all(r.get("technology") in tech and all(c in isced for c in tech[r["technology"]][6].split(";")) for r in sv["net_protocols"]),
      [r["protocol"] for r in sv["net_protocols"] if r.get("technology") not in tech])
rp = [r for r in sv["net_protocols"] if r.get("family")]
check("routing protocols say how they learn and where they apply", len(rp) >= 5 and all(r.get("scope") in ("interior", "exterior") and r.get("plane") == "control" for r in rp))

# ---------------------------------------------------------------- cells see every attribute; planes
BEAN = os.path.join(G, "beans", "box.md")
def ep(extra):
    open(BEAN, "w").write("""---
bean: box
genos: host
title: "a machine"
status: active
summary: "probe"
nature: soma
identity: { status: confirmed, anchors: [ { key: serial, value: "SN-SHAPE-1", class: hardware, establishing: true } ] }
provenance: { src: observed, by: probe, as_of: 2026-09-20 }
owned_by: { legal: { external: "someone" } }
responsibility: { legal: { external: "someone" } }
endpoints:
  - { protocol: dns, system: ipv4, at: "%s", port: 53, observed: 2026-09-20, permission: required, %s }
---

probe.
""" % extra)
    return gate()
out = ep(("127.0.0.1", "exposure: loopback"))
check("a required cleartext surface on LOOPBACK no longer warns — the cell can see `exposure`", "IN BREACH" not in out and "0 error" in out, out[-600:])
out = ep(("203.0.113.10", "exposure: internet"))
check("...and the same surface on the internet still does", "IN BREACH" in out and "exposure:internet" in out, out[-600:])
out = ep(("203.0.113.10", "exposure: internet, confidentiality: encrypted, plane: management"))
check("a MANAGEMENT surface answering on the INTERNET is a finding the law states", "plane:management, exposure:internet but states no admitted_from" in out, out[-700:])
out = ep(("203.0.113.10", "exposure: lan, confidentiality: encrypted, plane: management"))
check("...and on a LAN it is not", "IN BREACH" not in out, out[-500:])
out = ep(("203.0.113.10", "exposure: lan, confidentiality: encrypted, plane: executive"))
check("a plane is a row of the registry", "plane 'executive' is not a declared planes" in out, out[-500:])

shutil.rmtree(T, ignore_errors=True)
print("\nshape: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
