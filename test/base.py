#!/usr/bin/env python3
"""The shapes release 24.0's parts share (BASE): what they let a garden write, and what they refuse by name.

Grows a garden for an invented choir and declares one local term that uses every new construct of the schema language:
`at_most_one_of`, a compound `keyed_by`, an `in: entries` with `one_of` and `at_most_one_of`, an extent counted in cells of
a calendar's level, and the value types `date_or_moment` and `field_path`. A `selections` entry is read by the gate as the
law's form of a reading, and named from another term by `key_of: selections`. Every example is invented.
"""
import os, sys, subprocess, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS = []

def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:900]))
    if not cond:
        FAILS.append(name)

def run(*a, cwd=None):
    return subprocess.run(list(a), capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd)

T = tempfile.mkdtemp(prefix="dmbase-")
G = os.path.join(T, "g")
r = run("sh", os.path.join(ROOT, "seed", "germinate.sh"), G, "--gardener", "keeper", cwd=ROOT)
check("a garden germinates from the release, and the new law loads", r.returncode == 0 and "0 error" in r.stdout, r.stdout + r.stderr)

TERM = """  - term: rehearsals
    meaning: "when a section of the choir rehearses, where, and what it sings"
    context_keys: [rehearsals]
    schema:
      shape: list_of_entries
      at_most_one_of: %(at_most)s
      keyed_by: [section, day]
      attrs:
        section: { required: true, in: { type: kebab }, meaning: "the section" }
        day:     { required: true, in: { type: date_or_moment }, meaning: "the day, or the moment" }
        room:    { in: prose, meaning: "a room" }
        hall:    { in: prose, meaning: "a hall" }
        length:  { in: extent, meaning: "how long the run of rehearsals lasts" }
        score:   { in: { type: field_path }, meaning: "where the score is read" }
        met_by:  { in: { key_of: selections }, meaning: "the reading that says who comes" }
        parts:
          meaning: "the parts sung"
          in:
            entries:
              voice: { in: { type: kebab } }
              sheet: { in: { type: kebab } }
            one_of: [voice, sheet]
            at_most_one_of: [[voice, sheet]]%(expiry)s
    merge: { cardinality: multi, order: by-section+day }
"""
V = os.path.join(G, "VOCAB.md")
VOCAB0 = open(V).read()
assert "local_terms: []" in VOCAB0, "the germinated VOCAB.md no longer says `local_terms: []`"   # a no-op edit is a bug

def vocab(at_most="[[room, hall]]", expiry=""):
    open(V, "w").write(VOCAB0.replace("local_terms: []", "local_terms:\n" + TERM % {"at_most": at_most, "expiry": expiry}, 1))

BEAN = os.path.join(G, "beans", "choir-book.md")
INPUTS_OK = ""
STEPS = """      - { id: people, op: select, genos: person }
      - { id: how-many, op: count, of: people }"""
R1 = '{ section: altos, day: 2026-10-28, room: "the small room", length: { of: time, in: gregorian-civil, level: month, count: 1 }, score: "parties[role=seller].who>title", met_by: members, parts: [ { voice: alto } ] }'
R2 = '{ section: altos, day: "2026-10-28 11:00-05:00", hall: "the hall" }'

def gate(rows=(R1, R2), inputs=INPUTS_OK):
    open(BEAN, "w").write("""---
bean: choir-book
genos: org
title: "the choir's book"
status: active
summary: "an invented choir's book of its members and its rehearsals"
nature: lekton
owned_by: { legal: { owner: { bean: keeper } } }
responsibility: { legal: { holder: { bean: keeper } } }
identity: { status: provisional, anchors: [] }
provenance: { src: asserted-by-human, by: keeper, as_of: 2026-09-25 }
selections:
  members:
    what: "the people who sing in the choir"
""" + inputs + """    steps:
""" + STEPS + """
rehearsals:
""" + "".join(f"  - {x}\n" for x in rows) + "---\n\nThe choir's book.\n")
    r = run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G)
    return r.stdout + r.stderr

vocab()
ok = gate()
check("a bean with a `selections` entry (select, then count) passes, and so does every new construct used rightly",
      "0 error(s), 0 warning(s)" in ok, ok[-900:])

# -- selections ----------------------------------------------------------------------------------------------------
out = gate(inputs="    inputs:\n      - { name: asker, origin: telepathy }\n")
check("an input of origin `telepathy` is refused by name", "telepathy" in out and "is not `{act, nature?, by?}`" in out, out[-900:])
out = gate(inputs="    inputs:\n      - { name: asker, origin: { act: dreamt } }\n")
check("...an input whose act is no row of `acts` is refused, the rows named",
      "act 'dreamt' is not a row of `acts`" in out, out[-900:])
out = gate(inputs="    inputs:\n      - { name: asker, origin: { act: said, by: reader } }\n")
check("...and one whose `by` its act does not list (the reader reads the clock; it says nothing)",
      "by 'reader' is not one of the names `acts[said]` lists" in out, out[-900:])
out = gate(inputs="    inputs:\n      - { name: asker, origin: { act: said } }\n      - { name: asker, origin: { act: read, nature: soma, by: reader } }\n")
check("two inputs of one name are refused, both named", "two entries for name 'asker' (0 and 1)" in out, out[-900:])
out = gate(rows=(R1.replace("met_by: members", "met_by: nobody"), R2))
check("`key_of: selections` refuses a key the bean does not declare, and names the one it does",
      "nobody" in out and "members" in out and "0 error" not in out, out[-900:])
