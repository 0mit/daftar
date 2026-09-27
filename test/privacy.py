#!/usr/bin/env python3
"""Who may see what (PRIV, 24.0; step 1, F2, N16, N17, N18, N29, N31): a bean's sensitivity derived and never stored;
another person kept by name only on their consent; a grant the one answer to who may do what, closed by default; an
issued anchor that identifies only with its issuer; a phone in E.164.

Grows a garden and commits invented fixtures through its hook: a pottery school's students and its enrolment
agreement, a choir's section leaders and what they may read, and two employers who each issued the number 0042.
"""
import os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
FAILS = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:900]))
    if not cond:
        FAILS.append(name)


def run(*a, cwd=None):
    return subprocess.run(list(a), capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd)


T = tempfile.mkdtemp(prefix="dmpriv-")
G = os.path.join(T, "g")
r = run("sh", os.path.join(ROOT, "seed", "germinate.sh"), G, "--gardener", "keeper", cwd=ROOT)
check("a garden germinates from the release, and the law with PRIV's terms loads", r.returncode == 0 and "0 error" in r.stdout,
      r.stdout + r.stderr)


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


def save(what, names):
    body = "- action: added " + " ".join(f"[[{n}]]" for n in names)
    r = run(PY, "bin/dmsave.py", "keeper (test)", what, "--body", body, cwd=G)
    return r.returncode, r.stdout + r.stderr


def restore():
    run("git", "reset", "-q", "--hard", cwd=G)
    run("git", "clean", "-qfd", cwd=G)


def py(code):
    r = run(PY, "-c", "import sys; sys.path.insert(0, 'bin')\n" + code, cwd=G)
    return (r.stdout + r.stderr).strip()


def person(bid, extra="", title=None, anchors=""):
    write(f"beans/{bid}.md", f"""---
bean: {bid}
genos: person
title: "{title or bid}"
status: active
summary: "a person"
nature: empsychon
owned_by: {{ legal: {{ crown: agape }} }}
responsibility: {{ legal: {{ self: true }} }}
identity: {{ status: confirmed, anchors: [ {{ key: person_id, value: "person:{bid}", class: logical, establishing: true }}{anchors} ] }}
provenance: {{ src: asserted-by-human, by: keeper, as_of: now }}
{extra}---
A person.
""")


def contract(bid, parties, extra=""):
    body = "\n".join(f"  {p}: {{ who: {{ bean: {p} }}{', accepted: 2026-09-01' if acc else ''} }}" for p, acc in parties)
    write(f"beans/{bid}.md", f"""---
bean: {bid}
genos: contract
title: "{bid}"
status: active
summary: "an agreement"
nature: lekton
owned_by: {{ legal: {{ crown: logos }} }}
responsibility: {{ legal: {{ parties: true }} }}
identity: {{ status: confirmed, anchors: [ {{ key: contract_id, value: "contract:{bid}", class: logical, establishing: true }} ] }}
provenance: {{ src: asserted-by-human, by: keeper, as_of: now }}
parties:
{body}
words: {{ form: spoken, agreed: 2026-09-01 }}
{extra}---
An agreement.
""")


OWN = "owned_by: { legal: { owner: { bean: keeper } } }\nresponsibility: { legal: { holder: { bean: keeper } } }\n"

# ============================================================ F2: another person, by name, only on their consent
person("wren-ash")
code, out = save("a student", ["wren-ash"])
check("F2: a named person who is not the gardener, added with no consent, is refused and told the two ways",
      code != 0 and "no consent of theirs is recorded" in out and "bin/dmheld.py person" in out, out[-1200:])
