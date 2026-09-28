#!/usr/bin/env python3
"""The line from place to location (std-vocab 29.0): جا and مکان, and what a placement takes from where it is placed.

Grows a garden and places beings in it along the rope: a machine in a rack's slots (a location that takes room), two
virtual machines in a hypervisor (a habitat that takes a share), a repository known only by the machine it is on (a
location known to its host alone). Checks that shares past a capacity are warned (overcommitted) and room past it
refused; that two beings never take the same room at once, unless one is part of the other; that a location's host is
the one its position names; that a rung that takes nothing takes nothing; and that one capsule, `<scheme>:<code>`,
holds a code wherever one is written — an identity included.
"""
import os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:900]))
    if not cond:
        FAILS.append(name)


def run(*a, cwd=None):
    return subprocess.run(list(a), capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd)


T = tempfile.mkdtemp(prefix="dmrope-")
G = os.path.join(T, "g")
r = run("sh", os.path.join(ROOT, "seed", "germinate.sh"), G, "--gardener", "sam", cwd=ROOT)
check("a garden germinates on the law with the line from place to location", r.returncode == 0, r.stdout + r.stderr)
OWN = 'owned_by: { legal: { owner: { bean: sam } } }\nresponsibility: { legal: { holder: { bean: sam } } }\n'
PROV = 'provenance: { src: asserted-by-human, by: "sam (gardener)", as_of: 2026-09-28 }\n'


def host(name, extra=""):
    return (f'---\nbean: {name}\ngenos: host\ntitle: "{name}"\nstatus: active\nsummary: "a machine"\nnature: soma\n'
            f'identity: {{ status: confirmed, anchors: [ {{ key: hostname, value: {name}, class: network, establishing: false }}, '
            f'{{ key: serial, value: SN-{name.upper()}, class: hardware, establishing: true }} ] }}\n'
            + PROV + OWN + extra + '---\nA machine.\n')


def write(name, text):
    open(os.path.join(G, "beans", name + ".md"), "w").write(text)


def gate():
    r = run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G)
    return r.stdout + r.stderr


# ---- a rack of 42 slots, and two machines that take room in it -------------------------------------------------------------
write("rack-a", host("rack-a", "capacity:\n  - { count: 42, unit: item, placement: location, note: \"its slots\" }\n"))
SLOT = 'located_at:\n  - { system: local-frame, openness: here, at: "rack-a#u17", takes: [ { count: 2, unit: item } ] }\n'
write("web-1", host("web-1", SLOT))
out = gate()
check("a machine takes two slots of a rack's 42: a location that takes room, within what its host holds", " 0 error(s)" in out, out[-900:])
write("web-2", host("web-2", SLOT))
out = gate()
check("two beings never take the same room at once: a second machine in slot 17 is refused",
      "takes the room at rack-a#u17 in rack-a, which web-1" in out and "two beings do not take the same room at once" in out, out[-900:])
write("web-2", host("web-2", SLOT + "part_of: { bean: web-1 }\n"))
out = gate()
check("...unless one is part of the other: a board in its machine's slot takes the machine's room", " 0 error(s)" in out, out[-900:])
write("web-2", host("web-2", SLOT.replace("u17", "u19")))
out = gate()
check("...and another slot passes", " 0 error(s)" in out, out[-900:])
write("rack-a", host("rack-a", "capacity:\n  - { count: 3, unit: item, placement: location }\n"))
out = gate()
check("room past what the host holds is refused: four slots taken of three", "capacity[0] holds 3 item, and what is placed in it takes 4 item"
      in out and "room is taken once" in out, out[-900:])
write("rack-a", host("rack-a", "capacity:\n  - { count: 42, unit: item, placement: location }\n"))

# ---- a hypervisor and its guests: a habitat that takes a share --------------------------------------------------------------
write("hv", host("hv", "provides_habitat: kvm\ncapacity:\n  - { count: 32, unit: gibibyte, placement: habitat }\n"))
def guest(name, gib):
    return host(name, f"lives_in: {{ bean: hv, takes: [ {{ count: {gib}, unit: gibibyte }} ] }}\n")
