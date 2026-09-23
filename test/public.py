#!/usr/bin/env python3
"""dmpublic: a public repository carries the LANGUAGE, never a garden.

Grows a garden, builds a throwaway repository beside it, and checks that a file, a commit message and a
pull-request body are each refused when they name one of the garden's beings — and that a word the
published classifications carry, or one PUBLIC-ALLOW records, is not refused.
"""
import os, sys, subprocess, tempfile, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS = []

def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:500]))
    if not cond:
        FAILS.append(name)

def run(*a, cwd=None):
    return subprocess.run(list(a), capture_output=True, text=True, cwd=cwd)

T = tempfile.mkdtemp(prefix="dmpub-")
G = os.path.join(T, "g")
run("sh", os.path.join(ROOT, "seed", "germinate.sh"), G, "--gardener", "keeper", cwd=ROOT)
open(os.path.join(G, "beans", "someone.md"), "w").write(
    '---\nbean: someone\nkind: person\ntitle: "a person"\nstatus: active\nsummary: "p"\nnature: living\n'
    'identity: { status: confirmed, anchors: [ { key: email, value: "a@example.org", class: logical, establishing: true } ] }\n'
    'provenance: { src: asserted-by-human, by: t, as_of: 2026-01-01 }\nowned_by: { legal: { crown: love } }\n'
    'responsibility: { legal: { self: true } }\n---\nA person.\n')
open(os.path.join(G, "beans", "quietbox.md"), "w").write(
    '---\nbean: quietbox\nkind: host\ntitle: "a machine"\nstatus: active\nsummary: "h"\nnature: physical\n'
    'identity: { status: confirmed, anchors: [ { key: serial, value: "SN-Q1", class: hardware, establishing: true },'
    ' { key: hostname, value: "quietbox.example.org", class: network, establishing: false } ] }\n'
    'provenance: { src: observed, by: t, as_of: 2026-01-01 }\n'
    'owned_by: { legal: { owner: { bean: someone } } }\nresponsibility: { legal: { holder: { bean: someone } } }\n'
    '---\nA machine.\n')

R = os.path.join(T, "repo")
os.makedirs(R)
run("git", "init", "-q", R)
def commit(text, msg):
    open(os.path.join(R, "doc.md"), "w").write(text)
    run("git", "-C", R, "add", "-A")
    return run("git", "-C", R, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", msg)

def dmpublic(*extra):
    return run(sys.executable, os.path.join(ROOT, "bin", "dmpublic.py"), "--garden", G, "--repo", R, *extra)

commit("an example on host-a, under /home/user/tree\n", "a neutral message")
r = dmpublic()
check("a file that names no being passes", r.returncode == 0, r.stdout + r.stderr)
commit("we measured this on quietbox, which holds the tree\n", "a neutral message")
r = dmpublic()
check("a file that names a host bean is refused, with the file and the word",
      r.returncode == 1 and "quietbox" in r.stdout and "doc.md" in r.stdout, r.stdout)
commit("an example on host-a\n", "fixed the thing on quietbox")
r = dmpublic("--no-files", "--range", "HEAD~1..HEAD")
check("a COMMIT MESSAGE that names it is refused too — the prose nobody greps",
      r.returncode == 1 and "quietbox" in r.stdout, r.stdout)
body = os.path.join(T, "pr.md")
open(body, "w").write("This was measured on quietbox.example.org and another machine.\n")
r = dmpublic("--no-files", "--text", body)
check("a pull-request body is checked the same way, including an fqdn anchor",
      r.returncode == 1 and "quietbox.example.org" in r.stdout, r.stdout)
open(body, "w").write("This was measured on one host and confirmed on another.\n")
r = dmpublic("--no-files", "--text", body)
check("...and passes once the names are gone", r.returncode == 0, r.stdout + r.stderr)

open(os.path.join(G, "beans", "samba-here.md"), "w").write(
    '---\nbean: samba\nkind: product\ntitle: "the file server software"\nstatus: active\nsummary: "s"\nnature: metaphysical\n'
    'identity: { status: confirmed, anchors: [ { key: product_id, value: "product:samba", class: logical, establishing: true } ] }\n'
    'provenance: { src: asserted-by-human, by: t, as_of: 2026-01-01 }\n'
    'owned_by: { legal: { owner: { bean: someone } } }\nresponsibility: { legal: { holder: { bean: someone } } }\n'
    '---\nSamba.\n')
commit("the vocabulary documents samba, which is public knowledge\n", "neutral")
r = dmpublic()
check("a word the published classifications carry is NOT a leak — a garden cannot make `samba` unsayable",
      r.returncode == 0, r.stdout + r.stderr)

shutil.rmtree(T, ignore_errors=True)
print("\npublic: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
