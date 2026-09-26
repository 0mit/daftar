#!/usr/bin/env python3
"""dmpublic: a public repository carries the LANGUAGE, never a garden.

Grows a garden, builds a throwaway repository beside it, and checks that a file, a commit message and a
pull-request body are each refused when they name one of the garden's beans or mappings, of any kind, or the value
of any of its identity anchors, whatever its key — and that a word the published classifications carry, or one
PUBLIC-ALLOW records, is not refused, and one it records for a named file is public in that file only.
"""
import os, sys, subprocess, tempfile, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS = []

def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)

def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:500]))
    if not cond:
        FAILS.append(name)

def run(*a, cwd=None):
    return subprocess.run(list(a), capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd)

T = tempfile.mkdtemp(prefix="dmpub-")
G = os.path.join(T, "g")
run("sh", os.path.join(ROOT, "seed", "germinate.sh"), G, "--gardener", "keeper", cwd=ROOT)
write(os.path.join(G, "beans", "someone.md"),
    '---\nbean: someone\ngenos: person\ntitle: "a person"\nstatus: active\nsummary: "p"\nnature: empsychon\n'
    'identity: { status: confirmed, anchors: [ { key: email, value: "a@example.org", class: logical, establishing: true } ] }\n'
    'provenance: { src: asserted-by-human, by: t, as_of: 2026-01-01 }\nowned_by: { legal: { crown: agape } }\n'
    'responsibility: { legal: { self: true } }\n---\nA person.\n')
write(os.path.join(G, "beans", "quietbox.md"),
    '---\nbean: quietbox\ngenos: host\ntitle: "a machine"\nstatus: active\nsummary: "h"\nnature: soma\n'
    'identity: { status: confirmed, anchors: [ { key: serial, value: "SN-Q1", class: hardware, establishing: true },'
    ' { key: hostname, value: "quietbox.example.org", class: network, establishing: false } ] }\n'
    'provenance: { src: observed, by: t, as_of: 2026-01-01 }\n'
    'owned_by: { legal: { owner: { bean: someone } } }\nresponsibility: { legal: { holder: { bean: someone } } }\n'
    '---\nA machine.\n')

R = os.path.join(T, "repo")
os.makedirs(R)
run("git", "init", "-q", R)
def commit(text, msg, name="doc.md"):
    write(os.path.join(R, name), text)
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
write(body, "This was measured on quietbox.example.org and another machine.\n")
r = dmpublic("--no-files", "--text", body)
check("a pull-request body is checked the same way, including an fqdn anchor",
      r.returncode == 1 and "quietbox.example.org" in r.stdout, r.stdout)
write(body, "This was measured on one host and confirmed on another.\n")
r = dmpublic("--no-files", "--text", body)
check("...and passes once the names are gone", r.returncode == 0, r.stdout + r.stderr)

write(os.path.join(G, "beans", "samba-here.md"),
    '---\nbean: samba\ngenos: product\ntitle: "the file server software"\nstatus: active\nsummary: "s"\nnature: lekton\n'
    'identity: { status: confirmed, anchors: [ { key: product_id, value: "product:samba", class: logical, establishing: true } ] }\n'
    'provenance: { src: asserted-by-human, by: t, as_of: 2026-01-01 }\n'
    'owned_by: { legal: { owner: { bean: someone } } }\nresponsibility: { legal: { holder: { bean: someone } } }\n'
    '---\nSamba.\n')
commit("the vocabulary documents samba, which is public knowledge\n", "neutral")
r = dmpublic()
check("a word the published classifications carry is NOT a leak — a garden cannot make `samba` unsayable",
      r.returncode == 0, r.stdout + r.stderr)

