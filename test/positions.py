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
r = run("sh", os.path.join(ROOT, "seed", "germinate.sh"), G, "--gardener", "keeper", cwd=ROOT)
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
genos: host
title: "a machine"
status: active
summary: "probe"
nature: soma
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
sys.path.insert(0, os.path.join(ROOT, "bin"))
import yaml, dmparse as _P
_rows = {r["system"]: r for r in yaml.safe_load(open(os.path.join(ROOT, "seed", "std-vocab.md")).read().split("\n---")[0].split("---\n", 1)[1])["anchor_systems"]}
check("an IP address's form is checked by the standard library's validator, not by a pattern written here — and never by both",
      _rows["ipv4"].get("checked_by") == "ipaddress-v4" and _rows["ipv6"].get("checked_by") == "ipaddress-v6"
      and "pattern" not in _rows["ipv4"] and "pattern" not in _rows["ipv6"])
check("...the check names the law offers are exactly the checks the tools carry",
      sorted(yaml.safe_load(open(os.path.join(ROOT, "seed", "std-vocab.md")).read().split("\n---")[0].split("---\n", 1)[1])["system_shape"]["checked_by"]) == sorted(_P.FORM_CHECKS))
out = gate(E % ("smtp", "ipv6", "2001:DB8::1", ", port: 25"))
check("...an address has ONE spelling, the library's own: upper case is refused", "'2001:DB8::1' is not in the one canonical form 'ipv6' declares" in out, out[-400:])
check("...and that spelling passes", "0 error" in gate(E % ("smtp", "ipv6", "2001:db8::1", ", port: 25")))
for _bad in ("256.1.1.1", "01.2.3.4", "10.0.0.0/33"):
    out = gate(E % ("smtp", "ipv4", _bad, ", port: 25"))
    check("an ipv4 position has real octets and a real prefix: %s is refused by the system that owns the form" % _bad,
          "at '%s' is not in the one canonical form 'ipv4' declares" % _bad in out, out[-400:])
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

# ---------------------------------------------------------------- 18.3: WHERE a surface is bound, and WHO may reach it
M = '  - { protocol: ssh, system: ipv4, at: "203.0.113.10", port: 22, confidentiality: encrypted, observed: 2026-09-20%s }\n'
ASKS = "endpoints[0] is at plane:management, exposure:internet but states no admitted_from"
out = gate(M % ", plane: management, exposure: internet")
check("a MANAGEMENT surface bound to a public address, with nothing said about who may reach it, warns",
      ASKS in out and "0 error" in out, out[-700:])
out = gate(M % ', plane: management, exposure: internet, admitted_from: "two named address lists, on the input chain"')
check("...and is silent once its sources are stated: a fixed thing stops warning",
      "admitted_from" not in out and "IN BREACH" not in out and "0 error" in out, out[-700:])
out = gate(M % ", plane: data, exposure: internet")
check("a DATA surface on the internet is never asked who it admits", "admitted_from" not in out and "0 error" in out, out[-700:])
out = gate(M % ", plane: management, exposure: lan")
check("...nor a management surface that is not bound to a public address", "admitted_from" not in out and "0 error" in out, out[-700:])
out = gate(M % ", exposure: internet")
check("`plane` is never defaulted — no protocol row carries one — so an entry that states none is not in the cell",
      "admitted_from" not in out and "0 error" in out, out[-700:])
out = gate(M % ', plane: data, exposure: lan, admitted_from: "the monitoring host"')
check("`admitted_from` may be stated on any surface, asked for or not", "0 error" in out, out[-700:])

import yaml, re
sv = yaml.safe_load(re.match(r'^---\n(.*?)\n---', open(os.path.join(ROOT, "seed", "std-vocab.md")).read(), re.S).group(1))
dims = {r.get("dimension") for r in sv["anchor_systems"]}
held = {a["domain"]["systems"] for a in sv["aspects"] if isinstance(a.get("domain"), dict)} | {"any"}
check("EVERY dimension a system positions in is held by some aspect — `address` belonged to no figure", dims <= held, f"{sorted(dims)} vs {sorted(held)}")
# a UNIT's dimension is what it MEASURES, which is a different thing: it must be one something is metered in
measured = {a.get("metered") for a in sv["aspects"]} | {(r.get("restrictions") or {}).get("metered") for r in sv["anchor_systems"]}
check("...and everything metered is metered in a declared base dimension",
      {x for x in measured if x and x != "none"} <= {d["dimension"] for d in sv["dimensions"]}, sorted(x for x in measured if x))
check("the address registry is gone rather than kept beside its replacement", "address_systems" not in sv)


# ---------------------------------------------------------------- 18.0: A MAPPING IS ONE ENTRY; two more domains
s = open(v).read(); assert s.count("local_terms: []") == 1
open(v, "w").write(s.replace("local_terms: []", """local_terms:
  - term: probe_stamp
    meaning: "a mapping — not a list of entries — whose attributes carry every kind of domain"
    context_keys: [probe_stamp]
    schema:
      shape: mapping
      attrs:
        at:     { in: { system: unix-epoch } }
        mode:   { in: [fast, slow] }
        tag:    { in: { pattern: "^[a-z]+$" } }
        rides:  { in: { key_of: links } }
    merge: { cardinality: single, order: none }"""))
