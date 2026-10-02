#!/usr/bin/env python3
"""public: a public repository carries the LANGUAGE, never a garden (v1 part 12: in a garden of the core).

Grows a garden of the core (test/grow.py), builds a throwaway repository beside it, and checks that a file, a commit
message and a pull-request body are each refused when they name one of the garden's beans, of any kind, or the text of
any of its `name` statements, whatever the namespace — and that a word the published classifications carry, or one
PUBLIC-ALLOW records, is not refused, and one it records for a named file is public in that file only. (A mapping is a
bean of its kind in the core, and a name a garden minted for a bean is its bean's id: test/ported.yaml.)
"""
import os, sys, subprocess, tempfile, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "test"))
import grow  # noqa: E402
FAILS = []


def bean(bid, kind, title, *statements, extra=""):
    """A bean of the core: its kind, its title, what it says, known by one act."""
    return (f'---\nbean: {bid}\nkind: {kind}\ntitle: "{title}"\nstatements:\n  - say: {{ by: keeper, at: "2026-01-01" }}\n'
            + "".join(f"  - {x}\n" for x in statements) + extra + f"---\n{title}.\n")

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
_g = grow.garden(grow.release(os.path.join(T, "release")), G, "keeper")
assert _g.returncode == 0, _g.out
write(os.path.join(G, "beans", "someone.md"), bean("someone", "person", "a person", "own: { by: theone, of: self }",
                                                   'name: { by: mail, of: self, as: "a@example.org" }'))
write(os.path.join(G, "beans", "quietbox.md"), bean("quietbox", "host", "a machine", "own: { by: someone, of: self }",
                                                    'name: { by: makers, of: self, as: "SN-Q1" }',
                                                    "name: { by: dns, of: self, as: quietbox.example.org }"))