# EVERY ID, NOT THE IDS OF CHOSEN KINDS. The guard once derived its words from a hand list of the kinds that are
# "beings", and a design's id sat in the public law because `design` was not on the list. A design, an agreement, a
# session: what a garden names is the garden's, whatever its kind.
write(os.path.join(G, "beans", "design-lantern-stack.md"),
    '---\nbean: design-lantern-stack\ngenos: design\ntitle: "how the lanterns are wired"\nstatus: active\nsummary: "d"\n'
    'nature: lekton\nprovenance: { src: asserted-by-human, by: t, as_of: 2026-01-01 }\n'
    'owned_by: { legal: { owner: { bean: someone } } }\nresponsibility: { legal: { holder: { bean: someone } } }\n---\nA design.\n')
write(os.path.join(G, "beans", "kettle-share.md"),
    '---\nbean: kettle-share\ngenos: contract\ntitle: "a kettle bought together"\nstatus: active\nsummary: "c"\n'
    'nature: lekton\n'
    'identity: { status: confirmed, anchors: [ { key: contract_id, value: "kettle-2026-17", class: logical, establishing: true } ] }\n'
    'provenance: { src: asserted-by-human, by: t, as_of: 2026-01-01 }\n'
    'owned_by: { legal: { crown: logos } }\n---\nAn agreement.\n')
commit("where that is being taken up, see [[design-lantern-stack]] `open:`\n", "neutral")
r = dmpublic()
check("a DESIGN's id in a public file is refused — the kind of leak the hand-kept list of kinds let through",
      r.returncode == 1 and "design-lantern-stack" in r.stdout and "doc.md" in r.stdout, r.stdout)
commit("the split follows the terms of kettle-share\n", "neutral")
r = dmpublic()
check("...and so is a CONTRACT's: an agreement between two people is theirs, not the language's",
      r.returncode == 1 and "kettle-share" in r.stdout, r.stdout)
write(os.path.join(G, "mappings", "lantern-circuits.md"), "---\nmapping: lantern-circuits\n---\nA mapping.\n")
commit("the table in lantern-circuits lists them\n", "neutral")
r = dmpublic()
check("...and so is a MAPPING's id", r.returncode == 1 and "lantern-circuits" in r.stdout, r.stdout)
# A mapping's id is its `mapping:` field, and a file may be named otherwise: the field is what is guarded.
write(os.path.join(G, "mappings", "wiring.md"), "---\nmapping: porch-feeds\n---\nA mapping.\n")
commit("the table in porch-feeds lists them\n", "neutral")
r = dmpublic()
check("...by its `mapping:` id, when the file is named otherwise", r.returncode == 1 and "porch-feeds" in r.stdout, r.stdout)
write(os.path.join(G, "beans", "daftar.md"),
    '---\nbean: daftar\ngenos: product\ntitle: "the ledger this garden is kept in"\nstatus: active\nsummary: "p"\n'
    'nature: lekton\nprovenance: { src: asserted-by-human, by: t, as_of: 2026-01-01 }\n'
    'owned_by: { legal: { owner: { bean: someone } } }\nresponsibility: { legal: { holder: { bean: someone } } }\n---\nd.\n')
commit("daftar is a ledger kept in git\n", "neutral")
r = dmpublic()
check("...while a word seed/PUBLIC-ALLOW records as public is not refused, though a garden also names a bean by it",
      r.returncode == 0, r.stdout + r.stderr)


# EVERY ANCHOR'S VALUE, NOT THE VALUES OF CHOSEN KEYS. The guard once read hostname, fqdn and ip, and nothing else a
# garden identifies a being by: a person's email, an agreement's id, a serial, the gardener's own qualified name.
commit("write to a@example.org for a copy\n", "neutral")
r = dmpublic()
check("an EMAIL anchor's value in a public file is refused — a person is identified by it",
      r.returncode == 1 and "a@example.org" in r.stdout and "doc.md" in r.stdout, r.stdout)
commit("the agreement is filed as kettle-2026-17\n", "neutral")
r = dmpublic()
check("...and so is a CONTRACT_ID's value — an agreement's own name for itself",
      r.returncode == 1 and "kettle-2026-17" in r.stdout, r.stdout)
