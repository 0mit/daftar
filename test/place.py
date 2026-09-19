#!/usr/bin/env python3
"""Place (std-vocab 11.0, "P3"): positions that name their host, and the merge order over them.

A path with no host is a position in a system nobody named: the estate this grew in holds 13 paths that exist
on two machines as two different trees. This grows a garden and checks that the gate refuses the old
host-relative staleness key, warns (never blocks) on a bare path while a corpus is migrated, accepts a
network segment as a place, and that the merge absorbs a tree into a subtree of it under the same host only.
"""
import os, sys, subprocess, tempfile, shutil, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'bin'))
FAILS = []

def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:600]))
    if not cond:
        FAILS.append(name)

def run(*a, cwd=None):
    return subprocess.run(list(a), capture_output=True, text=True, cwd=cwd)

T = tempfile.mkdtemp(prefix="dmplace-")
G = os.path.join(T, "g")
run("sh", os.path.join(ROOT, "seed", "germinate.sh"), G, cwd=ROOT)
_v = os.path.join(G, "VOCAB.md"); _s = open(_v).read()        # code_paths and analysis_cache are `code` profile terms
open(_v, "w").write(_s.replace("extends_profiles: [", "extends_profiles: [code, ", 1)
                    .replace("extends_profiles: []", "extends_profiles: [code]")
                    if "extends_profiles:" in _s else _s.replace("\n---", "\nextends_profiles: [code]\n---", 1))

def gate():
    r = run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G)
    return r.stdout + r.stderr

OWN = 'owned_by: { legal: { owner: { bean: someone } } }\nresponsibility: { legal: { holder: { bean: someone } } }\n'
open(os.path.join(G, "beans", "someone.md"), "w").write(
    '---\nbean: someone\nkind: person\ntitle: "a person"\nstatus: active\nsummary: "p"\nnature: living\n'
    'identity: { status: confirmed, anchors: [ { key: email, value: "a@example.org", class: logical, establishing: true } ] }\n'
    'provenance: { src: asserted-by-human, by: t, as_of: 2026-01-01 }\nowned_by: { legal: { crown: love } }\n'
    'responsibility: { legal: { self: true } }\n---\nA person.\n')

def codebase(path, key, located=""):
    open(os.path.join(G, "beans", "tree.md"), "w").write(
        '---\nbean: tree\nkind: codebase\ntitle: "a codebase"\nstatus: active\nsummary: "s"\nnature: metaphysical\n'
        'identity: { status: confirmed, anchors: [ { key: git_remote, value: "git@example.org:t.git", class: logical, establishing: true } ] }\n'
        'provenance: { src: observed, by: t, as_of: 2026-01-01 }\n' + OWN +
        f'code_paths:\n  - {{ path: "{path}", role: own-source, scan_policy: index }}\n'
        'analysis_cache:\n  code-structure:\n    produced_by: t\n    as_of: 2026-01-01\n'
        f'    staleness_key: "{key}"\n    policy: index\n' + located + '---\nA tree.\n')
    return gate()

out = codebase("root:tree/src", "tree@a1b2c3d4e5f6")
check("a position naming its root and a staleness key in the git object graph pass, with no warning",
      "0 error" in out and " 0 warning" in out, out[-900:])
out = codebase("root:tree/src", "git-head:a1b2c3d4e5f6")
check("the host-relative `git-head:<sha>` key is refused — one analysis had one verdict per machine",
      "is not in the form this term declares" in out, out[-900:])
out = codebase("root:tree/src", "manual:checked by hand")
check("`manual:<why>` stays legal for what no key can track", "0 error" in out, out[-900:])
out = codebase("/home/someone/tree", "tree@a1b2c3d4e5f6")
check("a bare absolute path WARNS while a corpus is migrated, and does not block",
      "0 error" in out and "names no host" in out, out[-900:])
out = codebase("host-a:/home/someone/tree", "tree@a1b2c3d4e5f6")
check("...and a path that states its host passes", "0 error" in out and " 0 warning" in out, out[-900:])

SEG = 'located_at:\n  - { system: network-segment, at: "office/vlan-13", openness: here, observed: 2026-01-01 }\n'
out = codebase("root:tree/src", "tree@a1b2c3d4e5f6", SEG)
check("a network segment is a place a being can be located at, and occupying its Tier-0 vacancy says so",
      "0 error" in out and "is declared vacant at TIER-0 but is OCCUPIED here" in out, out[-900:])
BAD = 'located_at:\n  - { system: network-segment, at: "vlan-13", openness: here, observed: 2026-01-01 }\n'
out = codebase("root:tree/src", "tree@a1b2c3d4e5f6", BAD)
check("...and a segment that names no network is refused — two sites both have a vlan-13",
      "canonical form" in out or "must be in" in out, out[-900:])