restore()
person("p-3f9a0c1d")
code, out = save("a student, opaque", ["p-3f9a0c1d"])
check("…an opaque person (an id, the title the id, one anchor person:<id>) passes", code == 0, out[-1200:])
person("wren-ash", "consent: { bean: enrolment-2026 }\n")
contract("enrolment-2026", [("keeper", True), ("wren-ash", False)])
code, out = save("a student who has not yet accepted", ["wren-ash", "enrolment-2026"])
check("…a consent naming an agreement she has not accepted is no consent", code != 0 and "no consent" in out, out[-1200:])
restore()
person("wren-ash", "consent: { bean: enrolment-2026 }\n")
contract("enrolment-2026", [("keeper", True), ("wren-ash", True)])
code, out = save("a student who consented", ["wren-ash", "enrolment-2026"])
check("…and one whose agreement holds her acceptance passes by name", code == 0, out[-1200:])

write("beans/firing-class.md", f"""---
bean: firing-class
genos: event
title: "a firing class"
status: active
summary: "next month's firing class, at the kiln room"
nature: praxis
{OWN}identity: {{ status: confirmed, anchors: [ {{ key: event_id, value: "event:firing-class", class: logical, establishing: true }} ] }}
provenance: {{ src: asserted-by-human, by: keeper, as_of: now }}
timing:
  start: {{ system: gregorian-civil, at: "2099-10-20T18:00", unit: minute }}
about: [ {{ who: wren-ash }} ]
located_at: [ {{ system: physical, openness: elsewhere, at: "the kiln room" }} ]
---
A class.
""")
code, out = save("a class to come", ["firing-class"])
check("F2: a future whereabouts of a person who is not the gardener is refused in git, consent or not",
      code != 0 and "in the future, in git" in out, out[-1500:])
restore()

# ============================================================ N29 `about`, and sensitivity derived (step 1)
write("beans/kiln-note.md", f"""---
bean: kiln-note
genos: document
title: "a note on a student's glaze"
status: active
summary: "a note"
nature: lekton
{OWN}identity: {{ status: confirmed, anchors: [ {{ key: doc_id, value: "document:kiln-note", class: logical, establishing: true }} ] }}
provenance: {{ src: asserted-by-human, by: keeper, as_of: now }}
about: [ {{ who: p-3f9a0c1d }} ]
located_at: [ {{ system: unix-filesystem, openness: unknown }} ]
---
A note.
""")
code, out = save("a note about a student", ["kiln-note"])
check("a document `about` a person is saved", code == 0, out[-1200:])
out = py("import dmpass, dmheld; fm = dmpass.beans_here('.')['kiln-note']; print(dmpass.sensitivity(fm, dmheld.types_law('.')))")
check("dmpass.sensitivity derives it personal, naming whom it is about", "'personal'" in out and "about p-3f9a0c1d" in out, out)
r = run(PY, "bin/dmcursor.py", "kiln-note", cwd=G)
check("dmcursor shows it, derived, and whom it is about", "sensitivity personal — about p-3f9a0c1d" in r.stdout, r.stdout + r.stderr)
text = read("beans/kiln-note.md")
write("beans/kiln-note.md", text.replace("about: [", 'sensitivity: { is: none, why: "only a glaze" }\nabout: [')
      .replace("src: asserted-by-human", "src: generated-by-tool"))
out = gate()
check("a mark below what the content derives, under a tool's provenance, is refused: lowering is a person's word",
      "is marked none, below the personal" in out, out[-1500:])
write("beans/kiln-note.md", text.replace("about: [", 'sensitivity: { is: none, why: "only a glaze" }\nabout: ['))
out = gate()
check("…and stands on the gardener's own word", "below the personal" not in out and " 0 error" in out, out[-1500:])
out = py("import dmpass, dmheld; fm = dmpass.beans_here('.')['kiln-note']; print(dmpass.sensitivity(fm, dmheld.types_law('.')))")
check("…where dmpass.sensitivity says it was lowered, and on whose word", "'none'" in out and "lowered on a person" in out, out)
write("beans/kiln-note.md", text.replace("about: [", 'sensitivity: { is: special-category, why: "names a condition" }\nabout: ['))
out = py("import dmpass, dmheld; fm = dmpass.beans_here('.')['kiln-note']; print(dmpass.sensitivity(fm, dmheld.types_law('.')))")
check("a person raises it above what is derived", "'special-category'" in out and "raised by a person" in out, out)
restore()

