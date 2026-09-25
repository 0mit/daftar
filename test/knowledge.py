#!/usr/bin/env python3
"""The `knowledge` profile (std-vocab 9.1): universal anchors from published classifications.

Grows a garden with seed/germinate.sh, opts it into the profile, and checks that the gate accepts real codes
and refuses invented ones — as anchors and as `knowledge:` entries — and that dmknowledge resolves them.
"""
import os, sys, subprocess, tempfile, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS = []

def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:500]))
    if not cond:
        FAILS.append(name)

def run(*a, cwd=None):
    return subprocess.run(list(a), capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd)

T = tempfile.mkdtemp(prefix="dmknow-")
G = os.path.join(T, "g")
r = run("sh", os.path.join(ROOT, "seed", "germinate.sh"), G, "--gardener", "keeper", cwd=ROOT)
check("a garden germinates with seed/knowledge/ in the language", r.returncode == 0 and os.path.exists(os.path.join(G, "seed", "knowledge", "isco-08.tsv")), r.stdout + r.stderr)

v = os.path.join(G, "VOCAB.md"); s = open(v).read()
if "extends_profiles:" in s:
    s = s.replace("extends_profiles: [", "extends_profiles: [knowledge, ", 1).replace("extends_profiles: []", "extends_profiles: [knowledge]")
else:
    s = s.replace("\n---", "\nextends_profiles: [knowledge]\n---", 1)
open(v, "w").write(s)

def bean(name, body):
    open(os.path.join(G, "beans", name + ".md"), "w").write("---\n" + body + "---\n\n" + name + "\n")

def gate():
    return run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G)

OWN = 'owned_by: { legal: { owner: { bean: someone } } }\nresponsibility: { legal: { holder: { bean: someone } } }\n'
bean("someone", 'bean: someone\ngenos: person\ntitle: "a person"\nstatus: active\nsummary: "p"\nnature: empsychon\n'
     'identity: { status: confirmed, anchors: [ { key: email, value: "a@example.org", class: logical, establishing: true } ] }\n'
     'provenance: { src: asserted-by-human, by: t, as_of: 2026-01-01 }\nowned_by: { legal: { crown: agape } }\nresponsibility: { legal: { self: true } }\n')
bean("file-server", 'bean: file-server\ngenos: product\ntitle: "a file server product"\nstatus: active\nsummary: "the SMB server software"\nnature: lekton\n'
     'identity: { status: confirmed, anchors: [ { key: technology, value: samba, class: logical, establishing: true } ] }\n'
     'provenance: { src: asserted-by-human, by: t, as_of: 2026-01-01 }\n' + OWN +
     'knowledge:\n  - { scheme: technology, code: samba, rel: classified_as }\n  - { scheme: isced-f-2013, code: "0612", rel: draws_on, topic: "network file sharing" }\n'
     '  - { scheme: isco-08, code: "2522", rel: classified_as, note: "who runs it" }\n')
r = gate()
check("real codes pass: a technology anchor and knowledge entries in three schemes", "0 error" in r.stdout + r.stderr, r.stdout[-1500:] + r.stderr[-800:])

bean("bad-anchor", 'bean: bad-anchor\ngenos: product\ntitle: "x"\nstatus: active\nsummary: "x"\nnature: lekton\n'
     'identity: { status: confirmed, anchors: [ { key: isco_08, value: "9999", class: logical, establishing: true } ] }\n'
     'provenance: { src: asserted-by-human, by: t, as_of: 2026-01-01 }\n' + OWN)
r = gate()
check("an invented ISCO-08 code as an anchor is refused", "anchor isco_08='9999' is not a isco-08 code" in r.stdout + r.stderr, r.stdout[-1200:])
os.remove(os.path.join(G, "beans", "bad-anchor.md"))

bean("bad-entry", 'bean: bad-entry\ngenos: product\ntitle: "x"\nstatus: active\nsummary: "x"\nnature: lekton\n'
     'identity: { status: confirmed, anchors: [ { key: technology, value: postfix, class: logical, establishing: true } ] }\n'
     'provenance: { src: asserted-by-human, by: t, as_of: 2026-01-01 }\n' + OWN +
     'knowledge:\n  - { scheme: isced-f-2013, code: "0699", rel: draws_on }\n  - { scheme: nonsense, code: "1", rel: uses }\n')
r = gate(); out = r.stdout + r.stderr
check("a code checked against the scheme its entry names is refused when absent", "'0699' is not a declared isced-f-2013" in out, out[-1200:])
check("an unknown scheme is refused", "'nonsense' is not a declared knowledge_schemes" in out, out[-1200:])
os.remove(os.path.join(G, "beans", "bad-entry.md"))

r = run(sys.executable, os.path.join(G, "bin", "dmknowledge.py"), "bean", "file-server", cwd=G)
check("dmknowledge resolves a bean's knowledge, with the official documentation", "https://www.samba.org/samba/docs/" in r.stdout and "Database and network design" in r.stdout, r.stdout + r.stderr)
r = run(sys.executable, os.path.join(G, "bin", "dmknowledge.py"), "show", "isco-08", "2522", cwd=G)
check("dmknowledge shows an occupation's ancestry", "Professionals" in r.stdout and "2522" in r.stdout, r.stdout + r.stderr)

os.rename(os.path.join(G, "seed", "knowledge", "technology.tsv"), os.path.join(G, "seed", "knowledge", "t.bak"))
r = gate(); out = r.stdout + r.stderr
check("a declared registry file that is missing is an error, never an empty list", "technology" in out and "missing" in out and "0 error" not in out, out[-800:])
shutil.rmtree(T, ignore_errors=True)
print("\nknowledge: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