commit("a serial like SN-Q1 is printed on the case\n", "neutral")
r = dmpublic()
check("...and a SERIAL's, an anchor key no list named", r.returncode == 1 and "sn-q1" in r.stdout, r.stdout)
_pid = next(l.split('value: "')[1].split('"')[0] for l in open(os.path.join(G, "beans", "keeper.md"), encoding="utf-8")
            if "key: person_id" in l)
_gid = run("git", "-C", G, "rev-list", "--first-parent", "--max-parents=0", "HEAD").stdout.split()[-1][:12]
commit("the gardener is %s\n" % _pid, "neutral")
r = dmpublic()
check("...and the gardener's qualified PERSON_ID", r.returncode == 1 and _pid.lower() in r.stdout, r.stdout)
commit("this came from garden %s\n" % _gid, "neutral")
r = dmpublic()
check("...and the garden's OWN id, read from git as the gate reads it", r.returncode == 1 and _gid in r.stdout, r.stdout)
commit("the catalogue knows product:samba as it knows samba\n", "neutral")
r = dmpublic()
check("...while an anchor value made only of public words (`product:samba`) is not refused", r.returncode == 0,
      r.stdout + r.stderr)

# A CONSENT FOR ONE PAGE IS NOT A CONSENT FOR EVERY FILE. A PUBLIC-ALLOW line may name the files a word is public
# in; anywhere else — another file, a commit message, a pull-request body — the word is guarded as before. Read from
# a copy of the language with its own PUBLIC-ALLOW, so this repository's list is not bent to the test.
L = os.path.join(T, "lang")
shutil.copytree(os.path.join(ROOT, "bin"), os.path.join(L, "bin"))
shutil.copytree(os.path.join(ROOT, "seed", "knowledge"), os.path.join(L, "seed", "knowledge"))
write(os.path.join(L, "seed", "PUBLIC-ALLOW"), "quietbox notes/about.md   # consented to on that page only\n")
def dmpublic_l(*extra):
    return run(sys.executable, os.path.join(L, "bin", "dmpublic.py"), "--garden", G, "--repo", R, *extra)
commit("an example on host-a\n", "neutral")
commit("quietbox is named here, with consent\n", "neutral", name="notes/about.md")
r = dmpublic_l()
check("a word PUBLIC-ALLOW scopes to one file passes in that file", r.returncode == 0, r.stdout + r.stderr)
commit("and quietbox again\n", "neutral")
r = dmpublic_l()
check("...and is refused in any other file", r.returncode == 1 and "doc.md" in r.stdout and "about.md" not in r.stdout,
      r.stdout)
commit("an example on host-a\n", "and quietbox in a message")
r = dmpublic_l("--no-files", "--range", "HEAD~1..HEAD")
check("...and in a commit message", r.returncode == 1 and "quietbox" in r.stdout, r.stdout)
write(body, "measured on quietbox\n")
r = dmpublic_l("--no-files", "--text", body)
check("...and in a pull-request body", r.returncode == 1 and "quietbox" in r.stdout, r.stdout)
commit("an example on host-a\n", "neutral")
commit("quietbox notes/about.md   # consented to on that page only\n", "neutral", name="seed/PUBLIC-ALLOW")
r = dmpublic_l()
check("...while PUBLIC-ALLOW itself may say the word: the line that records the decision has to",
      r.returncode == 0, r.stdout + r.stderr)
_scoped = [l.split("#")[0].split() for l in open(os.path.join(ROOT, "seed", "PUBLIC-ALLOW"), encoding="utf-8")]
_dead = [c for cells in _scoped for c in cells[1:] if not os.path.isfile(os.path.join(ROOT, *c.split("/")))]
check("every file a line of this repository's PUBLIC-ALLOW is scoped to exists", not _dead, _dead)

shutil.rmtree(T, ignore_errors=True)
print("\npublic: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