# ============================================================ N31 grants, and N16's ratify
person("p-0a1b2c3d")
person("p-4e5f6a7b")
keeper = read("beans/keeper.md")
write("beans/keeper.md", keeper.replace("\n---\n", """
selections:
  members: { what: "the choir's members", steps: [ { id: people, op: select, genos: person } ] }
  section-leaders: { what: "the section leaders", steps: [ { id: people, op: select, genos: person, where: [ { path: bean, is: p-0a1b2c3d } ] } ] }
grants:
  leaders-read-names: { act: read, over: members, positions: [ { path: title } ], audience: { selection: section-leaders }, why: "a leader calls the register" }
---
""", 1))
code, out = save("who may read the register", ["keeper", "p-0a1b2c3d", "p-4e5f6a7b"])
check("a grant on the gardener's bean, over a selection, to a selection, is saved", code == 0, out[-1500:])
ask = "import dmpass; a = dmpass.may({!r}, {!r}, {!r}, positions={!r}, root='.'); print(a.granted, '|', a.why, '|', a.grants)"
out = py(ask.format("p-0a1b2c3d", "read", "p-4e5f6a7b", ["title"]))
check("may: a section leader may read a member's title, and the answer names the grant", out.startswith("True") and "keeper:grants[leaders-read-names]" in out, out)
out = py(ask.format("p-0a1b2c3d", "read", "p-4e5f6a7b", ["located_at"]))
check("…not where the member is: no grant opens it, closed by default", out.startswith("False") and "closed by default" in out, out)
out = py(ask.format("p-4e5f6a7b", "read", "p-0a1b2c3d", ["title"]))
check("…and a member who is no leader is not in the audience", out.startswith("False"), out)
out = py(ask.format(None, "read", "p-4e5f6a7b", None))
check("…nobody named is granted nothing", out.startswith("False") and "nobody named" in out, out)
out = py(ask.format("keeper", "write", "p-4e5f6a7b", None))
check("…the gardener is granted, as the keeper", out.startswith("True") and "gardener" in out, out)
k2 = read("beans/keeper.md")
write("beans/keeper.md", k2.replace("---\nkeeper", "---\nkeeper", 1).replace(
    '  leaders-read-names:', '  no-titles: { act: read, over: members, positions: [ { path: title } ], audience: { selection: section-leaders }, stance: forbidden, why: "a ceiling" }\n  leaders-read-names:'))
out = py(ask.format("p-0a1b2c3d", "read", "p-4e5f6a7b", ["title"]))
check("…the gardener's forbidden grant is a ceiling no permitted one passes", out.startswith("False") and "forbidden by keeper:grants[no-titles]" in out, out)
restore()
m = read("beans/p-4e5f6a7b.md")
write("beans/p-4e5f6a7b.md", m.replace("\n---\n", '\ngrants:\n  i-decide: { act: "ratify:D", audience: { who: p-0a1b2c3d }, why: "mine" }\n---\n', 1))
out = gate()
check("N16: a ratify grant on a member's bean is refused — delegated only by the gardener's own act",
      "delegated only by the gardener's own act" in out, out[-1500:])
write("beans/p-4e5f6a7b.md", m.replace("\n---\n", '\ngrants:\n  mine: { act: read, positions: [ { path: shoe-size } ], audience: { who: p-0a1b2c3d }, why: "mine" }\n---\n', 1))
out = gate()
check("a grant's position that names no term is refused", "'shoe-size' names no term" in out, out[-1500:])
restore()

