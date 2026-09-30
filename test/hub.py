#!/usr/bin/env python3
"""The authenticated writer (PRIV, 24.0; N32): a hub that judges every push again — each commit signed by a key a
writer's bean carries, what it changes within that writer's grants, and the garden it leaves by the gate.

Grows an invented bakery's garden, makes ed25519 keys in a temp dir, and pushes to a bare hub from two clones: the
gardener's and the baker's. The keys are SSH keys where `ssh-keygen -Y` can check a signature, and OpenPGP keys, in a
keyring of the test's own, where it cannot and `gpg` is there: the hub reads both. Skipped, saying why, where neither is.

THE HUB RUNS ONLY CODE THE GARDENER LET IN: a writer granted `write` on a bean is refused a change to the gate, to a
file a release keeps, to `.gitattributes`, to a Python file wherever it is, and to the drawing module a page names; and
a commit with no parent, whose own tree would name its writers, is refused by a hub that already holds the garden.
"""
import os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
FAILS = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:900]))
    if not cond:
        FAILS.append(name)


def run(*a, cwd=None, inp=None):
    return subprocess.run(list(a), capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd, input=inp)


SSH = bool(shutil.which("ssh-keygen")) and \
    "check-novalidate" in run("ssh-keygen", "-Y", "x").stderr + run("ssh-keygen", "-?").stderr
if not SSH and not shutil.which("gpg"):
    print("SKIP  this machine has neither an ssh-keygen that can check a signature (`ssh-keygen -Y check-novalidate`, "
          "OpenSSH 8.2 and later) nor gpg: the hub's signature check cannot be shown here\n\nhub: 0 failed")
    sys.exit(0)
ANCHOR = "ssh_key_fingerprint" if SSH else "openpgp_fingerprint"
ESTABLISHING = "false" if SSH else "true"         # the law's own: an OpenPGP key establishes who; an SSH key corroborates
print(f"(the keys are {'SSH' if SSH else 'OpenPGP'} keys: {ANCHOR})")

T = tempfile.mkdtemp(prefix="dmhub-")
if not SSH:
    os.environ["GNUPGHOME"] = os.path.join(T, "gnupg")       # the test's own keyring: the pushes and the hub read it
    os.makedirs(os.environ["GNUPGHOME"], mode=0o700)
G, HUB, BAKER = (os.path.join(T, n) for n in ("g", "hub.git", "baker"))
r = run("sh", os.path.join(ROOT, "seed", "germinate.sh"), G, "--gardener", "keeper", cwd=ROOT)
check("a garden germinates from the release", r.returncode == 0 and "0 error" in r.stdout, r.stdout + r.stderr)


def key(name):
    """(what git signs with, the fingerprint a bean carries)."""
    if not SSH:
        run("gpg", "--batch", "--pinentry-mode", "loopback", "--passphrase", "", "--quick-gen-key",
            f"{name} <{name}@example.org>", "ed25519", "sign", "never")
        out = run("gpg", "--with-colons", "--list-secret-keys", f"{name}@example.org").stdout
        fpr = re.search(r"^fpr:+([0-9A-F]{40,64}):", out, re.M).group(1)
        return fpr, fpr
    p = os.path.join(T, name + "-key")
    run("ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", name, "-f", p)
    fpr = re.search(r"(SHA256:[A-Za-z0-9+/]{43})", run("ssh-keygen", "-lf", p + ".pub").stdout).group(1)
    return p, fpr


KEEPER_KEY, KEEPER_FPR = key("keeper")
BAKER_KEY, BAKER_FPR = key("baker")


def signing(where, k):
    for a in (("gpg.format", "ssh" if SSH else "openpgp"), ("user.signingkey", k), ("commit.gpgsign", "true")):
        run("git", "config", *a, cwd=where)