LINK = '  - { protocol: smtp, system: ipv4, at: "203.0.113.10", port: 25, exposure: lan, observed: 2026-09-20 }\nlinks:\n  wan0: { kind: ethernet, medium: copper }\n'
# A closed list on a mapping's own attribute offers positions like an entry's (21.0), so this garden's `probe_stamp.mode`
# is accounted for: two small beans hold `fast` and `slow` throughout, whatever the probe bean says.
def twin(mode):
    open(os.path.join(G, "beans", "twin-%s.md" % mode), "w").write("""---
bean: twin-%s
genos: product
title: "a twin"
status: active
summary: "probe"
nature: lekton
identity: { status: confirmed, anchors: [ { key: product_id, value: "product:twin-%s", class: logical, establishing: true } ] }
provenance: { src: asserted-by-human, by: keeper, as_of: 2026-09-20 }
owned_by: { legal: { owner: { bean: keeper } } }
responsibility: { legal: { holder: { bean: keeper } } }
probe_stamp: { mode: %s }
---
probe.
""" % (mode, mode, mode))
twin("fast"); twin("slow")
def stamp(text):
    return gate(E % ("smtp", "ipv4", "203.0.113.10", ", port: 25") + "probe_stamp: " + text + "\n")
base = stamp("{ at: 1786245253747, mode: fast, tag: abc }")
check("a mapping's own attributes pass when they are what they say", "0 error" in base, base[-600:])
out = stamp("{ at: 2026-09-20 }")
check("`in: { system }` — a position in ONE named system, in its one form; a date is not a moment",
      "probe_stamp.at '2026-09-20' is not in the one canonical form 'unix-epoch' declares" in out, out[-500:])
out = stamp("{ mode: sideways }")
check("a closed list on a MAPPING's attribute is read — until 18.0 nothing read it", "probe_stamp.mode 'sideways' not in" in out, out[-500:])
out = stamp("{ tag: ABC }")
check("...and so is a pattern", "probe_stamp.tag 'ABC' is not in the form this term declares" in out, out[-500:])
out = stamp("{ rides: no-such-link }")
check("`in: { key_of }` — a part of a being is named by its key, and the key must exist",
      "probe_stamp.rides 'no-such-link' is no key of `links`" in out, out[-500:])
out = stamp("{ rides: nobody:wan0 }")
check("...on another bean, the bean must be held here", "names bean 'nobody'" in out, out[-500:])
# ---------------------------------------------------------------- 18.1: entries INSIDE an entry
def ledger(record, tracks="owns.addr"):
    return gate(E % ("smtp", "ipv4", "203.0.113.10", ", port: 25") + "owns: { addr: \"203.0.113.10\" }\nbeanger:\n  lan-ip:\n"
                "    defines: \"the address\"\n    tracks: \"" + tracks + "\"\n    source: \"ip addr\"\n    records:\n      - " + record + "\n")
GOOD = '{ seq: 1, at: 1786245253747, op: add, value: "203.0.113.10", prev: null, who: "tool:probe", to_where: { bean: box }, from_where: { host: box } }'
out = ledger(GOOD)
check("a datum's records pass when they are what the term says a record is", "0 error" in out, out[-600:])
for what, bad, want in (
        ("an operation nobody declared", GOOD.replace("op: add", "op: invent"), "beanger.records[lan-ip/0].op 'invent' not in"),
        ("an attribute nobody declared", GOOD.replace("op: add", "op: add, mood: cheerful"), "carries `mood`"),
        ("a date where a moment belongs", GOOD.replace("at: 1786245253747", "at: 2026-09-20"), "is not in the one canonical form 'unix-epoch' declares"),
        ("a ref to a being nobody holds", GOOD.replace("to_where: { bean: box }", "to_where: { bean: nobody }"), "names 'nobody', which this garden does not hold"),
        ("a cursor naming a host nobody holds", GOOD.replace("host: box", "host: elsewhere"), "'elsewhere' is not the id of a bean this garden holds"),
        ("a record with no sequence number", GOOD.replace("seq: 1, ", ""), "missing ['seq']")):
    out = ledger(bad)
    check("entries INSIDE an entry are judged as entries: %s is refused" % what, want in out, out[-500:])
sv_now = open(os.path.join(ROOT, "seed", "std-vocab.md")).read()
check("NOTHING in the law is `untyped` any more — and `any` is a decision, said as one",
      "in: untyped," not in sv_now and "value: { in: any," in sv_now)

