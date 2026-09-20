#!/usr/bin/env python3
"""Addresses and ports are places (std-vocab 14.0).

Grows a garden, opts into the `network` profile and checks that an endpoint's address and port are positions in
PLACE systems read from the registry: the form a port must take, that tcp and udp are separate port spaces, that
a socket path is an endpoint, that a system outside `place` is refused, and that the transport is read from the
protocol's row unless the entry states it.
"""
import os, sys, subprocess, tempfile, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS = []

def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:700]))
    if not cond:
        FAILS.append(name)

def run(*a, cwd=None):
    return subprocess.run(list(a), capture_output=True, text=True, cwd=cwd)

T = tempfile.mkdtemp(prefix="dmpos-")
G = os.path.join(T, "g")
r = run("sh", os.path.join(ROOT, "seed", "germinate.sh"), G, cwd=ROOT)
check("a garden germinates", r.returncode == 0, r.stdout + r.stderr)
v = os.path.join(G, "VOCAB.md"); s = open(v).read()
if "extends_profiles:" in s:
    s = (s.replace("extends_profiles: []", "extends_profiles: [network]") if "extends_profiles: []" in s
         else s.replace("extends_profiles: [", "extends_profiles: [network, ", 1))
else:
    s = s.replace("\n---", "\nextends_profiles: [network]\n---", 1)
assert "network" in s.split("\n---")[0], "the garden did not opt into the network profile"   # a no-op edit is a bug
open(v, "w").write(s)
BEAN = os.path.join(G, "beans", "box.md")

def gate(endpoints):
    open(BEAN, "w").write("""---
bean: box
kind: host
title: "a machine"
status: active
summary: "probe"
nature: physical
identity: { status: confirmed, anchors: [ { key: serial, value: "SN-POS-1", class: hardware, establishing: true } ] }
provenance: { src: observed, by: probe, as_of: 2026-09-20 }
owned_by: { legal: { external: "someone" } }
responsibility: { legal: { external: "someone" } }
endpoints:
""" + endpoints + "---\n\nprobe.\n")
    r = run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G)
    return r.stdout + r.stderr

E = '  - { protocol: %s, system: %s, at: "%s"%s, exposure: lan, observed: 2026-09-20 }\n'
ok = gate(E % ("smtp", "ipv4", "203.0.113.10", ", port: 25"))
check("an address is a position in a PLACE system, and an ordinary endpoint passes", "0 error" in ok, ok[-700:])
out = gate(E % ("smtp", "ipv4", "203.0.113.10", ', port: "110/143/993/995"'))
check("four ports jammed into one string — the defect `endpoints` was written to end — is refused at last",
      "endpoints[0].port '110/143/993/995' is not in the one canonical form 'tcp' declares" in out, out[-700:])
out = gate(E % ("smtp", "ipv4", "203.0.113.10", ", port: 70000"))
check("a port outside 0-65535 is refused by the system that owns the form", "port '70000' is not in the one canonical form" in out, out[-500:])
out = gate(E % ("dns", "ipv4", "203.0.113.10", ", port: 53") + E % ("dns", "ipv4", "203.0.113.10", ", port: 53, transport: tcp"))
check("53/udp and 53/tcp are two positions: an entry STATES its transport when it is not its protocol's usual one",
      "0 error" in out, out[-700:])
out = gate(E % ("dns", "ipv4", "203.0.113.10", ", port: 53, transport: smtp"))
check("...and `transport` names a TRANSPORT-layer row, not any protocol — the registry is narrowed by `where`",
      "transport 'smtp' is not a declared net_protocols where layer is transport" in out, out[-600:])
out = gate(E % ("http", "unix-filesystem", "host-a:/run/app/www.sock", ""))
check("a unix socket path is an endpoint like any other — its system has always been a place",
      "0 error" in out, out[-700:])
out = gate(E % ("http", "unix-filesystem", "/run/app/www.sock", ""))
check("...held to that system's one form: a bare path names no host", "is not in the one canonical form 'unix-filesystem' declares" in out, out[-500:])
out = gate(E % ("smtp", "gregorian-civil", "2026-09-20", ""))
check("a TIME system is not where a being answers: `system` is narrowed to place", "system 'gregorian-civil' is not a declared anchor_systems where dimension is" in out, out[-600:])
out = gate(E % ("smtp", "ipv6", "203.0.113.10", ", port: 25"))
check("ipv4 and ipv6 are still separate systems with separate forms", "is not in the one canonical form 'ipv6' declares" in out, out[-500:])

import yaml, re
sv = yaml.safe_load(re.match(r'^---\n(.*?)\n---', open(os.path.join(ROOT, "seed", "std-vocab.md")).read(), re.S).group(1))
dims = {r.get("dimension") for r in sv["anchor_systems"]}
held = {a["domain"]["systems"] for a in sv["aspects"] if isinstance(a.get("domain"), dict)} | {"any"}
check("EVERY dimension a system positions in is held by some aspect — `address` belonged to no figure", dims <= held, f"{sorted(dims)} vs {sorted(held)}")
# a UNIT's dimension is what it MEASURES, which is a different thing: it must be one something is metered in
measured = {a.get("metered") for a in sv["aspects"]} | {(r.get("restrictions") or {}).get("metered") for r in sv["anchor_systems"]}
check("...and every dimension a unit measures is one some aspect or system is metered in",
      {u.get("dimension") for u in sv["units"]} <= measured, f"{sorted({u.get('dimension') for u in sv['units']})} vs {sorted(x for x in measured if x)}")
check("the address registry is gone rather than kept beside its replacement", "address_systems" not in sv)

shutil.rmtree(T, ignore_errors=True)
print("\npositions: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