write("vm-1", guest("vm-1", 16))
write("vm-2", guest("vm-2", 8))
out = gate()
check("two guests take 24 GiB of a hypervisor's 32: a habitat that takes a share", " 0 error(s), 0 warning(s)" in out, out[-900:])
write("vm-3", guest("vm-3", "16384"))
write("vm-3", host("vm-3", "lives_in: { bean: hv, takes: [ { count: 16384, unit: megabyte } ] }\n"))
out = gate()
check("shares promised past what a host holds are warned, not refused — a hypervisor overcommits its memory — and are "
      "summed exactly across units", " 0 error(s)" in out and "capacity[0] holds 32 gibibyte" in out and "overcommitted" in out,
      out[-900:])
os.remove(os.path.join(G, "beans", "vm-3.md"))

# ---- a location known to its host alone: the place known, the position not ---------------------------------------------------
write("repo", host("repo", 'located_at:\n  - { system: git-remote, openness: unknown, host: { bean: hv } }\n'))
out = gate()
check("a repository known only by the machine it is on: `host` alone, the position within it unknown", " 0 error(s)" in out, out[-900:])
write("repo", host("repo", 'located_at:\n  - { system: git-remote, openness: here, at: "hv:git/ledger.git", host: { bean: hv } }\n'))
out = gate()
check("...and beside `at`, the host the position names", " 0 error(s)" in out, out[-900:])
write("repo", host("repo", 'located_at:\n  - { system: git-remote, openness: here, at: "web-1:git/ledger.git", host: { bean: hv } }\n'))
out = gate()
check("a position is on the one host it names: `at` on web-1 and `host` hv is refused",
      "located_at[0].at names the host web-1, and `host` is hv" in out, out[-900:])
write("repo", host("repo", 'located_at:\n  - { system: iso-3166, openness: here, at: TR, host: { bean: hv } }\n'))
out = gate()
check("a system measured from no host takes no `host`", "`iso-3166` is measured from none" in out, out[-900:])
os.remove(os.path.join(G, "beans", "repo.md"))

# ---- crossing into 29.0: the words it folded, translated where they are written ---------------------------------------------
for b in ("rack-a", "web-1", "web-2", "hv", "vm-1", "vm-2"):
    os.remove(os.path.join(G, "beans", b + ".md"))
_voc = open(os.path.join(G, "VOCAB.md")).read()
open(os.path.join(G, "VOCAB.md"), "w").write(_voc.replace("\n---", "\nextends_profiles: [code, domain, knowledge]\n---", 1)
                                             if "extends_profiles:" not in _voc else
                                             re.sub(r"extends_profiles: \[[^\]]*\]", "extends_profiles: [code, domain, knowledge]", _voc))
write("box", host("box"))
CODE = ('---\nbean: {b}\ngenos: codebase\ntitle: "{b}"\nstatus: active\nsummary: "code"\nnature: lekton\n'
        'identity: {{ status: confirmed, anchors: [ {{ key: identifier, value: "codebase:{b}", class: logical, establishing: true }}{anchor} ] }}\n'
        + (PROV + OWN).replace('{', '{{').replace('}', '}}') + '{extra}analysis_cache:\n  code-structure: {{ produced_by: probe, as_of: 2026-09-28, staleness_key: "{b}@abc1234", '
        'policy: index, form: inline, covers_paths: ["root:{b}"] }}\n---\nCode.\n')
