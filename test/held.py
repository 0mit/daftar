#!/usr/bin/env python3
"""The held layer (PRIV, 24.0; N30, F13, S6): material a garden keeps OFF git, in a store this host resolves through its
`roots`, pointed at from a bean by an opaque pointer — sealed by bin/dmheld.py, journalled in one line, erased per
subject, and checked where the store is, never by the gate.

Grows a garden and commits an invented vet's practice through its hook: a client minted opaque, her scanned letter
sealed on the service agreement she accepted, and her erasure.
"""
import os, re, shutil, socket, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
FAILS = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:900]))
    if not cond:
        FAILS.append(name)


def run(*a, cwd=None):
    return subprocess.run(list(a), capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd)


T = tempfile.mkdtemp(prefix="dmheld-")
G = os.path.join(T, "g")
STORE = os.path.join(T, "vault")
HOST = socket.gethostname().lower()
r = run("sh", os.path.join(ROOT, "seed", "germinate.sh"), G, "--gardener", "keeper", cwd=ROOT)
check("a garden germinates from the release, and the law with the held layer loads",
      r.returncode == 0 and "0 error" in r.stdout, r.stdout + r.stderr)


def write(rel, text):
    p = os.path.join(G, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def read(rel):
    with open(os.path.join(G, *rel.split("/")), encoding="utf-8") as fh:
        return fh.read()


def save(what, body):
    r = run(PY, "bin/dmsave.py", "keeper (test)", what, "--body", body, cwd=G)
    return r.returncode, r.stdout + r.stderr


def held(*a):
    r = run(PY, "bin/dmheld.py", *a, cwd=G)
    return r.returncode, r.stdout + r.stderr


def restore():
    run("git", "reset", "-q", "--hard", cwd=G)
    run("git", "clean", "-qfd", cwd=G)


def gate():
    r = run(PY, "bin/dmcheck.py", "--all", cwd=G)
    return r.stdout + r.stderr


OWN = "owned_by: { legal: { owner: { bean: keeper } } }\nresponsibility: { legal: { holder: { bean: keeper } } }\n"
write("beans/this-host.md", f"""---
bean: this-host
genos: host
title: "the practice's laptop"
status: active
summary: "the machine the practice's records are kept on"
nature: soma
os: linux
identity: {{ status: confirmed, anchors: [ {{ key: hostname, value: "{HOST}", class: network, establishing: false }}, {{ key: serial, value: "SN-VET-1", class: hardware, establishing: true }} ] }}
provenance: {{ src: asserted-by-human, by: keeper, as_of: now }}
{OWN}roots:
  vault: {{ system: unix-filesystem, at: "{HOST}:{STORE}", observed: 2026-09-01, keeps: personal, controller: keeper, readable_from: this-host, backup: "copied to a second disk each week" }}
---
The practice's laptop.
""")
code, out = save("the practice's laptop, and its store", "- action: added [[this-host]], whose root `vault` keeps personal material off git.")
check("a root that keeps personal material, on this host, is saved", code == 0, out)

code, out = held("person", "name=Wren Ash", "phone=+15555550100")
pid = (re.search(r"(p-[0-9a-f]{8})", out) or [None])[0] if code == 0 else None
check("dmheld person mints an opaque id, and holds the name and the phone off git", pid is not None, out)
code, out = save("a client", f"- action: added [[{pid}]], a client minted opaque.")
check("the opaque client is saved", code == 0, out)

write("beans/service-2026.md", f"""---
bean: service-2026
genos: contract
title: "service-2026"
status: active
summary: "the service agreement the client accepted"
nature: lekton
owned_by: {{ legal: {{ crown: logos }} }}
responsibility: {{ legal: {{ parties: true }} }}
identity: {{ status: confirmed, anchors: [ {{ key: contract_id, value: "contract:service-2026", class: logical, establishing: true }} ] }}
provenance: {{ src: asserted-by-human, by: keeper, as_of: now }}
parties:
  practice: {{ who: {{ bean: keeper }}, accepted: 2026-09-01 }}
  client: {{ who: {{ bean: {pid} }}, accepted: 2026-09-01 }}
words: {{ form: spoken, agreed: 2026-09-01 }}
---
The service agreement.
""")
write("beans/intake-letter.md", f"""---
bean: intake-letter
genos: document
title: "an intake letter"
status: active
summary: "a client's letter, scanned at intake"
nature: lekton
{OWN}identity: {{ status: confirmed, anchors: [ {{ key: doc_id, value: "document:intake-letter", class: logical, establishing: true }} ] }}
provenance: {{ src: asserted-by-human, by: keeper, as_of: now }}
about: [ {{ who: {pid} }} ]
located_at: [ {{ system: unix-filesystem, openness: here, at: "{HOST}:/srv/scans/letter.pdf" }} ]
refs:
  letter-scan: {{ bean: service-2026, rel: received-under }}
---
A letter.
""")
code, out = save("the agreement and the letter", "- action: added [[service-2026]] and [[intake-letter]].")
check("a document `about` the client, and the agreement she accepted, are saved", code == 0, out)

# ---- sealing an entry of an open map
code, out = held("put", "intake-letter", "refs", "letter-scan", "--basis", "service-2026")
ptr = (re.search(r"(root:vault/[0-9a-f]{32})", out) or [None])[0]
line = (re.search(r"(- held: intake-letter \S+ added)", out) or [None])[0]
check("dmheld put seals an entry, and prints its pointer and its one journal line", code == 0 and ptr and line, out)
text = read("beans/intake-letter.md")
check("the bean keeps only the pointer, under a key that is the pointer's first eight digits",
      f'h-{ptr[11:19]}: {{ held: "{ptr}", basis: {{ bean: service-2026 }} }}' in text
      and "letter-scan" not in text, text)
code, out = save("the letter sealed", "- action: sealed an entry of [[intake-letter]].")
check("F13: a commit that seals an entry without its `- held:` line is refused by name",
      code != 0 and "- held: intake-letter refs.h-" in out, out)
with open(os.path.join(G, "log", "journal.md"), "a", encoding="utf-8", newline="\n") as fh:
    fh.write(line + "\n")
r = run(PY, "bin/dmsave.py", "--again", cwd=G)
check("…and passes with it", r.returncode == 0, r.stdout + r.stderr)
code, out = held("resolve", ptr)
check("dmheld resolve reads the entry back from the store", code == 0 and "letter-scan" in out and "service-2026" in out, out)
code, out = held("check")
check("dmheld check: every pointer resolves here", code == 0 and "0 error" in out, out)

# ---- what the gate refuses of a sealed entry
text = read("beans/intake-letter.md")
write("beans/intake-letter.md", text.replace(f"h-{ptr[11:19]}:", "letter-scan:"))
out = gate()
check("a sealed entry keyed by its name is refused: a key says nothing either",
      "a sealed entry's key is `h-" in out, out[-1500:])
write("beans/intake-letter.md", text.replace(", basis: { bean: service-2026 }", ""))
out = gate()
check("a sealed entry held on nothing, on a bean about another person, is refused",
      "is held on nothing" in out, out[-1500:])
write("beans/intake-letter.md", text.replace("service-2026 } }", "service-2026 }, rel: received-under }"))
out = gate()
check("a sealed entry that still says something beside its pointer is refused", "holds ['rel'] beside it" in out, out[-1500:])
write("beans/intake-letter.md", text.replace(ptr, "root:vault/letter"))
out = gate()
check("a pointer that is not minted is refused by the type's own words", "32 lowercase hexadecimal" in out, out[-1500:])
restore()

# ---- a save refuses a pointer this host does not hold
text = read("beans/intake-letter.md")
write("beans/intake-letter.md", text.replace("located_at: [", "located_at: [ { held: \"root:vault/" + "0" * 32 + "\", basis: { bean: service-2026 } }, "))
code, out = save("a pointer from nowhere", "- action: a pointer to nothing.\n- held: intake-letter located_at added")
check("dmsave refuses a pointer that resolves to nothing on this host: the hook its commit runs says so",
      code != 0 and "holds nothing here" in out and run("git", "diff", "HEAD", "--quiet", cwd=G).returncode != 0, out)
run("git", "reset", "-q", cwd=G)
# A PLAIN COMMIT IS JUDGED AS THE SAVE IS (guards-after-parts-1-10, fix 2): the hook runs on the host, and asks dmheld.
r = run(PY, "bin/dmjournal.py", "keeper (test)", "a pointer from nowhere, by hand", "--body",
        "- action: a pointer to nothing.\n- held: intake-letter located_at added", cwd=G)
run("git", "add", "-A", cwd=G)
r = run("git", "commit", "-q", "-m", "a pointer from nowhere, by hand", cwd=G)
check("...and so does a plain `git commit` of the same, which the gate alone would let through",
      r.returncode != 0 and "holds nothing here" in r.stdout + r.stderr
      and run(PY, "bin/dmheld.py", "new", "--staged", cwd=G).returncode == 1, (r.stdout + r.stderr)[-1500:])
restore()
code, out = held("new", "--staged")
check("...and with nothing added, `dmheld new --staged` is silent and passes", code == 0 and out == "", out)

# ---- nothing of her is in git
blobs = run("git", "log", "-p", "--all", cwd=G).stdout
check("nothing of the client — her name, her phone, the scan's name — is in any blob of the history",
      "Wren" not in blobs and "5555550100" not in blobs and "letter-scan" not in blobs.split("sealed")[-1], "")

# ---- erasure
code, out = held("erase", pid)
check("dmheld erase deletes every record the client is in", code == 0 and "erased 2 held record" in out, out)
code, out = held("resolve", ptr)
check("…and the pointer resolves to Erased, never to an error of the bean", code != 0 and "erased for its subject" in out, out)
code, out = held("check")
check("dmheld check: an erased pointer is no finding", code == 0 and "0 error(s), 0 warning" in out, out)

# ---- the store's own cell
text = read("beans/this-host.md")
write("beans/this-host.md", text.replace("keeps: personal", "keeps: special-category").replace("readable_from: this-host", "readable_from: remote"))
out = gate()
check("a root keeping special-category material in cleartext, readable from a remote party, warns in breach",
      "special-category material stored in cleartext" in out and " 0 error" in out, out[-1500:])
restore()

shutil.rmtree(T, ignore_errors=True)
print(f"\nheld: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