# an agreement decides over its own bean and what a party who ACCEPTED it brings — never the rest of the garden
contract("reading-circle", [("keeper", True), ("p-0a1b2c3d", True)], """selections:
  people: { what: "every person the garden holds", steps: [ { id: p, op: select, genos: person } ] }
grants:
  circle-reads: { act: read, over: people, audience: { selection: people }, why: "the circle reads one another" }
  circle-notes: { act: read, audience: { selection: people }, why: "the circle's own terms are its members' to read" }
""")
out = py(ask.format("p-4e5f6a7b", "read", "p-0a1b2c3d", None))
check("H4: an agreement's grant opens the bean of a party who accepted it", out.startswith("True")
      and "reading-circle:grants[circle-reads]" in out, out)
out = py(ask.format("p-0a1b2c3d", "read", "p-4e5f6a7b", None))
check("…and not the bean of a person who never accepted it, whatever its `over` selects — an agreement is not a key to "
      "the garden", out.startswith("False") and "closed by default" in out, out)
out = py(ask.format("p-4e5f6a7b", "read", "reading-circle", None))
check("…its own bean it opens, `over` or not", out.startswith("True") and "reading-circle:grants[circle-notes]" in out, out)
out = gate()
_w = next((l for l in out.splitlines() if "reading-circle: grants[circle-reads] is over" in l), "")
check("…and the gate names the beans its `over` reaches that it does not share, as a warning: they open nothing",
      "p-4e5f6a7b" in _w and "p-0a1b2c3d" not in _w and "which this agreement does not share" in _w
      and " 0 error(s)" in out, out[-1500:])
restore()

# ============================================================ N17 issuer-scoped anchors, N18 phone
for org in ("fern-bakery", "gull-ferries"):
    write(f"beans/{org}.md", f"""---
bean: {org}
genos: org
title: "{org}"
status: active
summary: "an employer"
nature: lekton
{OWN}identity: {{ status: confirmed, anchors: [ {{ key: org_id, value: "org:{org}", class: logical, establishing: true }} ] }}
provenance: {{ src: asserted-by-human, by: keeper, as_of: now }}
---
An employer.
""")
contract("staff-2026", [("keeper", True), ("rook-hale", True), ("tam-ivy", True)])
person("rook-hale", "consent: { bean: staff-2026 }\n", anchors=', { key: emp_id, value: "0042", class: logical, establishing: true, issuer: { bean: fern-bakery } }')
person("tam-ivy", "consent: { bean: staff-2026 }\n", anchors=', { key: emp_id, value: "0042", class: logical, establishing: true, issuer: { bean: gull-ferries } }')
code, out = save("two employees", ["fern-bakery", "gull-ferries", "staff-2026", "rook-hale", "tam-ivy"])
check("N17: two employers each issuing 0042 are two identities, no collision", code == 0, out[-1500:])
t = read("beans/tam-ivy.md")
write("beans/tam-ivy.md", t.replace("gull-ferries", "fern-bakery"))
out = gate()
check("…the same issuer twice collides", "emp_id=0042 issued by fern-bakery" in out, out[-1500:])
write("beans/tam-ivy.md", t.replace(", issuer: { bean: gull-ferries }", ""))
out = gate()
check("…and an issued anchor with no issuer is warned, not refused", "names none" in out and " 0 error" in out, out[-1500:])
restore()
k = read("beans/keeper.md")
write("beans/keeper.md", k.replace("establishing: true }\nprovenance", 'establishing: true }\n    - { key: phone, value: "+15555550100", class: logical, establishing: false }\nprovenance', 1))
out = gate()
check("N18: a phone in E.164 passes", " 0 error" in out, out[-1500:])
write("beans/keeper.md", k.replace("establishing: true }\nprovenance", 'establishing: true }\n    - { key: phone, value: "0044 20 7946 0000", class: logical, establishing: false }\nprovenance', 1))
out = gate()
check("…and one not in E.164 is refused", "phone" in out and "error" in out and " 0 error" not in out, out[-1500:])
restore()

shutil.rmtree(T, ignore_errors=True)
print(f"\nprivacy: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