write("fw", CODE.format(b="fw", anchor="", extra='code_paths:\n  - { path: "root:fw", role: own-source, scan_policy: reference-only }\n'))
write("tool", CODE.format(b="tool", anchor=', { key: git_remote, value: "box:git/tool.git", class: logical, establishing: true }',
                          extra='code_paths:                  # LOCATE only\n'
                                '  - { path: "root:tool", role: own-source, scan_policy: index }   # its own tree\n'
                                '  - { path: "root:fw", role: framework-reference, scan_policy: reference-only }   # the framework it is read beside\n'
                                'git_host: { bean: box }\n'
                                'knowledge:\n  - { scheme: technology, code: samba, rel: uses }\n'))
write("prod", CODE.format(b="prod", anchor="", extra='code_paths:\n  - { path: "root:prod", role: own-source, scan_policy: index }\n'
                          'git_host: { bean: box, repo: "box:git/prod.git" }\n'
                          '  # where the bare repository lives, and not a claim about the working copies\n'))
write("samba", '---\nbean: samba\ngenos: product\ntitle: "Samba"\nstatus: active\nsummary: "the technology"\nnature: lekton\n'
      'identity: { status: confirmed, anchors: [ { key: technology, value: samba, class: logical, establishing: true } ] }\n'
      + PROV + OWN + '---\nSamba.\n')
write("example-org", '---\nbean: example-org\ngenos: domain\ntitle: "example.org"\nstatus: active\nsummary: "a name"\nnature: lekton\n'
      'identity: { status: confirmed, anchors: [ { key: fqdn, value: "example.org", class: logical, establishing: true } ] }\n'
      + PROV + 'owned_by: { legal: { external: "the .org registry" } }\nresponsibility: { legal: { holder: { bean: sam } } }\n'
      'registration:\n  registrar: "Example Registrar Inc."\n  created: 2020-01-15\n  expires: 2027-01-15\n'
      '  auto_renew: disabled     # the gardener said so; the registry does not show it\n  observed: 2026-09-28\n'
      '  source: "WHOIS for example.org"\n---\nA name.\n')
STEP = ("import os, sys\nsys.path.insert(0, os.path.join(os.getcwd(), 'bin'))\nimport dmupgrade\n"
        "s = dmupgrade.Step29(sys.argv[1], 'v-next', False)\ns.plan()\nprint(s.apply()[0])\n")
r = run(sys.executable, "-c", STEP, ROOT, cwd=G)
out = gate()
check("a garden in 28's words crosses into 29.0 by the step's own translation, with 0 errors", r.returncode == 0 and " 0 error(s)" in out,
      (r.stdout + r.stderr)[-600:] + out[-900:])
def fm(b):
    import yaml
    return yaml.safe_load(open(os.path.join(G, "beans", b + ".md")).read().split("---")[1])
T_, P_, S_ = fm("tool"), fm("prod"), fm("samba")
check("...a code written apart from its scheme is one coding: `technology:samba`", T_["knowledge"][0] == {"code": "technology:samba", "rel": "uses"})
check("...an anchor a knowledge scheme keyed is the identifier it is: `identifier: technology:samba`",
      S_["identity"]["anchors"][0]["key"] == "identifier" and S_["identity"]["anchors"][0]["value"] == "technology:samba")
check("...git_host is read from the code's own git_remote where that names its host, and so written nowhere",
      "git_host" not in T_ and not any(e.get("system") == "git-remote" for e in T_["located_at"]), T_.get("located_at"))
check("...and otherwise is a location in `git-remote`, the repository as its host names it",
      {"system": "git-remote", "openness": "here", "at": "box:git/prod.git"} in P_["located_at"], P_.get("located_at"))
check("...a code bean's trees are its locations, with the code profile's words",
      "code_paths" not in T_ and {"system": "unix-filesystem", "openness": "here", "at": "root:tool", "role": "own-source",
                                  "scan_policy": "index"} in T_["located_at"], T_.get("located_at"))
check("...and a framework it is read beside is a dependency on that framework's bean, whose tree it is",
      T_.get("depends_on") == {"framework": {"bean": "fw"}}, T_.get("depends_on"))