# dmstale reads the key as a POSITION: before 11.0 it knew only `git-head:`, so every migrated key read
# as UNKNOWN — "not machine-checkable" — which is the opposite of what migrating them was for.
codebase("root:tree/src", "tree@a1b2c3d4e5f6")
r = run(sys.executable, os.path.join(G, "bin", "dmstale.py"), cwd=G)
check("dmstale reads `<repo>@<sha>` and says the source is not on this host, not that the key is uncheckable",
      "NOT-HERE" in r.stdout and "UNKNOWN" not in r.stdout, r.stdout[-700:])
codebase("root:tree/src", "manual:checked by hand")
r = run(sys.executable, os.path.join(G, "bin", "dmstale.py"), cwd=G)
check("...and a `manual:` key is still the one thing it calls uncheckable", "UNKNOWN" in r.stdout, r.stdout[-700:])

# WHAT STALE MEANS (human-ratified 2026-09-20): the source MOVED under the analysis. A clone that simply
# lacks the keyed objects is behind — a fact about the reader — and an analysis whose source moved on must
# not read FRESH, which is what it did while STALE was produced only by a missing object.
R = os.path.join(T, "repo")
os.makedirs(os.path.join(R, "src"))
def git(*a):
    return run("git", "-C", R, *a)
run("git", "init", "-q", R)
open(os.path.join(R, "src", "a.txt"), "w").write("one\n")
git("add", "-A"); git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "first")
KEY = git("rev-parse", "--short=7", "HEAD").stdout.strip()
open(os.path.join(G, "beans", "trixy-like.md"), "w").write(
    '---\nbean: trixy-like\nkind: host\ntitle: "this machine"\nstatus: active\nsummary: "h"\nnature: physical\n'
    'identity: { status: confirmed, anchors: [ { key: hostname, value: "' + __import__("socket").gethostname().lower() + '", class: network, establishing: false }, { key: serial, value: "SN-T1", class: hardware, establishing: true } ] }\n'
    'provenance: { src: observed, by: t, as_of: 2026-01-01 }\n' + OWN +
    'roots:\n  tree: { system: unix-filesystem, at: "' + __import__("socket").gethostname().lower() + ':' + R + '", observed: 2026-01-01 }\n'
    '---\nA host.\n')
def stale_run(key):
    codebase("root:tree/src", key)
    return run(sys.executable, os.path.join(G, "bin", "dmstale.py"), cwd=G).stdout
out = stale_run("tree@" + KEY)
check("dmstale: the key is here and nothing since it touches the covered paths — FRESH",
      "FRESH" in out and "STALE" not in out, out[-500:])
open(os.path.join(R, "src", "a.txt"), "w").write("two\n")
git("add", "-A"); git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "the source moves")
out = stale_run("tree@" + KEY)
check("dmstale: a commit after the key that TOUCHES the covered paths — STALE, which is what the name promises",
      "STALE" in out and "touch the covered paths" in out, out[-500:])
open(os.path.join(R, "elsewhere.txt"), "w").write("x\n")
git("add", "-A"); git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "a change somewhere else")
NEW = git("rev-parse", "--short=7", "HEAD").stdout.strip()
out = stale_run("tree@" + NEW)
check("dmstale: a commit that touches nothing covered leaves the analysis FRESH",
      "FRESH" in out and "STALE" not in out, out[-500:])
out = stale_run("tree@0000000")
check("dmstale: a clone that does not have the keyed objects is BEHIND, not stale",
      "NOT-HERE" in out and "STALE" not in out and "is behind" in out, out[-500:])

import dmmerge as M
def merged(a, b):
    def g(garden, val):
        return [{'garden': garden, 'id': 'box', 'fm': {
            'bean': 'box', 'kind': 'host', 'nature': 'physical', 'title': 'b', 'status': 'active', 'summary': 'b',
            'identity': {'status': 'confirmed', 'anchors': [{'key': 'serial', 'value': 'SN-P1', 'class': 'hardware',
                                                            'establishing': True}]},
            'provenance': {'src': 'observed', 'by': garden, 'as_of': '2026-09-17'}, 'owns': {'tree': val}}}]
    sd = list(M.merge_gardens([g('g1', a), g('g2', b)]).values())[0]
    return sd['facts']['owns']['members']['tree']

m = merged("host-a:/home/user", "host-a:/home/user/tree")
check("P3c: a tree is absorbed by a subtree of it on the SAME host",
      m.get('value') == "host-a:/home/user/tree", json.dumps(m))
m = merged("host-a:/home/user/tree", "host-b:/home/user/tree")
check("P3c: the same path on two hosts is two places — a disagreement, never absorbed",
      'conflict' in json.dumps(m), json.dumps(m))
m = merged("root:tree", "root:tree/src")
check("P3c: logical roots nest the same way", m.get('value') == "root:tree/src", json.dumps(m))
m = merged("root:tree/src", "root:other/src")
check("P3c: two different roots are unordered", 'conflict' in json.dumps(m), json.dumps(m))

shutil.rmtree(T, ignore_errors=True)
print("\nplace: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