R = os.path.join(T, "repo")
os.makedirs(R)
run("git", "init", "-q", R)
def commit(text, msg, name="doc.md"):
    write(os.path.join(R, name), text)
    run("git", "-C", R, "add", "-A")
    return run("git", "-C", R, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", msg)

def dmpublic(*extra):
    return run(sys.executable, os.path.join(ROOT, "bin", "public.py"), "--garden", G, "--repo", R, *extra)

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

write(os.path.join(G, "beans", "samba.md"), bean("samba", "product", "the file server software", "own: { by: someone, of: self }"))
commit("the vocabulary documents samba, which is public knowledge\n", "neutral")
r = dmpublic()
check("a word the published classifications carry is NOT a leak — a garden cannot make `samba` unsayable",
      r.returncode == 0, r.stdout + r.stderr)

# EVERY ID, NOT THE IDS OF CHOSEN KINDS. The guard once derived its words from a hand list of the kinds that are
# "beings", and a design's id sat in the public law because `design` was not on the list. A design, an agreement, a
# session: what a garden names is the garden's, whatever its kind.
write(os.path.join(G, "beans", "design-lantern-stack.md"), bean("design-lantern-stack", "design", "how the lanterns are wired",
                                                                "own: { by: someone, of: self }"))
write(os.path.join(G, "beans", "kettle-share.md"), bean("kettle-share", "contract", "a kettle bought together",
                                                        'name: { by: kettles, of: self, as: "kettle-2026-17" }'))
commit("where that is being taken up, see [[design-lantern-stack]] `open:`\n", "neutral")
r = dmpublic()
check("a DESIGN's id in a public file is refused — the kind of leak the hand-kept list of kinds let through",
      r.returncode == 1 and "design-lantern-stack" in r.stdout and "doc.md" in r.stdout, r.stdout)
commit("the split follows the terms of kettle-share\n", "neutral")
r = dmpublic()
check("...and so is a CONTRACT's: an agreement between two people is theirs, not the language's",
      r.returncode == 1 and "kettle-share" in r.stdout, r.stdout)
write(os.path.join(G, "beans", "daftar.md"), bean("daftar", "product", "the ledger this garden is kept in",
                                                  "own: { by: someone, of: self }"))
commit("daftar is a ledger kept in git\n", "neutral")
r = dmpublic()
check("...while a word seed/PUBLIC-ALLOW records as public is not refused, though a garden also names a bean by it",
      r.returncode == 0, r.stdout + r.stderr)


# EVERY ANCHOR'S VALUE, NOT THE VALUES OF CHOSEN KEYS. The guard once read hostname, fqdn and ip, and nothing else a
# garden identifies a being by: a person's email, an agreement's id, a serial, the gardener's own qualified name.
commit("write to a@example.org for a copy\n", "neutral")
r = dmpublic()
check("an EMAIL a `name` gives in a public file is refused — a person is reached by it",
      r.returncode == 1 and "a@example.org" in r.stdout and "doc.md" in r.stdout, r.stdout)
commit("the agreement is filed as kettle-2026-17\n", "neutral")
r = dmpublic()
check("...and so is an agreement's IDENTIFIER, a name a garden's own namespace gives",
      r.returncode == 1 and "kettle-2026-17" in r.stdout, r.stdout)
commit("a serial like SN-Q1 is printed on the case\n", "neutral")
r = dmpublic()
check("...and a SERIAL's, a namespace no list named", r.returncode == 1 and "sn-q1" in r.stdout, r.stdout)
_gid = run("git", "-C", G, "rev-list", "--first-parent", "--max-parents=0", "HEAD").stdout.split()[-1][:12]
commit("this came from garden %s\n" % _gid, "neutral")
r = dmpublic()
check("...and the garden's OWN id, read from git as the gate reads it", r.returncode == 1 and _gid in r.stdout, r.stdout)

# A CONSENT FOR ONE PAGE IS NOT A CONSENT FOR EVERY FILE. A PUBLIC-ALLOW line may name the files a word is public
# in; anywhere else — another file, a commit message, a pull-request body — the word is guarded as before. Read from
# a copy of the language with its own PUBLIC-ALLOW, so this repository's list is not bent to the test.
L = os.path.join(T, "lang")
shutil.copytree(os.path.join(ROOT, "bin"), os.path.join(L, "bin"))
shutil.copytree(os.path.join(ROOT, "seed", "knowledge"), os.path.join(L, "seed", "knowledge"))
write(os.path.join(L, "seed", "PUBLIC-ALLOW"), "quietbox notes/about.md   # consented to on that page only\n")
def dmpublic_l(*extra):
    return run(sys.executable, os.path.join(L, "bin", "public.py"), "--garden", G, "--repo", R, *extra)
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
# WHAT ELSE A GARDEN SAYS OF ITSELF: a three-letter name, an address anywhere in a front matter, an email that is no
# anchor, a title of three words; a file whose path holds a space; and the published tables public only in themselves.
run("git", "-C", R, "rm", "-q", "notes/about.md", "seed/PUBLIC-ALLOW")      # the scoped consent above was the copy's
write(os.path.join(G, "beans", "nas.md"), bean("nas", "host", "the cellar storage box", "own: { by: someone, of: self }",
                                               'name: { by: makers, of: self, as: "SN-N1" }',
                                               "be: { by: self, at: 10.20.30.40, as: location }",
                                               "be: { by: self, at: 203.0.113.77, as: location }",
                                               extra='details:\n  contact: "ops-desk@cellar-net.io"\n  manual: "help@example.org"\n'))
write(os.path.join(G, "beans", "bakers.md"), bean("bakers", "host", "m", "own: { by: someone, of: self }",
                                                  'name: { by: makers, of: self, as: "SN-M1" }'))
for _text, _word, _why in (("the nas in the cellar\n", "nas", "a name of three letters"),
                           ("it answers at 10.20.30.40\n", "10.20.30.40", "an address a `be` names"),
                           ("write to ops-desk@cellar-net.io\n", "ops-desk@cellar-net.io", "an email `details` keeps"),
                           ("see the cellar storage box\n", "the cellar storage box", "a title of three words"),
                           ("the bakers restart it\n", "bakers", "a host a garden calls by a word of the occupations' table")):
    commit(_text, "neutral")
    r = dmpublic()
    check(f"{_why} in a public file is refused", r.returncode == 1 and _word in r.stdout, r.stdout + r.stderr)
commit("at 203.0.113.77, or help@example.org\n", "neutral")
r = dmpublic()
check("...while an address or a domain kept for documentation is not", r.returncode == 0, r.stdout + r.stderr)
commit("the nas in the cellar\n", "neutral", name="notes with a space.md")
commit("an example\n", "neutral")
r = dmpublic()
check("a file whose path holds a space is read, and named whole", r.returncode == 1 and "notes with a space.md" in r.stdout,
      r.stdout + r.stderr)
run("git", "-C", R, "rm", "-q", "notes with a space.md")
os.makedirs(os.path.join(R, "seed", "knowledge"), exist_ok=True)
commit("code\tname\n1\tbakers and cooks\n", "neutral", name="seed/knowledge/occupations.tsv")
r = dmpublic()
check("a published table may say its own words (`bakers`), where the rest of the repository may not",
      r.returncode == 0, r.stdout + r.stderr)
for _b in ("nas", "bakers"):
    os.remove(os.path.join(G, "beans", _b + ".md"))

_scoped = [l.split("#")[0].split() for l in open(os.path.join(ROOT, "seed", "PUBLIC-ALLOW"), encoding="utf-8")]
# ---- a word the gardener keeps out, though the world knows it (29.1: the garden's own PUBLIC-DENY) ----------------------
commit("samba serves the files here\n", "a neutral message", "old.md")
_base = run("git", "-C", R, "rev-parse", "HEAD").stdout.strip()
write(os.path.join(G, "PUBLIC-DENY"), "# the gardener's own reason is kept here\nsamba\n")
r = dmpublic("--range", _base + "..HEAD")
check("a word the catalogue makes public, that the gardener denies, is not refused where it was published before",
      r.returncode == 0, r.stdout + r.stderr)
commit("and samba again, in a new line\n", "a neutral message", "new.md")
r = dmpublic("--range", _base + "..HEAD")
check("...and is refused in a line the range adds", r.returncode == 1 and "samba" in r.stdout and "added" in r.stdout, r.stdout)
open(os.path.join(T, "pr.md"), "w").write("this pull request speaks of Samba\n")
r = dmpublic("--no-files", "--text", os.path.join(T, "pr.md"))
check("...in a pull request's text, and in a commit message", r.returncode == 1 and "samba" in r.stdout.lower(), r.stdout)
os.remove(os.path.join(G, "PUBLIC-DENY"))

_dead = [c for cells in _scoped for c in cells[1:] if not os.path.isfile(os.path.join(ROOT, *c.split("/")))]
check("every file a line of this repository's PUBLIC-ALLOW is scoped to exists", not _dead, _dead)

shutil.rmtree(T, ignore_errors=True)
print("\npublic: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
