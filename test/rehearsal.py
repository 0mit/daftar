#!/usr/bin/env python3
"""The rehearsal (std-vocab 24.0, step 12): an invented health garden, end to end, with no network and no hosted
harness. Its gardener is the patient: the household's own record. Readings coded in a scheme marked special-category
are sealed off git one by one, a series sealed whole (S6), and read by the reckoner on the host that holds them — and
nowhere else. No special value reaches any blob of the history; a store in cleartext readable from a remote party is
warned in breach; an erasure leaves every pointer `Erased`, and a reading of it finds nothing.

Every fixture is INVENTED.
Run: python3 test/rehearsal.py   (0 = green)
"""
import os, re, shutil, socket, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
FAILS = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-2500:]))
    if not cond:
        FAILS.append(name)


def run(*a, cwd=None, stdin=None):
    return subprocess.run(list(a), capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd,
                          input=stdin, env=dict(os.environ, PYTHONIOENCODING="utf-8"))


T = tempfile.mkdtemp(prefix="dmrehearse-")
G = os.path.join(T, "g")
STORE = os.path.join(T, "vault")
HOST = socket.gethostname().lower()
r = run(PY, os.path.join(ROOT, "seed", "germinate.py"), G, "--gardener", "keeper", cwd=ROOT)
check("a health garden germinates, kept by its patient", r.returncode == 0, r.stdout + r.stderr)
run("git", "config", "user.name", "keeper (test)", cwd=G)
run("git", "config", "user.email", "keeper@example.org", cwd=G)


