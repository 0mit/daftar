#!/usr/bin/env python3
"""Observations (std-vocab 24.0, OBS): what was found of a being, coded in a published scheme, at a moment, by whom; a
verdict that answers another entry, once per observer; a hearing ruled on only once every speaker is heard; a scheme a
garden holds as its own extract, with labels in another language and relations between its codes, edited as a journalled
write; a scheme held at its authority, checked by form; configuration kept as such an extract, with no RULE-CHANGE.

Every fixture is INVENTED: a lichen survey of three standing stones, its two surveyors, and a co-op's kinds of leave.
Run: python3 test/observations.py   (0 = green)
"""
import os, re, shutil, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS = []
PY = sys.executable


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-3000:]))
    if not cond:
        FAILS.append(name)


def run(*a, cwd):
    return subprocess.run(list(a), capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd,
                          env=dict(os.environ, PYTHONIOENCODING="utf-8"))


T = tempfile.mkdtemp(prefix="dmobs-")
G = os.path.join(T, "g")
r = run(PY, os.path.join(ROOT, "seed", "germinate.py"), G, "--gardener", "keeper", cwd=ROOT)
check("a garden germinates, kept by keeper", r.returncode == 0, r.stdout + r.stderr)
run("git", "config", "user.name", "keeper (test)", cwd=G)
run("git", "config", "user.email", "keeper@example.org", cwd=G)