def write(where, rel, text):
    p = os.path.join(where, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def read(where, rel):
    with open(os.path.join(where, *rel.split("/")), encoding="utf-8") as fh:
        return fh.read()


def save(where, who, what, names):
    r = run(PY, "bin/dmsave.py", who, what, "--body", "- action: " + " ".join(f"[[{n}]]" for n in names), cwd=where)
    return r.returncode, r.stdout + r.stderr


def push(where):
    r = run("git", "push", "-q", "origin", "HEAD:" + BRANCH, cwd=where)
    return r.returncode, r.stdout + r.stderr


def doc(bid, what):
    return f"""---
bean: {bid}
genos: document
title: "{what}"
status: active
summary: "{what}"
nature: lekton
owned_by: {{ owner: {{ bean: keeper }} }}
identity: {{ status: confirmed, anchors: [ {{ key: identifier, value: "document:{bid}", class: logical, establishing: true }} ] }}
provenance: {{ src: asserted-by-human, by: keeper, as_of: now }}
located_at: [ {{ system: unix-filesystem, openness: unknown }} ]
---
{what}.
"""


# ---- the gardener's key is in the garden before the hub exists: trust starts from the gardener
BRANCH = run("git", "branch", "--show-current", cwd=G).stdout.strip()
k = read(G, "beans/keeper.md")
write(G, "beans/keeper.md", k.replace("establishing: true }\nprovenance",
                                      f"establishing: true }}\n    - {{ key: {ANCHOR}, value: \"{KEEPER_FPR}\", class: logical, establishing: {ESTABLISHING} }}\nprovenance", 1))
write(G, "beans/oven-log.md", doc("oven-log", "the oven's log"))
code, out = save(G, "keeper (test)", "the gardener's key, and the oven's log", ["keeper", "oven-log"])
check("the gardener's signing key is recorded as an anchor on the gardener's bean", code == 0, out[-1200:])
run("git", "clone", "-q", "--bare", G, HUB)
r = run(PY, "bin/dmhub.py", "install", HUB, cwd=G)
check("dmhub install writes the hub's pre-receive hook", r.returncode == 0 and os.path.isfile(os.path.join(HUB, "hooks", "pre-receive")), r.stdout + r.stderr)
run("git", "remote", "add", "origin", HUB, cwd=G)

# ---- 1. unsigned (said here, so a machine that signs every commit by default still makes one that is not)
run("git", "config", "commit.gpgsign", "false", cwd=G)
write(G, "beans/bread-note.md", doc("bread-note", "the bread notes"))
code, out = save(G, "keeper (test)", "the bread notes", ["bread-note"])
code, out = push(G)
check("an unsigned push is refused", code != 0 and "is not signed" in out, out[-1200:])
run("git", "reset", "-q", "--hard", "origin/" + BRANCH, cwd=G) if run("git", "rev-parse", "origin/" + BRANCH, cwd=G).returncode == 0 else run("git", "reset", "-q", "--hard", "HEAD~1", cwd=G)

# ---- 2. signed by a key no bean carries
signing(G, BAKER_KEY)
write(G, "beans/bread-note.md", doc("bread-note", "the bread notes"))
code, out = save(G, "keeper (test)", "the bread notes", ["bread-note"])
code, out = push(G)
check("a push signed by a key no bean carries is refused", code != 0 and "which no bean carries" in out, out[-1200:])
run("git", "reset", "-q", "--hard", "HEAD~1", cwd=G)

# ---- 3. the gardener adds the baker, her key and her grant
signing(G, KEEPER_KEY)
write(G, "beans/bake-2026.md", f"""---
bean: bake-2026
genos: contract
title: "bake-2026"
status: active
summary: "the baker's terms"
nature: lekton
owned_by: {{ crown: true }}
responsibility: {{ legal: {{ parties: true }} }}
identity: {{ status: confirmed, anchors: [ {{ key: identifier, value: "contract:bake-2026", class: logical, establishing: true }} ] }}
provenance: {{ src: asserted-by-human, by: keeper, as_of: now }}
parties:
  bakery: {{ who: {{ bean: keeper }}, accepted: 2026-09-01 }}
  baker: {{ who: {{ bean: baker }}, accepted: 2026-09-01 }}
words: {{ form: spoken, agreed: 2026-09-01 }}
---
The baker's terms.
""")
write(G, "beans/baker.md", f"""---
bean: baker
genos: person
title: "baker"
status: active
summary: "the baker"
nature: soma
owned_by: {{ crown: true }}
responsibility: {{ legal: {{ self: true }} }}
identity: {{ status: confirmed, anchors: [ {{ key: identifier, value: "person:baker", class: logical, establishing: true }}, {{ key: {ANCHOR}, value: "{BAKER_FPR}", class: logical, establishing: {ESTABLISHING} }} ] }}
provenance: {{ src: asserted-by-human, by: keeper, as_of: now }}
consent: {{ bean: bake-2026 }}
---
The baker.
""")
write(G, "beans/bread-note.md", doc("bread-note", "the bread notes"))
k = read(G, "beans/keeper.md")
write(G, "beans/keeper.md", k.replace("\n---\n", """
selections:
  notes: { what: "the bread notes", steps: [ { id: n, op: select, genos: document, where: [ { path: bean, is: bread-note } ] } ] }
grants:
  baker-writes-notes: { act: write, over: notes, audience: { who: baker }, why: "the baker keeps the bread notes" }
---
""", 1))
code, out = save(G, "keeper (test)", "the baker, her key, and what she may write", ["bake-2026", "baker", "bread-note", "keeper"])
check("the gardener saves the baker's bean, key and grant", code == 0, out[-1200:])
code, out = push(G)
check("…and the gardener's signed push is accepted", code == 0, out[-1500:])

# ---- 4. the baker writes what her grant opens, and not what it does not
r = run("git", "clone", "-q", HUB, BAKER)
check("the baker clones the hub", r.returncode == 0, r.stdout + r.stderr)
signing(BAKER, BAKER_KEY)
run(PY, "bin/install.py", cwd=BAKER)
run("git", "config", "user.name", "baker", cwd=BAKER)
run("git", "config", "user.email", "baker@example.org", cwd=BAKER)
write(BAKER, "beans/bread-note.md", doc("bread-note", "the bread notes").replace("the bread notes.", "Rye: two days' levain."))
code, out = save(BAKER, "baker (test)", "rye", ["bread-note"])
check("the baker saves her edit in her own clone", code == 0, out[-1200:])
code, out = push(BAKER)
check("the baker's signed push, within her grant, is accepted", code == 0, out[-1500:])
write(BAKER, "beans/oven-log.md", doc("oven-log", "the oven's log").replace("the oven's log.", "Fired at six."))
code, out = save(BAKER, "baker (test)", "the oven", ["oven-log"])
check("the baker saves an edit to the oven's log in her own clone", code == 0, out[-1200:])
code, out = push(BAKER)
check("…one it does not open is refused, naming the missing grant",
      code != 0 and "baker may not make it" in out and "beans/oven-log.md needs a grant of `write`" in out, out[-1500:])
run("git", "reset", "-q", "--hard", "HEAD~1", cwd=BAKER)

# ---- 4b. code is the gardener's: a writer's grant to write a bean opens no file the hub or a host would run
def attempt(where, rel, text, what):
    """Commit one file as the writer (the hub judges it, whatever the writer's own hook says), push, put it back."""
    write(where, rel, text)
    run("git", "add", "-A", cwd=where)
    run("git", "commit", "-q", "--no-verify", "-m", what, cwd=where)
    code, out = push(where)
    run("git", "reset", "-q", "--hard", "HEAD~1", cwd=where)
    run("git", "clean", "-qfd", cwd=where)
    return code, out


for rel, what in (("bin/dmcheck.py", "the gate itself, which the hub runs"),
                  (".gitattributes", "what a merge dispatches to"),
                  ("work/notes.py", "a Python file in no layer")):
    old = read(BAKER, rel) if os.path.isfile(os.path.join(BAKER, *rel.split("/"))) else ""
    code, out = attempt(BAKER, rel, old + "\n# the baker was here\n", f"a change to {rel}")
    check(f"a writer's change to {rel} ({what}) is refused at the hub, naming `ratify:G`",
          code != 0 and "baker may not make it" in out and f"{rel} needs a grant of `ratify:G`" in out, out[-1500:])
note = read(BAKER, "beans/bread-note.md")
code, out = attempt(BAKER, "beans/bread-note.md", note.replace("\n---\n", '\nview: { drawings: "file:work/draw.py" }\n---\n', 1),
                    "the bread notes name a drawing module")
check("a writer who may write a bean may not make it name a drawing module (`view.drawings`): `ratify:G`",
      code != 0 and "beans/bread-note.md needs a grant of `ratify:G`" in out, out[-1500:])

# ---- 4c. a commit with no parent names its own writers, and a hub that holds the garden refuses it
run("git", "checkout", "-q", "--orphan", "stray", cwd=BAKER)
write(BAKER, "GARDEN.md", re.sub(r"(?m)^gardener: *\S+", "gardener: baker", read(BAKER, "GARDEN.md"), count=1))
run("git", "add", "-A", cwd=BAKER)
run("git", "commit", "-q", "--no-verify", "-m", "a garden of my own", cwd=BAKER)
r = run("git", "push", "-q", "origin", "HEAD:refs/heads/stray", cwd=BAKER)
check("a signed commit with no parent, naming its signer as gardener, is refused by a hub that holds the garden",
      r.returncode != 0 and "it has no parent" in r.stdout + r.stderr, (r.stdout + r.stderr)[-1500:])
run("git", "checkout", "-q", "-f", BRANCH, cwd=BAKER)
run("git", "branch", "-q", "-D", "stray", cwd=BAKER)

# ---- 5. a commit that breaks the gate
run("git", "pull", "-q", "--rebase", "origin", BRANCH, cwd=G)
write(G, "beans/bread-note.md", read(G, "beans/bread-note.md").replace("genos: document", "genos: loaf"))
run("git", "add", "-A", cwd=G)
run("git", "commit", "-q", "--no-verify", "-m", "a genos no law has", cwd=G)
code, out = push(G)
check("a signed commit whose garden fails the gate is refused at the hub", code != 0 and "does not pass the gate" in out, out[-1500:])

shutil.rmtree(T, ignore_errors=True)
print(f"\nhub: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