def write(rel, text):
    p = os.path.join(G, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def read(rel):
    with open(os.path.join(G, *rel.split("/")), encoding="utf-8") as fh:
        return fh.read()


def gate():
    r = run(PY, "bin/dmcheck.py", "--all", cwd=G)
    return r.stdout + r.stderr


def ok(out):
    return re.search(r" 0 error\(s\)", out) is not None


def save(what, body):
    r = run(PY, "bin/dmsave.py", "keeper (test)", what, "--body", body, cwd=G)
    return r.returncode, r.stdout + r.stderr


def tool(*a):
    r = run(PY, *a, cwd=G)
    return r.returncode, r.stdout + r.stderr


# ---------------------------------------------------------------- the garden says it is a rehearsal
g = read("GARDEN.md")
write("GARDEN.md", g.replace("\ngardener:", '\ntest: "a household\'s own health record, invented"\ngardener:', 1))

VOCAB_EXTRA = """registry_additions:
  knowledge_schemes:
    - scheme: vital-signs
      classifies: what a household reads of a body, where on it and how, invented
      holding: extract
      sensitive: special-category
      licence: CC0-1.0
      release: "the household's own, 2026"
      publisher: the household (invented)
      url: "extracts/vital-signs.tsv"
      levels: [ { level: sign } ]
      neighbours: none
      sources: extracts/vital-signs.tsv
registry_files:
  - { registry: vital-signs, file: extracts/vital-signs.tsv, key: code }
"""
v = read("VOCAB.md")
for k in ("registry_additions", "registry_files"):
    v = re.sub(rf"(?m)^{k}: (\[\]|\{{\}}).*\n", "", v)
h, sep, rest = v.partition("\n---\n")
write("VOCAB.md", h + "\n" + VOCAB_EXTRA + sep + rest)
write("extracts/vital-signs.tsv", "code\tparent\tname\nsystolic\t\tthe pressure at the heart's beat\n"
      "diastolic\t\tthe pressure between beats\nupper-arm\t\tthe upper arm\ncuff\t\tan automatic cuff\n")

OWN = "owned_by: { legal: { owner: { bean: keeper } } }\nresponsibility: { legal: { holder: { bean: keeper } } }\n"
write("beans/this-host.md", f"""---
bean: this-host
genos: host
title: "the household's laptop"
status: active
summary: "the machine the household's record is kept on"
nature: soma
os: linux
identity: {{ status: confirmed, anchors: [ {{ key: hostname, value: "{HOST}", class: network, establishing: false }}, {{ key: serial, value: "SN-HOME-1", class: hardware, establishing: true }} ] }}
provenance: {{ src: asserted-by-human, by: keeper, as_of: now }}
{OWN}roots:
  vault: {{ system: unix-filesystem, at: "{HOST}:{STORE}", observed: 2026-09-01, keeps: special-category, controller: keeper, readable_from: this-host, backup: "copied to a second disk each week" }}
---
The household's laptop.
""")
code, out = save("the household's scheme, laptop and store",
                 "- action: RULE-CHANGE (VOCAB.md) the scheme [[vital-signs]] held as the household's extract; "
                 "[[this-host]], whose root `vault` keeps special-category material off git.")
check("a scheme marked special-category, and a store that keeps such material on this host, are saved", code == 0, out)

# ---------------------------------------------------------------- the readings, written first as the patient says them
SPECIAL = ("127.5", "83.5", "121.5", "0.3172", "0.3418", "0.2963")
READINGS = """observations:
  bp-0314:
    property: { scheme: vital-signs, code: systolic }
    of: { scheme: vital-signs, code: upper-arm }
    value: { count: "127.5", unit: millimetre-of-mercury, u: { count: "2.5", unit: millimetre-of-mercury } }
    at: "2026-03-14 08:30+03:00"
    method: { scheme: vital-signs, code: cuff }
    by: keeper
  bp-0314-d:
    property: { scheme: vital-signs, code: diastolic }
    value: { count: "83.5", unit: millimetre-of-mercury, u: { count: "2.5", unit: millimetre-of-mercury } }
    at: "2026-03-14 08:30+03:00"
    by: keeper
  bp-0315:
    property: { scheme: vital-signs, code: systolic }
    value: { count: "121.5", unit: millimetre-of-mercury, u: { count: "2.5", unit: millimetre-of-mercury } }
    at: "2026-03-15 08:25+03:00"
    by: keeper
series:
  perfusion:
    grid: { of: time, in: gregorian-civil, every: { count: 1, unit: minute }, from: "2026-03-14 08:31+03:00" }
    unit: minute
    holds:
      - { name: index, quantity: ratio, unit: percent, stands_for: point, u: { count: "0.0001", unit: percent } }
    rows: |
      index
      0.3172
      0.3418
      0.2963
selections:
  highest-systolic:
    what: "the highest systolic pressure read"
    steps:
      - { id: sys, op: select, entries: "observations.*", where: [ { path: property.code, is: systolic } ] }
      - { id: top, op: max, of: sys, path: value }
  systolic-readings:
    what: "how many systolic readings there are"
    steps:
      - { id: sys, op: select, entries: "observations.*", where: [ { path: property.code, is: systolic } ] }
      - { id: n, op: count, of: sys }
"""
k = read("beans/keeper.md")
head, sep, body = k[4:].partition("\n---\n")
write("beans/keeper.md", "---\n" + head + "\n" + READINGS.rstrip() + "\n---\n" + body)
out = gate()
check("written in the bean, the readings pass the gate and are WARNED as special-category material in git, by path",
      ok(out) and "holds special-category material at" in out and not any(s in out for s in SPECIAL), out[-2500:])
code, out = save("the readings, as the patient says them", "- action: the readings of [[keeper]], as said.")
check("...and a commit that would carry them unsealed is REFUSED, each path named and no value: a value committed is "
      "in every clone for good, and no seal made afterwards takes it back",
      code != 0 and "this commit adds special-category material at observations.bp-0314" in out
      and "seal it first" in out and not any(s in out for s in SPECIAL)
      and run("git", "log", "-p", "--all", cwd=G).stdout.count("127.5") == 0, out[-2500:])
run("git", "reset", "-q", cwd=G)
run("git", "checkout", "-q", "--", "log/journal.md", cwd=G)

# ---------------------------------------------------------------- sealed, one by one, and the series whole
lines = []
for key in ("bp-0314", "bp-0314-d", "bp-0315"):
    code, out = tool("bin/dmheld.py", "put", "keeper", "observations", key)
    m = re.search(r"(- held: keeper \S+ added)", out)
    check(f"dmheld put seals the reading {key}, and prints its one journal line", code == 0 and m, out)
    lines.append(m.group(1) if m else "")
code, out = tool("bin/dmheld.py", "put", "keeper", "series", "perfusion")
m = re.search(r"(- held: keeper \S+ added)", out)
check("S6: the perfusion series is sealed whole — its line, channel and rows", code == 0 and m, out)
lines.append(m.group(1) if m else "")
text = read("beans/keeper.md")
check("the bean keeps only pointers: no value, no code, no key of a reading",
      not any(s in text for s in SPECIAL) and "systolic\n" not in text.split("selections:")[0]
      and "bp-0314" not in text and "rows:" not in text and text.count("held: \"root:vault/") == 4, text)
out = gate()
check("sealed, the bean is no longer warned", ok(out) and "holds special-category material" not in out, out[-2000:])
code, out = save("the household's readings, sealed", "- action: the readings of [[keeper]], sealed off git.\n"
                 + "\n".join(lines))
check("the save commits, with each seal's one line and nothing more", code == 0, out)

# ---------------------------------------------------------------- read where they are held
code, out = tool("bin/dmreckon.py", "keeper:highest-systolic")
check("a reading on this host reads the sealed readings: the highest systolic, with its u",
      code == 0 and "127.5" in out and "millimetre-of-mercury" in out, out)
code, out = tool("bin/dmreckon.py", "keeper:systolic-readings")
check("...and counts them", code == 0 and "= 2 item" in out, out)
check("...and writes nothing back", run("git", "status", "--porcelain", cwd=G).stdout.strip() == "",
      run("git", "status", "--porcelain", cwd=G).stdout)
code, out = tool("bin/dmheld.py", "check")
check("dmheld check: every pointer resolves here", code == 0 and "0 error" in out, out)

# ---------------------------------------------------------------- nothing special in any blob of the history
objs = run("git", "rev-list", "--all", "--objects", cwd=G).stdout.split()
blobs = run("git", "cat-file", "--batch", cwd=G, stdin="\n".join(o for o in objs if re.fullmatch(r"[0-9a-f]{40}", o)) + "\n").stdout
check("no special value — a pressure, a perfusion row — is in any object of the repository",
      blobs and not any(s in blobs for s in SPECIAL), [s for s in SPECIAL if s in blobs])
kb = run("git", "log", "-p", "--all", "--", "beans/keeper.md", cwd=G).stdout
check("...and no code of the special scheme was ever in the bean's history", "code: systolic" not in kb
      and "code: upper-arm" not in kb, "")

# ---------------------------------------------------------------- the store's own cell
text = read("beans/this-host.md")
write("beans/this-host.md", text.replace("readable_from: this-host", "readable_from: remote"))
out = gate()
check("a store of special-category material in cleartext, readable from a remote party, warns in breach",
      "special-category material stored in cleartext" in out and ok(out), out[-1500:])
run("git", "checkout", "-q", "--", "beans/this-host.md", cwd=G)

# ---------------------------------------------------------------- erasure
code, out = tool("bin/dmheld.py", "erase", "keeper")
check("dmheld erase deletes every record the patient is in", code == 0 and "erased 4 held record" in out, out)
ptrs = re.findall(r"root:vault/[0-9a-f]{32}", read("beans/keeper.md"))
res = [tool("bin/dmheld.py", "resolve", p) for p in ptrs]
check("...and every pointer resolves to Erased", len(ptrs) == 4 and all(c != 0 and "erased for its subject" in o for c, o in res), res)
code, out = tool("bin/dmheld.py", "check")
check("dmheld check: an erased pointer is no finding", code == 0 and "0 error(s), 0 warning" in out, out)
code, out = tool("bin/dmreckon.py", "keeper:systolic-readings")
check("a reading after the erasure finds nothing of them", "127.5" not in out and "= 2 item" not in out, out)
out = gate()
check("the garden still passes the gate", ok(out), out[-1500:])

shutil.rmtree(T, ignore_errors=True)
print(f"\nrehearsal: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