_tt, _pt = open(os.path.join(G, "beans", "tool.md")).read(), open(os.path.join(G, "beans", "prod.md")).read()
check("...and every comment goes where the fact it sat on goes: the block's, a tree's, a framework's, a repository's",
      "# LOCATE only" in _tt and "# its own tree" in _tt and "# the framework it is read beside" in _tt
      and "# where the bare repository lives" in _pt, _tt[-700:])
_reg = os.path.join(G, "beans", "example-org-registration.md")
R_ = fm("example-org-registration") if os.path.exists(_reg) else {}
check("...a registration is the contract it is, over its domain: the registrar a party, its day its timing, its lapse a "
      "renewal clause with ninety days' notice and the gardener's word on it",
      R_.get("over") == [{"thing": {"bean": "example-org"}}] and R_["parties"]["registrar"]["external"] == "Example Registrar Inc."
      and R_["clauses"]["renewal"]["due"].isoformat() == "2027-01-15" and R_["clauses"]["renewal"]["notice"] == {"count": 90, "unit": "day"}
      and "# the gardener said so" in open(_reg).read() and "registration" not in fm("example-org"), R_)
run("git", "-C", G, "config", "user.name", "sam"); run("git", "-C", G, "config", "user.email", "sam@example.org")
_all = sorted(f[:-3] for f in os.listdir(os.path.join(G, "beans")) if f.endswith(".md"))
sv = run(sys.executable, os.path.join(G, "bin", "dmsave.py"), "sam (gardener)", "crossed into 29.0", "--body",
         "- action: RULE-CHANGE (VOCAB.md) extends the code, domain and knowledge profiles; the translation of "
         + ", ".join(f"[[{b}]]" for b in _all), cwd=G)
check("...and the translated garden is saved: what the step wrote passes the save's own rules, a new record's day stamped "
      "at writing and the day its facts were read kept in `from`", sv.returncode == 0, (sv.stdout + sv.stderr)[-700:])
st = run(sys.executable, os.path.join(G, "bin", "dmstale.py"), cwd=G).stdout
check("...and dmstale reads the renewal as it read the registration: its day, its registrar, whether it renews itself",
      "example-org-registration.clauses[renewal]" in st and "auto_renew=disabled" in st and "Example Registrar Inc." in st, st[-600:])

# ---- 29.1: time is place's sibling, a port is room, a working copy is a position --------------------------------------------
_voc = open(os.path.join(G, "VOCAB.md")).read()
open(os.path.join(G, "VOCAB.md"), "w").write(_voc.replace("extends_profiles: [code, domain, knowledge]",
                                                           "extends_profiles: [code, domain, knowledge, network]"))
def event(name, start, end, rel="present"):
    return (f'---\nbean: {name}\ngenos: event\ntitle: "{name}"\nstatus: active\nsummary: "a dinner"\nnature: lekton\n'
            f'identity: {{ status: confirmed, anchors: [ {{ key: identifier, value: "event:{name}", class: logical, establishing: true }} ] }}\n'
            + PROV + 'owned_by: { legal: { crown: logos } }\nresponsibility: { legal: { holder: { bean: sam } } }\n'
            f'timing:\n  start: {{ system: gregorian-civil, at: "{start}", unit: minute }}\n'
            f'  end: {{ system: gregorian-civil, at: "{end}", unit: minute }}\n'
            f'refs:\n  guest: {{ bean: sam, rel: {rel} }}\n---\nA dinner.\n')
write("dinner-a", event("dinner-a", "2026-09-12 19:30+03:00", "2026-09-12 22:00+03:00"))
write("dinner-b", event("dinner-b", "2026-09-12 21:00+03:00", "2026-09-12 23:00+03:00"))
out = gate()
check("a meeting takes the hours of those present at it: sam at two dinners whose times overlap is refused",
      "sam is present at it and at dinner-a, and their times overlap" in out, out[-900:])