out = gate(rows=(R1.replace("met_by: members", 'met_by: "choir-book#members"'), R2))
check("the in-flight spelling `<bean>#<key>` is refused", "choir-book#members" in out and "0 error" not in out, out[-900:])

# -- at_most_one_of, nested one_of, compound keyed_by ------------------------------------------------------------------
out = gate(rows=(R1, R2.replace('hall: "the hall"', 'hall: "the hall", room: "the small room"')))
check("`at_most_one_of` refuses two of a group, and names both", "states `room` and `hall`, and carries at most one of ['room', 'hall']" in out, out[-900:])
out = gate(rows=(R1.replace("parts: [ { voice: alto } ]", "parts: [ { sheet: s-1, voice: alto } ]"), R2))
check("a nested `at_most_one_of` refuses two of a group inside an entry", "carries at most one of ['voice', 'sheet']" in out, out[-900:])
out = gate(rows=(R1.replace("parts: [ { voice: alto } ]", "parts: [ { } ]"), R2))
check("a nested `one_of` refuses an entry holding none", "needs one of ['voice', 'sheet']" in out, out[-900:])
out = gate(rows=(R1, R2, '{ section: altos, day: 2026-10-28, hall: "the other hall" }'))
check("a compound `keyed_by` refuses a repeated combination, naming both entries",
      "rehearsals[0] and rehearsals[2] hold the same section + day" in out, out[-900:])
check("... and a different combination is not a repeat", "rehearsals[1]" not in out.split("hold the same")[0][-40:], out[-900:])

# -- the extent in cells of a level ----------------------------------------------------------------------------------
out = gate(rows=(R1.replace("level: month", "level: fortnight"), R2))
check("`level: fortnight` is refused: gregorian-civil has no such level", "level 'fortnight' is not a level of gregorian-civil" in out, out[-900:])
out = gate(rows=(R1.replace("level: month, count: 1", "level: month, count: 0"), R2))
check("a count of no cells is refused", "count must be a positive whole number of cells, not 0" in out, out[-900:])
out = gate(rows=(R1.replace("level: month, count: 1", "level: month, count: 1, measure: { count: 30, unit: day }"), R2))
check("a length both in cells and as a measure is refused", "states both `measure` and `level`" in out, out[-900:])
out = gate(rows=(R1.replace("in: gregorian-civil, level: month", "level: month"), R2))
check("a level with no system named is refused", "a level belongs to its system, and `in` names none" in out, out[-900:])

# -- date_or_moment ----------------------------------------------------------------------------------------------------
for bad, why in (('"2026-02-30"', "a day the calendar does not have"), ('"2026-10-28 11:00"', "a moment with no offset")):
    out = gate(rows=(R1, R2.replace('"2026-10-28 11:00-05:00"', bad)))
    check(f"`date_or_moment` refuses {bad}: {why}", "rehearsals[1].day" in out and "0 error" not in out, out[-900:])

# -- field_path --------------------------------------------------------------------------------------------------------
for good in ("over.thing>clauses.advance.amount", "c-0101", "ledger-a:transactions.t-07", "observations.*.property",
             "steps[id=fix].gives", "@occurrence", "located_at[system=geographic].at"):
    out = gate(rows=(R1.replace("parties[role=seller].who>title", good), R2))
    check(f"`field_path` takes {good}", "0 error(s)" in out, out[-900:])
for bad in ("a..b", ".a", "a.", "A.b", "a>", "@other", "a[b]", "a b", "a:b:c"):
    out = gate(rows=(R1.replace("parties[role=seller].who>title", bad), R2))
    check(f"`field_path` refuses {bad!r}", "must be a path into what beans hold" in out, out[-900:])
sys.path.insert(0, os.path.join(ROOT, "bin"))
import dmparse
_s = dmparse.path_read("ledger-a:parties[role=seller].who>title")
check("the one path reader reads a bean, a match and a followed ref",
      [(x.bean, x.key, x.match, x.follow) for x in _s] == [("ledger-a", "parties", ("role", "seller"), False),
                                                         (None, "who", None, False), (None, "title", None, True)], _s)
check("the path reader says where a path stops being one", "character 3" in (dmparse.path_problem("a..b") or ""),
      dmparse.path_problem("a..b"))

# -- the law's own shapes ----------------------------------------------------------------------------------------------
vocab(at_most="[room]")
out = gate()
check("`at_most_one_of` written as a flat list is refused by name", "`schema.at_most_one_of` is a list of groups" in out, out[-900:])
vocab(expiry="\n      expiry: { attr: day, notice: { of: time, measure: { count: 7, unit: day } }, why: \"a rehearsal missed\", permission: mood }")
out = gate()
check("an `expiry` whose `permission` names no attribute of its term is refused", "rehearsals.schema.expiry.permission names `mood`, which is no attribute of rehearsals" in out, out[-900:])
vocab()

r = run(sys.executable, os.path.join(ROOT, "bin", "dmrules.py"), cwd=G)
check("dmrules prints the three new constructs, the four new value types and the `selections` term",
      all(w in r.stdout for w in ("at_most_one_of", "keyed_by", "exclusive", "date_or_moment", "field_path", "held_pointer",
                                  "language_tag", "selections")), r.stdout[-600:])

print(f"\n{len(FAILS)} failed" + (": " + ", ".join(FAILS) if FAILS else ""))
sys.exit(1 if FAILS else 0)
