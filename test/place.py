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
run("sh", os.path.join(ROOT, "seed", "germinate.sh"), G, "--gardener", "keeper", cwd=ROOT)
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
        'analysis_cache:\n  code-structure:\n    produced_by: "tool:test"\n    as_of: 2026-01-01\n'
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
# NAMED `this-host` SINCE 2026-09-20. It was `trixy-like` — a real host of the estate this grew in, with
# a suffix, which is exactly the shape `bin/dmpublic.py` cannot see: the guard matches whole words, so the
# name went out in a published file while the guard reported nothing. The fixture never needed the name.
open(os.path.join(G, "beans", "this-host.md"), "w").write(
    '---\nbean: this-host\nkind: host\ntitle: "this machine"\nstatus: active\nsummary: "h"\nnature: physical\n'
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

# ---------------------------------------------------------------------------------------------------
# ONE DATUM, ONE VERDICT — every tool that reads a staleness key must agree about it.
#
# WHY THIS SECTION EXISTS. 11.0 abolished `git-head:<sha>` and the gate, dmstale and the corpus all moved.
# Three tools did not, and nothing noticed for three days, because each was tested only against itself:
#   bin/dmcursor.py  kept its own copy of the verdict and answered "UNKNOWN — unverifiable here" for EVERY
#                    analysis in a migrated garden. CHECKLIST Part D sends a reader there first and then
#                    tells them to trust a FRESH measurement, so the read protocol quietly stopped working.
#   bin/dmreview.py  counted a tracked cache only if its key began `git-head:` or `digest:`, so it reported
#                    0 caches and asked the reader to judge 38 settled pairs — the harm its own note names.
#   bin/dmpos.py     WROTE the abolished spelling into the position index header.
# The lesson is not "grep for the old prefix". It is that a rule with one statement in the law had four
# implementations, so the check is behavioural: hand the same key to every tool and require one answer.
_FMT = "tree@a1b2c3d4e5f6"          # the form the law declares
_OLD = "git-head:a1b2c3d4e5f6"      # the form 11.0 replaced

def tool(name, *args):
    return run(sys.executable, os.path.join(G, "bin", name), *args, cwd=G).stdout

codebase("root:tree/src", _FMT)
_c = tool("dmcursor.py", "tree")
check("every tool reads the declared form: the cursor gives a real verdict rather than UNKNOWN",
      "UNKNOWN" not in _c and ("NOT-HERE" in _c or "FRESH" in _c or "STALE" in _c), _c[-500:])
# dmreview's question is a different one from dmstale's: not "can this key be checked here" but "is this
# transcription TRACKED at all", which `manual:` keys also satisfy. It needs two near-duplicate beans to
# have a pair to classify, so the fixture builds them: the same long manifest text on two codebases, one
# of which points a cache at it. With a key the tool cannot read, the pair is raised as a possible mirror.
_LONG = ("a manifest transcribed from the upstream project: name, version, licence, dependencies, entry "
         "points and the data files it loads on install, kept here so a reader need not fetch it")
def twin(name, key, manifest):
    open(os.path.join(G, "beans", name + ".md"), "w").write(
        f'---\nbean: {name}\nkind: codebase\ntitle: "t"\nstatus: active\nsummary: "s"\nnature: metaphysical\n'
        f'identity: {{ status: confirmed, anchors: [ {{ key: git_remote, value: "git@example.org:{name}.git", '
        'class: logical, establishing: true } ] }\n'
        'provenance: { src: observed, by: t, as_of: 2026-01-01 }\n' + OWN +
        f'code_paths:\n  - {{ path: "root:{name}/src", role: own-source, scan_policy: index }}\n'
        'analysis_cache:\n  code-structure:\n    produced_by: "tool:test"\n    as_of: 2026-01-01\n'
        f'    staleness_key: "{key}"\n    policy: index\n    form: summary_ref\n'
        '    summary_ref: [owns.manifest]\n'
        f'owns:\n  manifest: "{manifest}"\n---\nA tree.\n')

def tracked_count():
    for line in tool("dmreview.py").splitlines():
        if "staleness-keyed CACHES" in line:
            return int(line.strip().split()[0])
    return -1

twin("alpha", f"alpha@a1b2c3d4e5f6", _LONG + " for alpha")
twin("beta",  f"beta@a1b2c3d4e5f6",  _LONG + " for beta")
check("dmreview counts a key in the declared form as a tracked CACHE rather than asking about it",
      tracked_count() >= 1, f"tracked={tracked_count()}")
twin("alpha", "git-head:a1b2c3d4e5f6", _LONG + " for alpha")
twin("beta",  "git-head:a1b2c3d4e5f6", _LONG + " for beta")
check("...and a key it cannot read is NOT counted as tracked — the aid must not vouch for what it cannot check",
      tracked_count() == 0, f"tracked={tracked_count()}")
for _n in ("alpha", "beta"):
    os.remove(os.path.join(G, "beans", _n + ".md"))

codebase("root:tree/src", _OLD)
_c = tool("dmcursor.py", "tree")
check("and the abolished form is unreadable to the cursor too — refused by the gate, never silently FRESH",
      "FRESH" not in _c, _c[-500:])

# dmpos WRITES a key. What it writes must be a key the law would accept, or the next person to copy the
# header learns the wrong spelling from a file no tool validates.
import re as _re
run(sys.executable, os.path.join(G, "bin", "dmpos.py"), "--build", cwd=G)
_idx = os.path.join(G, "log", ".position-index", "position.txt")
_hdr = [l for l in open(_idx, encoding="utf-8")] if os.path.exists(_idx) else []
_keys = [l.split(":", 1)[1].strip() for l in _hdr if l.startswith("# staleness_key:")]
sys.path.insert(0, os.path.join(G, "bin"))
import dmparse as _dp, yaml as _y
_sv = _y.safe_load(_dp.read(os.path.join(G, "seed", "std-vocab.md"))[0])
_ac = next(t for t in (list(_sv["terms"]) + [x for pr in _sv["profiles"].values() for x in pr["terms"]])
           if t["term"] == "analysis_cache")
_PAT = _ac["schema"]["attrs"]["staleness_key"]["in"]["pattern"]
check("the position index writes a staleness key the LAW would accept, in the one declared spelling",
      _keys and all(_re.match(_PAT, k) for k in _keys), f"keys={_keys} pattern={_PAT}")

# And the law does not teach a spelling its own pattern refuses. This is the defect the other way round:
# v0.14.0 was a law the code ignored; this is prose the code ignores, which a person reads and copies.
_doc = str(_ac["schema"]["attrs"]["staleness_key"].get("meaning", ""))
_taught = _re.findall(r"`([a-z][a-z0-9-]*:[^`]*)`", _doc) + _re.findall(r"'([a-z][a-z0-9-]*:[^']*)'", _doc)
_bad = [s for s in _taught if not _re.match(_PAT, s.replace("<repo>@<object-id>", "r@abc1234")
                                                 .replace("<why>", "x"))]
check("the term's own prose teaches no spelling its pattern would refuse",
      not _bad, f"taught but refused: {_bad}")

# A POSITION MUST RESOLVE BOTH WAYS. `code_paths` stopped being a literal path in 11.0, and
# bin/dmcursor.py's REVERSE lookup — "you are about to touch this file; which being owns it, and what
# does it require you to know" — still compared the argument against the raw declared string. After a
# garden migrated, `dmcursor <a real file>` answered "nothing in the garden claims it" about a file a
# bean plainly claims, which is CHECKLIST Part D's very first instruction returning a falsehood.
codebase("root:tree/src", _FMT)
_f = os.path.join(R, "src", "a.txt")
_c = run(sys.executable, os.path.join(G, "bin", "dmcursor.py"), _f, cwd=G).stdout
check("a file inside a `root:` tree resolves back to the bean that declares it",
      "cursor -> tree" in _c and "root:tree/src" in _c, _c[:400])
# ...and a position this host does NOT hold must not match by coincidence of spelling, which is the
# defect `root:` exists to end: two machines with the same absolute path are two different trees.
_elsewhere = run(sys.executable, os.path.join(G, "bin", "dmcursor.py"),
                 "/home/someone/not-declared-here/x.py", cwd=G).stdout
check("...and a path no declared position covers still resolves to nothing",
      "no bean points at" in _elsewhere, _elsewhere[:300])

shutil.rmtree(T, ignore_errors=True)
print("\nplace: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