write("dinner-b", event("dinner-b", "2026-09-12 22:00+03:00", "2026-09-12 23:00+03:00"))
check("...one after the other is no overlap", " 0 error(s)" in gate(), "")
write("dinner-b", event("dinner-b", "2026-09-12 21:00+03:00", "2026-09-12 23:00+03:00", rel="invited"))
check("...and an invitation takes no one's hour (RFC 5545's TRANSPARENT): only those present are judged", " 0 error(s)" in gate(), "")
EP = 'endpoints:\n  - { protocol: ssh, system: ipv4, at: "192.0.2.10", port: 22, exposure: lan }\n'
write("mx-1", host("mx-1", EP))
write("mx-2", host("mx-2", EP))
out = gate()
check("a port is room: two beings answering on one port of one address are refused",
      "answers on 192.0.2.10 port 22" in out and "mx-1" in out, out[-900:])
write("mx-2", host("mx-2", EP + "part_of: { bean: mx-1 }\n"))
check("...unless one is part of the other", " 0 error(s)" in gate(), "")
write("mx-2", host("mx-2", EP.replace("system: ipv4, at: \"192.0.2.10\"", "system: event-anchored, at: \"after:dinner-a\"")))
out = gate()
check("an endpoint is a place: a system of any dimension is refused where it answers", "where dimension is ['place']" in out, out[-900:])
os.remove(os.path.join(G, "beans", "mx-2.md"))
SESSION = ('---\nbean: session-one\ngenos: session\ntitle: "a session"\nstatus: active\nsummary: "work"\nnature: lekton\n'
           'identity: { status: confirmed, anchors: [ { key: identifier, value: "session:session-one", class: logical, establishing: true } ] }\n'
           + PROV + OWN + 'timing:\n  start: { system: gregorian-civil, at: "2026-09-28 10:00+03:00", unit: minute }\n'
           'workspace:\n  host: { bean: box }\n  {AT}\n  branch: main\n---\nA session.\n')
write("session-one", SESSION.replace("{AT}", "system: unix-filesystem\n  at: \"box:/srv/tree\""))
check("a working copy is a position in its host's filesystem", " 0 error(s)" in gate(), gate()[-600:])
write("session-one", SESSION.replace("{AT}", "system: unix-filesystem\n  at: \"mx-1:/srv/tree\""))
out = gate()
check("...on the one machine its position names", "workspace.at names the host mx-1, and `host` is box" in out, out[-600:])
write("session-one", SESSION.replace("{AT}", "at: \"root:tree\""))
r = run(sys.executable, "-c", STEP, ROOT, cwd=G)
check("...and the translation writes the filesystem a working copy is in, from its position's form",
      "system: unix-filesystem" in open(os.path.join(G, "beans", "session-one.md")).read() and " 0 error(s)" in gate(),
      (r.stdout + r.stderr)[-400:])

# ---- the law holds its line -------------------------------------------------------------------------------------------------
STD = os.path.join(G, "seed", "std-vocab.md")
law = open(STD).read()
def law_gate(old, new, want, why):
    assert old in law, old
    open(STD, "w").write(law.replace(old, new, 1))
    out = gate()
    check("the law holds its line: " + why, want in out, [l for l in out.splitlines() if l.startswith("ERROR")][:4])
law_gate("    placement: habitat\n", "    placement: nowhere\n", "placement 'nowhere' is no rung of the line",
         "a term's placement is a rung of it")
law_gate("    placement: habitat\n", "    placement: presence\n", "its rung, `presence`, takes nothing from where it places a being",
         "a rung that takes nothing takes nothing — a memory takes nothing from a heart")
open(STD, "w").write(law)
rules = run(sys.executable, os.path.join(G, "bin", "dmrules.py"), cwd=G).stdout
check("the rules a garden prints show the line", re.search(r"^  lives_in .*placement habitat", rules, re.M)
      and re.search(r"^  located_at .*placement location", rules, re.M), [l for l in rules.splitlines() if "lives_in" in l][:2])

shutil.rmtree(T, ignore_errors=True)
print("\nrope: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