# ---------------------------------------------------------------- 21.0: A MAPPING'S OWN CLOSED LIST OFFERS POSITIONS
# `shape: mapping` is one entry, and its attributes' closed lists are positions like an entry's. They were counted
# nowhere: `words.form` offered `written` and `unstated`, used by no garden and declarable vacant by none.
V1 = open(v).read()
open(v, "w").write(V1.replace("local_terms:\n", """local_terms:
  - term: mood
    meaning: "a mapping whose one attribute is a closed list"
    context_keys: [mood]
    schema:
      shape: mapping
      attrs:
        level: { in: [calm, stormy], meaning: "how it is" }
    merge: { cardinality: single, order: none }
""", 1))
out = gate(E % ("smtp", "ipv4", "203.0.113.10", ", port: 25") + "mood: { level: calm }\n")
check("a closed list on a MAPPING's attribute is a set of positions: the one no bean takes is named",
      "VOCAB mood.level: position 'stormy' is declared but NO bean occupies it" in out
      and "mood.level: position 'calm'" not in out, out[-700:])
V2 = open(v).read()
open(v, "w").write(V2.replace("\n---", '\nvacancies: [ { at: "mood.level", position: stormy, reason: prediction, why: "a storm comes" } ]\n---', 1))
out = gate(E % ("smtp", "ipv4", "203.0.113.10", ", port: 25") + "mood: { level: calm }\n")
check("...declared vacant, it is accounted for", "0 error" in out and "mood.level" not in out, out[-700:])
out = gate(E % ("smtp", "ipv4", "203.0.113.10", ", port: 25") + "mood: { level: stormy }\n")
check("...and a vacancy for one a bean takes is reported stale",
      "VOCAB vacancies: mood.level = 'stormy' is declared vacant but IS occupied" in out, out[-700:])
open(v, "w").write(V2.replace("\n---", '\nvacancies: [ { at: "words.form", position: unstated, reason: prediction, why: "x" } ]\n---', 1))
out = gate(E % ("smtp", "ipv4", "203.0.113.10", ", port: 25") + "mood: { level: calm }\n")
check("`words.form` is a declared position a vacancy may be declared at — and the law accounts for its own",
      "is not a declared position" not in out and "words.form" not in out, out[-700:])
open(v, "w").write(V1)

# ---------------------------------------------------------------- 21.0: A KEY THAT IS A REGISTRY'S ROW IS A POSITION AT IT
# `owned_by` and `responsibility` take their keys from the `facets` registry. The keys were counted at a source nothing
# declares, so a facet a garden added and used was refused as unoccupied, and a vacancy for one in use never went stale.
V0 = open(v).read()
def vocab(extra):
    open(v, "w").write(V0.replace("\n---", "\n" + extra + "\n---", 1))
WIDGET = os.path.join(G, "beans", "widget.md")
open(WIDGET, "w").write("""---
bean: widget
genos: product
title: "a widget"
status: active
summary: "probe"
nature: lekton
identity: { status: confirmed, anchors: [ { key: product_id, value: "product:widget", class: logical, establishing: true } ] }
provenance: { src: asserted-by-human, by: keeper, as_of: 2026-09-20 }
owned_by: { legal: { owner: { bean: keeper } }, moral: { owner: { bean: keeper } } }
responsibility: { legal: { holder: { bean: keeper } }, moral: { holder: { bean: keeper } } }
notes_x: [ { a: "one form" }, { b: "the other" } ]
---
probe.
""")
LISTY = """  - term: notes_x
    meaning: "a LIST whose entries take one of two forms"
    context_keys: [notes_x]
    schema:
      shape: list_of_entries
      entry_one_of: [a, b]
      attrs:
        a: { in: prose }
        b: { in: prose }
    merge: { cardinality: single, order: none }"""
assert V0.count("local_terms:\n") == 1
open(v, "w").write(V0.replace("local_terms:\n", "local_terms:\n" + LISTY + "\n", 1)); V0 = open(v).read()
vocab('registry_additions: { facets: [ { facet: moral, depends_on: [legal], meaning: "who answers for it to the people it touches" } ] }')
out = gate(E % ("smtp", "ipv4", "203.0.113.10", ", port: 25"))
check("a facet a garden ADDS and uses occupies its position at `registry:facets` — it is not refused as unoccupied",
      "0 error" in out and "position 'moral' is declared but NO bean occupies it" not in out, out[-700:])
check("...and a garden's own LIST term with `entry_one_of` has its forms occupied by its list's entries",
      "notes_x.entry_one_of" not in out, out[-700:])
vocab('registry_additions: { facets: [ { facet: moral, depends_on: [legal], meaning: "who answers for it to the people it touches" } ] }\n'
      'vacancies: [ { at: "registry:facets", position: moral, reason: prediction, why: "expected" } ]')
out = gate(E % ("smtp", "ipv4", "203.0.113.10", ", port: 25"))
check("...a vacancy the garden declares for a facet in use is reported STALE — a false vacancy does not stand",
      "VOCAB vacancies: registry:facets = 'moral' is declared vacant but IS occupied" in out, out[-700:])
os.remove(WIDGET)
vocab('registry_additions: { facets: [ { facet: moral, depends_on: [legal], meaning: "who answers for it to the people it touches" } ] }')
out = gate(E % ("smtp", "ipv4", "203.0.113.10", ", port: 25"))
check("...and with nothing using it, the added facet is unoccupied again, and says so",
      "VOCAB registry:facets: position 'moral' is declared but NO bean occupies it" in out, out[-700:])

shutil.rmtree(T, ignore_errors=True)
print("\npositions: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