def write(rel, text):
    p = os.path.join(G, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def read(rel):
    return open(os.path.join(G, *rel.split("/")), encoding="utf-8").read()


def gate():
    r = run(PY, "bin/dmcheck.py", "--all", cwd=G)
    return r.stdout + r.stderr


def ok(out):
    return re.search(r" 0 error\(s\)", out) is not None


def save(what, names, rule_change=False):
    body = "- action: " + ("RULE-CHANGE (VOCAB.md) " if rule_change else "") + " ".join(f"[[{n}]]" for n in names)
    r = run(PY, "bin/dmsave.py", "keeper (test)", what, "--body", body, cwd=G)
    return r.returncode, r.stdout + r.stderr


def restore():
    run("git", "reset", "-q", "--hard", cwd=G)
    run("git", "clean", "-qfd", cwd=G)


def tool(*a):
    r = run(PY, *a, cwd=G)
    return r.returncode, r.stdout + r.stderr


PERSON_OWN = "owned_by: { legal: { crown: agape } }\nresponsibility: { legal: { self: true } }\n"
OWN = "owned_by: { legal: { owner: { bean: keeper } } }\nresponsibility: { legal: { holder: { bean: keeper } } }\n"


def person(id):
    return (f"---\nbean: {id}\ngenos: person\ntitle: \"{id}\"\nstatus: active\nsummary: \"{id}, invented\"\nnature: empsychon\n"
            f"{PERSON_OWN}consent: {{ bean: survey }}\n"
            f"identity: {{ status: confirmed, anchors: [ {{ key: identifier, value: \"person:{id}\", class: logical, "
            f"establishing: true }} ] }}\nprovenance: {{ src: asserted-by-human, by: keeper, as_of: now }}\n---\n{id}, invented.\n")


def stone(id, obs=""):
    return (f"---\nbean: {id}\ngenos: stone\ntitle: \"{id} — a standing stone\"\nstatus: active\n"
            f"summary: \"an invented standing stone, surveyed for lichen\"\nnature: soma\n{OWN}"
            f"identity: {{ status: confirmed, anchors: [ {{ key: serial, value: \"{id.upper()}-1\", class: hardware, "
            f"establishing: true }} ] }}\nprovenance: {{ src: observed, by: keeper, as_of: now }}\n{obs}---\n{id}, invented.\n")


# ---------------------------------------------------------------- the garden's own scheme, held as an extract (O-3)
VOCAB_EXTRA = """local_gene:
  - { genos: stone, of_nature: soma, meaning: "a standing stone in a field, invented" }
registry_additions:
  knowledge_schemes:
    - scheme: lichen-forms
      classifies: the growth forms of lichen, and how much of a surface they cover
      holding: extract
      licence: CC0-1.0
      release: "the survey's own, 2026"
      relations: lichen-forms-relations
      labels: [ { language: fr, registry: lichen-forms-fr, attribution: "traduction du relevé, inventée" } ]
      publisher: the survey (invented)
      url: "extracts/lichen-forms.tsv"
      levels: [ { level: form } ]
      neighbours: none
      sources: extracts/lichen-forms.tsv
    - scheme: field-codes
      classifies: the codes an invented field office keeps, looked up there
      holding: at-authority
      code_pattern: '^[A-Z][0-9]{2}$'
      licence: LicenseRef-invented
      publisher: an invented field office
      url: "https://example.org/field-codes"
      levels: [ { level: code } ]
      neighbours: none
      sources: "https://example.org/field-codes"
registry_files:
  - { registry: lichen-forms, file: extracts/lichen-forms.tsv, key: code }
  - { registry: lichen-forms-relations, file: extracts/lichen-forms-relations.tsv, key: from }
  - { registry: lichen-forms-fr, file: extracts/lichen-forms-fr.tsv, key: code }
"""
_v = read("VOCAB.md")
for _k in ("local_gene", "registry_additions", "registry_files"):
    _v = re.sub(rf"(?m)^{_k}: (\[\]|\{{\}}).*\n", "", _v)
_h, _sep, _rest = _v.partition("\n---\n")
write("VOCAB.md", _h + "\n" + VOCAB_EXTRA + _sep + _rest)
write("extracts/lichen-forms.tsv", "code\tparent\tname\n"
      "cover\t\tthe share of a surface lichen covers\ncrustose\t\ta crust, fixed to the surface\n"
      "foliose\t\tleaf-like lobes\nfruticose\t\tshrubby, branched\nrim\t\tthe rim of a stone\nface\t\tthe face of a stone\n"
      "transect\t\ta line walked, counted at each step\n")
write("extracts/lichen-forms-relations.tsv", "from\tto\trel\nrim\tface\tadjacent\ncrustose\tcover\tpart-of\n")
write("extracts/lichen-forms-fr.tsv", "code\tname\ncover\trecouvrement\ncrustose\tcrustacé\nfoliose\tfoliacé\n")
write("beans/ada.md", person("ada"))
write("beans/bea.md", person("bea"))
write("beans/survey.md", f"""---
bean: survey
genos: contract
title: "the lichen survey"
status: active
summary: "an invented agreement: two surveyors read the stones' lichen, and the keeper keeps the record"
nature: lekton
owned_by: {{ legal: {{ crown: logos }} }}
responsibility: {{ legal: {{ parties: true }} }}
identity: {{ status: confirmed, anchors: [ {{ key: identifier, value: "contract:survey", class: logical, establishing: true }} ] }}
provenance: {{ src: asserted-by-human, by: keeper, as_of: now }}
parties:
  ada: {{ who: {{ bean: ada }}, role: surveyor, accepted: 2026-04-01 }}
  bea: {{ who: {{ bean: bea }}, role: surveyor, accepted: 2026-04-01 }}
  keeper: {{ who: {{ bean: keeper }}, role: recorder, accepted: 2026-04-01 }}
words: {{ form: spoken, agreed: 2026-04-01 }}
---
The survey, invented.
""")

B_OBS = """observations:
  crust-cover:
    property: { scheme: lichen-forms, code: cover }
    of: { scheme: lichen-forms, code: face }
    value: { count: "35", unit: percent, u: { count: "5", unit: percent } }
    at: 2026-05-02
    method: { scheme: lichen-forms, code: transect }
    by: ada
  crust-form:
    property: { scheme: lichen-forms, code: cover }
    code: { scheme: lichen-forms, code: crustose }
    at: 2026-05-02
    by: ada
"""
C_OBS = """observations:
  crust-cover:
    property: { scheme: lichen-forms, code: cover }
    presence: absent
    at: 2026-05-02
    by: ada
  second-look:
    answers: "stone-c:observations.crust-cover"
    answer: disputes
    by: bea
    note: "a crust on the north face, low down"
"""
write("beans/stone-b.md", stone("stone-b", B_OBS))
write("beans/stone-c.md", stone("stone-c", C_OBS))
write("beans/stone-d.md", stone("stone-d", "observations:\n  mark:\n    property: { scheme: field-codes, code: B42 }\n    at: 2026-05-03\n    by: bea\n"))
out = gate()
check("O-1 the survey passes: a reading with its u, a coded result, an absence, a verdict that disputes it",
      ok(out), out[-2500:])
check("O-3 a code of a scheme held at its authority passes by its form, with ONE warning that it is not looked up",
      out.count("field-codes: held at its authority") == 1, out[-1500:])
rc, out = save("the lichen survey of three stones, and the survey's own scheme",
               ["stone-b", "stone-c", "stone-d", "ada", "bea", "survey", "lichen-forms", "lichen-forms-relations", "lichen-forms-fr"], True)
check("...and commit through the hook", rc == 0, out[-2000:])


def refused(name, rel, text, want):
    write(rel, text)
    out = gate()
    check(name, not ok(out) and want in out, out[-2000:])
    restore()


# ---------------------------------------------------------------- O-1 refusals
refused("O-1 a second verdict by one observer on one entry is refused, wherever it is written",
        "beans/stone-b.md", stone("stone-b", B_OBS + "  again:\n    answers: \"stone-c:observations.crust-cover\"\n"
                                  "    answer: confirms\n    by: bea\n"),
        "two verdicts by bea on stone-c:observations.crust-cover")
refused("O-1 a verdict with no `answers` is refused (a verdict names the entry it is a verdict on)",
        "beans/stone-c.md", stone("stone-c", C_OBS.replace('    answers: "stone-c:observations.crust-cover"\n', "    at: 2026-05-04\n")),
        "but carries no answers")
refused("O-1 an entry that `answers` and gives no answer is refused",
        "beans/stone-c.md", stone("stone-c", C_OBS.replace("    answer: disputes\n", "")),
        "gives no `answer`")
refused("O-1 a verdict answering what is no observation is refused",
        "beans/stone-c.md", stone("stone-c", C_OBS.replace("stone-c:observations.crust-cover", "stone-c:observations.nothing-here")),
        "which names no observation")
refused("O-1 an absent entry with a value is refused",
        "beans/stone-c.md", stone("stone-c", C_OBS.replace("    presence: absent\n", "    presence: absent\n    value: { count: \"2\", unit: percent }\n")),
        "`presence: absent` beside a result (value)")
refused("O-1 a reading that states no property is refused",
        "beans/stone-b.md", stone("stone-b", B_OBS.replace("    property: { scheme: lichen-forms, code: cover }\n    of:", "    of:", 1)),
        "a reading states its `property`")
refused("O-1 a property coded in a word the scheme does not hold is refused",
        "beans/stone-b.md", stone("stone-b", B_OBS.replace("code: cover }\n    of:", "code: moss }\n    of:", 1)),
        "'moss' is not a declared lichen-forms")
refused("O-1 both `at` and `during` is refused (when it held is one of the two)",
        "beans/stone-b.md", stone("stone-b", B_OBS.replace("    at: 2026-05-02\n    method:", "    at: 2026-05-02\n    during: { from: 2026-05-01, to: 2026-05-02 }\n    method:", 1)),
        "at_most_one_of")
refused("O-1 an observer the garden does not hold is refused (N19: their standing must be readable)",
        "beans/stone-b.md", stone("stone-b", B_OBS.replace("    by: ada\n", "    by: nobody-here\n", 1)),
        "nobody-here")
refused("O-1 a retraction with no provenance of the observer's own is refused",
        "beans/stone-b.md", stone("stone-b", B_OBS.replace("    by: ada\n  crust-form:", "    by: ada\n    retracted: 2026-05-09\n  crust-form:", 1)),
        "a retraction is its observer's own word")
write("beans/stone-b.md", stone("stone-b", B_OBS.replace("    by: ada\n  crust-form:", "    by: ada\n    retracted: 2026-05-09\n"
                                                         "    provenance: { src: asserted-by-human, by: ada, as_of: now }\n  crust-form:", 1)))
out = gate()
check("...and passes when the observer's own word is recorded on the entry", ok(out), out[-2000:])
restore()

# ---------------------------------------------------------------- O-2 hearings
HEARING = """hearings:
  crust-on-c:
    over: [ { path: "stone-c:observations.crust-cover" }, { path: "stone-c:observations.second-look" } ]
    heard:
      - { speaker: ada, said: "I walked the whole face and saw none", at: 2026-05-05 }
%s    ruling: { by: keeper, what: "look again together in June", at: 2026-05-06 }
"""
write("beans/stone-c.md", stone("stone-c", C_OBS + HEARING % ""))
out = gate()
check("O-2 a ruling with one side heard is refused", not ok(out) and "rules before bea is heard" in out, out[-1500:])
write("beans/stone-c.md", stone("stone-c", C_OBS + HEARING % '      - { speaker: bea, said: "it is low down, under the grass line", at: 2026-05-05 }\n'))
out = gate()
check("...and with both heard, it passes", ok(out), out[-1500:])
restore()
refused("O-2 a hearing over an entry the garden does not hold is refused",
        "beans/stone-c.md", stone("stone-c", C_OBS + "hearings:\n  x:\n    over: [ { path: \"stone-z:observations.a\" } ]\n"),
        "names no entry this garden holds")

# ---------------------------------------------------------------- O-3 the extract, a journalled write
write("extracts/lichen-forms.tsv", read("extracts/lichen-forms.tsv") + "squamulose\t\tsmall scales\n")
run("git", "add", "-A", cwd=G)
jr = run(PY, "bin/dmjournal.py", "keeper (test)", "a note about the survey", "--body", "- action: a note, naming no file", cwd=G)
run("git", "add", "log/journal.md", cwd=G)
r = run("git", "commit", "-qm", "an extract edited, the journal naming nothing", cwd=G)
check("O-3 an edit to an extract whose journal entry does not name it is refused",
      r.returncode != 0 and "extracts/lichen-forms.tsv: staged, but the staged journal entry never names it" in r.stdout + r.stderr,
      jr.stdout + jr.stderr + r.stdout + r.stderr)
restore()
write("extracts/lichen-forms.tsv", read("extracts/lichen-forms.tsv") + "squamulose\t\tsmall scales\n")
rc, out = save("a growth form added to the survey's scheme", ["lichen-forms"])
check("...and an entry naming it commits, with no RULE-CHANGE", rc == 0 and "RULE-CHANGE" not in read("log/journal.md").split("\n## ")[-1], out[-1500:])
refused("O-3 a relation between codes the scheme does not hold is refused",
        "extracts/lichen-forms-relations.tsv", "from\tto\trel\nrim\tknee\tadjacent\n", "to 'knee' is no code of lichen-forms")
refused("O-3 a relation of a kind the law does not know is refused",
        "extracts/lichen-forms-relations.tsv", "from\tto\trel\nrim\tface\tbeside\n", "part-of, requires or adjacent")
refused("O-3 a code not of the form an at-authority scheme declares is refused",
        "beans/stone-d.md", stone("stone-d", "observations:\n  mark:\n    property: { scheme: field-codes, code: b-42 }\n    at: 2026-05-03\n    by: bea\n"),
        "'b-42' is not in the form of a field-codes code")
write("VOCAB.md", read("VOCAB.md").replace("      code_pattern: '^[A-Z][0-9]{2}$'\n", "      code_pattern: '^[A-Z]\\d{2}$'\n"))
refused("O-3 a code's form is read as the law reads every pattern, in ASCII: `\\d` is 0 to 9, and `B۴۲` in Persian "
        "digits is not in it",
        "beans/stone-d.md", stone("stone-d", "observations:\n  mark:\n    property: { scheme: field-codes, code: \"B۴۲\" }\n"
                                             "    at: 2026-05-03\n    by: bea\n"),
        "'B۴۲' is not in the form of a field-codes code")
refused("O-3 a scheme held at its authority with no code_pattern is refused",
        "VOCAB.md", read("VOCAB.md").replace("      code_pattern: '^[A-Z][0-9]{2}$'\n", ""), "states no `code_pattern`")
refused("O-3 a holding the law does not know is refused",
        "VOCAB.md", read("VOCAB.md").replace("holding: extract", "holding: borrowed"), "shipped, extract or at-authority")
refused("O-3 labels in what is no language BCP 47 writes are refused",
        "VOCAB.md", read("VOCAB.md").replace("language: fr,", "language: French,"), "no language as BCP 47 writes one")

# ---------------------------------------------------------------- O-4 configuration as data
v = read("VOCAB.md").replace("registry_files:\n", "registry_files:\n  - { registry: leave-kinds, file: extracts/leave-kinds.tsv, key: code }\n", 1)
v = v.replace("    - scheme: field-codes\n", """    - scheme: leave-kinds
      classifies: the kinds of leave an invented co-op grants
      holding: extract
      licence: CC0-1.0
      publisher: the co-op (invented)
      url: "extracts/leave-kinds.tsv"
      levels: [ { level: kind } ]
      neighbours: none
      sources: extracts/leave-kinds.tsv
    - scheme: field-codes
""", 1)
write("VOCAB.md", v)
write("extracts/leave-kinds.tsv", "code\tparent\tname\nannual\t\tannual leave\nsick\t\tsick leave\n")
rc, out = save("the co-op's kinds of leave, declared once", ["leave-kinds"], True)
check("O-4 a garden's configuration is declared once, a RULE-CHANGE", rc == 0, out[-1500:])
write("extracts/leave-kinds.tsv", read("extracts/leave-kinds.tsv") + "harvest\t\tleave to bring the harvest in\n")
rc, out = save("a kind of leave added", ["leave-kinds"])
check("...and gains a row in an ordinary saved commit, with no RULE-CHANGE",
      rc == 0 and "RULE-CHANGE" not in read("log/journal.md").split("\n## ")[-1], out[-1500:])

# ---------------------------------------------------------------- F3: a scheme marked sensitive makes its readings so
write("VOCAB.md", read("VOCAB.md").replace("      holding: extract\n      licence: CC0-1.0\n      release: \"the survey's own, 2026\"\n",
                                         "      holding: extract\n      licence: CC0-1.0\n      release: \"the survey's own, 2026\"\n"
                                         "      sensitive: special-category\n", 1))
r = run(PY, "-c", "import sys; sys.path.insert(0, 'bin'); import dmpass, dmheld; "
        "print(dmpass.sensitivity(dmpass.beans_here('.')['stone-b'], dmheld.types_law('.')))", cwd=G)
check("F3 a reading coded in a scheme marked `sensitive` makes its bean special-category, naming the path and never the value",
      "'special-category'" in r.stdout and "a code of lichen-forms at observations.crust-cover.property" in r.stdout and "35" not in r.stdout,
      r.stdout + r.stderr)
restore()

# ---------------------------------------------------------------- O-5 the one finder
code, out = tool("bin/dmknowledge.py", "find", "crust")
check("O-5 the finder reads the garden's own extract", code == 0 and "lichen-forms" in out and "crustose" in out, out)
code, out = tool("bin/dmknowledge.py", "label", "lichen-forms", "crustose", "fr")
check("O-5 a label in another language, with the words its publisher asks to be printed",
      code == 0 and "crustacé" in out and "traduction du relevé, inventée" in out, out)
code, out = tool("bin/dmknowledge.py", "tree", "lichen-forms")
check("O-5 a tree of a scheme with no parent codes lists every code at the top", code == 0 and "squamulose" in out and "transect" in out, out)
code, out = tool("bin/dmknowledge.py", "find", "tile setter")
check("O-5 `find \"tile setter\"` ranks the ISCO unit a person would pick first (7122 Floor layers and tile setters)",
      code == 0 and out.strip().splitlines()[0].split()[:2] == ["isco-08", "7122"], out)
code, out = tool("bin/dmknowledge.py", "resolve", "field-codes", "B42")
check("O-5 a lookup at the authority is REFUSED until the flow law grants that party", code != 0 and "flow law" in out, out)
code, out = tool("bin/dmknowledge.py", "gold", os.path.join(ROOT, "test", "gold", "finder.tsv"))
m = re.search(r"recall@5 = (\d+)/(\d+)", out)
FLOOR = 20 / 24   # measured on the first run (2026-09-26): 20 of 24; the misses are synonyms the titles do not hold
check(f"O-5 the gold set: recall@5 printed and held at or above its measured floor {FLOOR}",
      code == 0 and m and int(m.group(1)) / int(m.group(2)) >= FLOOR, out)
print(out.strip().splitlines()[-1] if out.strip() else "")

shutil.rmtree(T, ignore_errors=True)
print("\nobservations: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
