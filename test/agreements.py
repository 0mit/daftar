#!/usr/bin/env python3
"""Agreements (std-vocab 24.0, AGREE): a clause that occurs for each member of a reading, settled occurrence by
occurrence; a due relative to another position; a window a clause holds in and the words its permission chooses; what
brings a clause into force as a reading; a party acting for another, one that declined, every party of a role; a
repetition at several places in its cell, lasting, with closures; one being held twice over one time refused where a
garden says a term is exclusive; and a value read across gardens only at a commit the other garden published and granted.

Every fixture is INVENTED: a piano-tuning shop and its tuner, a choir, a pupil's lessons, a rehearsal room, two
gardens that share a candle. Amounts are in XTS, the code ISO 4217 keeps for testing.
Run: python3 test/agreements.py   (0 = green)
"""
import datetime, os, re, shutil, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS = []
PY = sys.executable


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-6000:]))
    if not cond:
        FAILS.append(name)


def run(*a, cwd):
    return subprocess.run(list(a), capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd,
                          env=dict(os.environ, PYTHONIOENCODING="utf-8"))


T = tempfile.mkdtemp(prefix="dmagree-")


def grow(name, gardener):
    g = os.path.join(T, name)
    r = run(PY, os.path.join(ROOT, "seed", "germinate.py"), g, "--gardener", gardener, cwd=ROOT)
    check(f"the garden {name} germinates, kept by {gardener}", r.returncode == 0, r.stdout + r.stderr)
    run("git", "config", "user.name", f"{gardener} (test)", cwd=g)
    run("git", "config", "user.email", f"{gardener}@example.org", cwd=g)
    return g


G = grow("g", "keeper")


def write(rel, text, g=G):
    p = os.path.join(g, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def read(rel, g=G):
    return open(os.path.join(g, *rel.split("/")), encoding="utf-8").read()


def save(what, names, rule_change=False, g=G, who="keeper (test)"):
    body = "- action: " + ("RULE-CHANGE (VOCAB.md) " if rule_change else "") + " ".join(f"[[{n}]]" for n in names)
    r = run(PY, "bin/dmsave.py", who, what, "--body", body, cwd=g)
    return r.returncode, r.stdout + r.stderr


def restore(g=G):
    run("git", "reset", "-q", "--hard", cwd=g)
    run("git", "clean", "-qfd", cwd=g)


def tool(*a, g=G):
    r = run(PY, *a, cwd=g)
    return r.returncode, r.stdout + r.stderr


def bean(id, genos, nature, akey, rest, own, title=None, g=None):
    return (f"---\nbean: {id}\ngenos: {genos}\ntitle: \"{title or id}\"\nstatus: active\nsummary: \"{id}, invented\"\n"
            f"nature: {nature}\n{own}"
            f"identity: {{ status: confirmed, anchors: [ {{ key: {akey}, value: \"{akey.split('_')[0]}:{id}\", class: logical, "
            f"establishing: true }} ] }}\nprovenance: {{ src: asserted-by-human, by: keeper, as_of: now }}\n"
            f"{rest}---\n{id}, invented.\n")


PERSON_OWN = "owned_by: { legal: { crown: agape } }\nresponsibility: { legal: { self: true } }\n"
CROWN = "owned_by: { legal: { crown: logos } }\nresponsibility: { legal: { parties: true } }\n"
ORG_OWN = "owned_by: { legal: { owner: { bean: keeper } } }\nresponsibility: { legal: { holder: { bean: keeper } } }\n"


def person(id, consent):
    return bean(id, "person", "empsychon", "identifier", f"consent: {{ bean: {consent} }}\n", PERSON_OWN)


def contract(id, rest):
    return bean(id, "contract", "lekton", "identifier", rest, CROWN)


# ============================================================================ the fixtures
WALK = """---
mapping: walk-tuning
kind: procedure
summary: "An invented piano-tuning shop's walk for one tuning."
steps:
  - { id: booked, do: "a customer books a tuning", by: shop, next: [ { to: tuned, when: "a tuning at home" }, { to: concert-tuned, when: "a tuning for a concert" } ] }
  - { id: tuned, do: "the tuner tunes the piano", by: tuner, next: [ { to: refunded } ] }
  - { id: concert-tuned, do: "the tuner tunes it for a concert", by: tuner, next: [ { to: concert-refunded } ] }
  - { id: refunded, do: "the fee is given back", by: shop, final: true }
  - { id: concert-refunded, do: "the concert fee is given back", by: shop, final: true }
---
The shop's walk.
"""


def tuning(id, fee, steps):
    moves = "".join(f"  - {{ course: job, at: now, step: {s}, by: ivo }}\n" for s in steps)
    return contract(id, f"""parties:
  shop: {{ who: {{ bean: fine-keys }}, role: shop, accepted: 2026-09-01 }}
  customer: {{ external: "a customer of the shop", role: customer }}
words: {{ form: spoken, agreed: 2026-09-01 }}
clauses:
  fee: {{ what: "the customer pays the fee", by: customer, to: shop, amount: {{ count: {fee}, unit: XTS }}, state: met }}
courses:
  job: {{ walk: {{ mapping: walk-tuning }} }}
moves:
{moves}""")


TERMS_ = contract("tuner-terms", """parties:
  shop: { who: { bean: fine-keys }, role: shop, accepted: 2026-09-01 }
  tuner: { who: { bean: ivo }, role: tuner, accepted: 2026-09-01 }
  van-owner: { who: { bean: ada }, role: lender, accepted: 2026-09-01, acting_for: shop }
  other-tuner: { who: { bean: bo }, role: tuner, declined: 2026-09-02 }
words: { form: spoken, agreed: 2026-09-01 }
selections:
  tunings-done: { what: "each tuning tuned", steps: [ { id: t, op: select, genos: contract, where: [ { path: courses.job, reached: tuned } ] } ] }
  concerts-done: { what: "each concert tuning", steps: [ { id: t, op: select, genos: contract, where: [ { path: courses.job, reached: concert-tuned } ] } ] }
  tunings-refunded: { what: "each tuning refunded", steps: [ { id: t, op: select, genos: contract, where: [ { path: courses.job, reached: refunded } ] } ] }
  parts-arrived: { what: "the parts have arrived: a document of them is here", steps: [ { id: d, op: select, genos: document } ] }
clauses:
  pay:
    what: "the shop pays the tuner a tenth of each tuning's fee"
    by: shop
    to: tuner
    amount: { count: 10, unit: percent }
    each: tunings-done
    of: clauses.fee.amount
    falls_due: { from: "@occurrence", after: { of: time, in: gregorian-civil, level: month, count: 1 }, at: "10" }
  pay-concert:
    what: "the shop pays the tuner fifteen parts in a hundred of each concert tuning's fee"
    by: shop
    to: tuner
    amount: { count: 15, unit: percent }
    each: concerts-done
    of: clauses.fee.amount
  refund:
    what: "the tuner gives back a tenth of each refunded tuning's fee"
    by: tuner
    to: shop
    amount: { count: 10, unit: percent }
    each: tunings-refunded
    of: clauses.fee.amount
  van:
    what: "the tuner may take the shop's van"
    by: tuner
    permission: permitted
    during: { of: time, from: 2026-11-01, to: 2026-11-14 }
  parts-said: { what: "the shop fits the new hammers", by: shop, when: { said: "the parts have arrived" } }
  parts-read: { what: "the shop pays for the parts", by: shop, when: { selection: parts-arrived } }
transactions:
  october:
    what: "the October payout"
    amount: { count: 30, unit: XTS }
    paid_by: [ { party: shop } ]
    during: { of: time, from: 2026-10-01, to: 2026-10-31 }
    settles:
      - { clause: pay, occurrence: tune-a, amount: { count: 12, unit: XTS } }
      - { clause: pay-concert, occurrence: tune-b, amount: { count: 18, unit: XTS } }
""")

CHOIR = contract("choir-dues", """parties:
  ana: { who: { bean: ana }, role: member, accepted: 2026-09-01 }
  bo: { who: { bean: bo }, role: member, accepted: 2026-09-01 }
  keeper: { who: { bean: keeper }, role: treasurer, accepted: 2026-09-01 }
words: { form: spoken, agreed: 2026-09-01 }
clauses:
  dues: { what: "each member pays the season's dues", by_role: member, to: keeper, amount: { count: 20, unit: XTS }, due: 2026-12-01 }
""")

today = datetime.date.today()
tue = today + datetime.timedelta(days=(1 - today.weekday()) % 7 or 7)       # the next Tuesday after today
closed = tue                                                                 # the next Tuesday: a holiday
LESSONS = contract("lessons", f"""parties:
  teacher: {{ who: {{ bean: keeper }}, role: teacher, accepted: 2026-09-01 }}
  pupil: {{ who: {{ bean: pip }}, role: pupil, accepted: 2026-09-01 }}
  parent: {{ who: {{ bean: ada }}, role: parent, accepted: 2026-09-01, acting_for: pupil }}
words: {{ form: spoken, agreed: 2026-09-01 }}
clauses:
  lesson:
    what: "the teacher gives a lesson"
    by: teacher
    to: pupil
    due: "{(tue - datetime.timedelta(days=7)).isoformat()}T16:00+03:00"
    every: {{ of: time, in: iso-week, each: week, at: ["2", "4"], lasts: {{ of: time, measure: {{ count: 1, unit: hour }} }}, closures: [ "{closed.isocalendar()[0]}-W{closed.isocalendar()[1]:02d}-{closed.isoweekday()}" ] }}
""")

write("mappings/walk-tuning.md", WALK)
write("beans/fine-keys.md", bean("fine-keys", "org", "lekton", "identifier", "", ORG_OWN))
for p in ("ivo", "ada", "bo"):
    write(f"beans/{p}.md", person(p, "tuner-terms"))
write("beans/ana.md", person("ana", "choir-dues"))
write("beans/pip.md", person("pip", "lessons"))
write("beans/tune-a.md", tuning("tune-a", 120, ["booked", "tuned"]))
write("beans/tune-b.md", tuning("tune-b", 120, ["booked", "concert-tuned"]))
write("beans/tune-c.md", tuning("tune-c", 80, ["booked", "tuned", "refunded"]))
write("beans/tuner-terms.md", TERMS_)
write("beans/choir-dues.md", CHOIR)
write("beans/lessons.md", LESSONS)
rc, out = save("the invented agreements", ["tuner-terms", "choir-dues", "lessons", "tune-a", "tune-b", "tune-c", "walk-tuning",
                                            "fine-keys", "ivo", "ada", "bo", "ana", "pip"])
check("the invented fixtures commit through the hook with 0 errors — occurrences, settlements, a permission's window, "
      "two conditions, a party acting for another, one declined, a role, a repetition at two places with a closure",
      rc == 0, out)

# ============================================================================ the ledger
code, led = tool("bin/dmledger.py", "tuner-terms")
check("the ledger reads it", code == 0, led)
check("...each occurrence of the tenth: tune-a and tune-c tuned, tune-b not (it was a concert tuning)",
      re.search(r"occurs for each member of tunings-done: 2 occurrences", led) and "tune-a" in led, led)
check("...the amount owed for each is the tenth OF ITS OWN fee, exactly: 12 XTS of 120, 8 XTS of 80",
      "owed 12 XTS (10 percent of 120 XTS)" in led and "owed 8 XTS (10 percent of 80 XTS)" in led, led)
check("...one payment settles two occurrences under two rates, each its own amount",
      "settled 12 XTS by october" in led and "settled 18 XTS by october" in led and "owed 18 XTS (15 percent of 120 XTS)" in led, led)
check("...what is outstanding: tune-a nothing, tune-c all of it",
      "outstanding 0 XTS" in led and "outstanding 8 XTS" in led, led)
first_due = (today.replace(day=1) + datetime.timedelta(days=32)).replace(day=10)
check("...when each fell due: one month of gregorian-civil after it entered, on the 10th of the month reached",
      f"due {first_due.isoformat()}" in led, led)
refund = led.split("refund", 1)[-1].split("van", 1)[0] if "refund" in led else ""
check("...a tuning refunded STAYS an occurrence of the tenth, and occurs ONCE under the reverse clause: the tuner owes "
      "one refund of 8 XTS, not two", "1 occurrence" in refund and refund.count("owed 8 XTS") == 1, led)
check("...a permission is printed as one, with its window, and never as owed",
      "a permission: the party may — nothing is owed by it" in led and "holds within 2026-11-01 to 2026-11-14" in led
      and not re.search(r"van[^\n]*\n[^\n]*not yet known: amount", led), led)
check("...a condition in words is shown as said; a reading that does not hold is NOT YET in force",
      'in force when: "the parts have arrived"' in led and "clauses not yet in force (1)" in led
      and "in force while the reading parts-arrived holds" in led, led)
check("...a party acting for another, and one that declined, are said",
      "van-owner acts for shop" in led and "other-tuner declined on 2026-09-02" in led, led)
code, choir = tool("bin/dmledger.py", "choir-dues")
check("...a clause binding every party of a role", "by every party whose role is member" in choir, choir)

# the reading brings the clause into force once a document of the parts is here
write("beans/parts-note.md", bean("parts-note", "document", "lekton", "identifier", "located_at: [ { system: physical, openness: unknown } ]\n",
                                  ORG_OWN))
rc, out = save("the parts' delivery note", ["parts-note"])
code, led2 = tool("bin/dmledger.py", "tuner-terms")
check("...and once the reading holds (a delivery note is here), the clause is in force", rc == 0 and
      "clauses not yet in force" not in led2 and "in force while the reading parts-arrived holds" in led2, out + led2)

# ============================================================================ dmstale
code, st = tool("bin/dmstale.py", "--days", "400")
check("dmstale warns of each unsettled occurrence at its relative due, and of none settled",
      "tuner-terms.clauses[pay]@tune-c" in st and "clauses[pay]@tune-a" not in st, st)
check("...a permission's window closing is said in a permission's words",
      "clauses[van]" in st and "a permission lapses: after that day the party may no longer" in st, st)
check("...an obligation in its own words", "a clause falls due, and from that day the party it is owed to is owed it" in st, st)
check("...a lesson on each Tuesday and Thursday, each lasting an hour, and the closure skipped and said",
      re.search(r"each week in iso-week at \['?2'?, '?4'?\]", st) and "each lasting 1 hour" in st and "a closure the repetition names" in st, st)

# ============================================================================ refusals
def refused(name, rel, old, new, want, names=("tuner-terms",), rule_change=False):
    txt = read(rel)
    if old not in txt:
        check(name + " (fixture)", False, f"{old!r} not in {rel}")
        return
    write(rel, txt.replace(old, new, 1))
    rc, out = save(name, list(names), rule_change=rule_change)
    check(name, rc != 0 and want in out, out[-900:])
    restore()


refused("a condition in prose, the pre-24.0 form, is refused: `when` is {selection} or {said}",
        "beans/tuner-terms.md", 'when: { said: "the parts have arrived" }', 'when: "the parts"', "when")
refused("an `each` over a reading an occurrence can lose (`at_step`) is refused: an occurrence never vanishes",
        "beans/tuner-terms.md", "reached: tuned } ] } ] }", "at_step: tuned } ] } ] }", "its selection can lose an occurrence")
refused("both `due` and `falls_due` is refused", "beans/tuner-terms.md", "    each: tunings-done\n",
        "    each: tunings-done\n    due: 2026-10-10\n", "due")
refused("`of` on a clause that occurs for nothing is refused", "beans/tuner-terms.md",
        "  van:\n", "  van:\n    of: clauses.fee.amount\n", "occurs for none")
refused("a due relative to `@occurrence` on a clause that occurs for nothing is refused", "beans/tuner-terms.md",
        "    permission: permitted\n", '    permission: permitted\n    falls_due: { from: "@occurrence", after: { of: time, measure: { count: 7, unit: day } } }\n',
        "occurs for none")
refused("`settles` naming a clause with no `each` is refused", "beans/tuner-terms.md",
        "{ clause: pay-concert, occurrence: tune-b,", "{ clause: van, occurrence: tune-b,", "occurs for nothing")
refused("a party acting for itself is refused", "beans/tuner-terms.md", "acting_for: shop", "acting_for: van-owner",
        "acting_for names the party itself")
refused("a list `at` naming one place twice is refused", "beans/lessons.md", 'at: ["2", "4"]', 'at: ["2", "2"]',
        "names one place twice", names=("lessons",))

# N27: a rehearsal room lent twice over overlapping days, where the garden says `parties` is exclusive
voc = read("VOCAB.md")
overlay = "  - { term: parties, schema: { exclusive: { extent: during, being: who, role: role } } }\n"
voc = re.sub(r"(?m)^local_terms: \[\].*$", "local_terms:\n" + overlay.rstrip("\n"), voc, count=1)
check("(the overlay is written into VOCAB.md)", "term: parties, schema: { exclusive" in voc, voc[:400])
write("VOCAB.md", voc)
write("beans/room-b.md", bean("room-b", "org", "lekton", "identifier", "", ORG_OWN))


def booking(id, frm, to, extra=""):
    return contract(id, f"""parties:
  keeper: {{ who: {{ bean: keeper }}, role: hirer, accepted: 2026-09-01 }}
  room: {{ who: {{ bean: room-b }}, role: venue, during: {{ of: time, from: {frm}, to: {to} }}{extra} }}
words: {{ form: spoken, agreed: 2026-09-01 }}
""")


write("beans/book-1.md", booking("book-1", "2026-12-01", "2026-12-05"))
write("beans/book-2.md", booking("book-2", "2026-12-10", "2026-12-12"))
write("beans/book-3.md", booking("book-3", "2026-12-04", "2026-12-06", ", declined: 2026-09-03"))
rc, out = save("a rehearsal room booked, and `parties` exclusive here", ["room-b", "book-1", "book-2", "book-3"], rule_change=True)
check("a garden makes `parties` exclusive in its VOCAB.md; bookings that do not overlap, and one declined, pass",
      rc == 0, out[-900:])
refused("...a second booking of the room as venue over overlapping days is refused, naming both agreements",
        "beans/book-2.md", "from: 2026-12-10", "from: 2026-12-03", "book-1", names=("book-2",))

# N9 in the ledger: an allowance read from the one extent its entries' term declares — the TERM of `leave.*`, not `*`
LEAVE_TERM = """  - term: leave
    meaning: "the leave a person takes, span by span, invented"
    context_keys: [leave]
    schema:
      shape: open_map_of_entries
      attrs:
        during: { required: true, in: extent, meaning: "the days taken" }
    merge: { cardinality: multi, order: by-key }
"""
write("VOCAB.md", read("VOCAB.md").replace("local_terms:\n", "local_terms:\n" + LEAVE_TERM, 1))
ly = today.year - 1
write("beans/leave-terms.md", contract("leave-terms", f"""parties:
  keeper: {{ who: {{ bean: keeper }}, role: employer, accepted: 2026-09-01 }}
  pip: {{ who: {{ bean: pip }}, role: employee, accepted: 2026-09-01 }}
words: {{ form: spoken, agreed: 2026-09-01 }}
selections:
  taken: {{ what: "the leave taken", steps: [ {{ id: l, op: select, entries: "leave.*" }} ] }}
clauses:
  leave: {{ what: "twenty days' leave in each two years", by: keeper, to: pip, amount: {{ count: 20, unit: day }}, within: {{ of: time, in: gregorian-civil, level: year, count: 2 }}, used_by: taken }}
leave:
  spring: {{ during: {{ of: time, from: {ly}-03-02, to: {ly}-03-06 }} }}
  autumn: {{ during: {{ of: time, from: {ly}-11-02, to: {ly}-11-04 }} }}
"""))
rc, out = save("an allowance of leave", ["leave-terms"], rule_change=True)
check("a clause with `within` and `used_by`, over a garden's own term of spans, is saved", rc == 0, out[-900:])
code, led = tool("bin/dmledger.py", "leave-terms")
check("...and the ledger reads how much of it is used, from the one extent the term declares",
      f"used 8 day of 20 day within 2 year of gregorian-civil ending {today.isoformat()}" in led, led)

# ============================================================================ N35: a reading across gardens
H = grow("h", "hana")
gid = run("git", "rev-list", "--max-parents=0", "HEAD", cwd=G).stdout.split()[0][:12]
hid = run("git", "rev-list", "--max-parents=0", "HEAD", cwd=H).stdout.split()[0][:12]


def garden_bean(bid, gidv, owner, at=None):
    loc = f"located_at: [ {{ system: unix-filesystem, openness: here, at: \"{at}\" }} ]\n" if at else ""
    return (f"---\nbean: {bid}\ngenos: garden\ntitle: \"{bid}\"\nstatus: active\nsummary: \"another garden, kept by {owner}\"\n"
            f"nature: lekton\nowned_by: {{ legal: {{ owner: {{ bean: {owner} }} }} }}\n"
            f"responsibility: {{ legal: {{ holder: {{ bean: {owner} }} }} }}\n"
            f"identity: {{ status: confirmed, anchors: [ {{ key: garden_id, value: \"{gidv}\", class: logical, establishing: true }} ] }}\n"
            f"provenance: {{ src: asserted-by-human, by: keeper, as_of: now }}\n{loc}---\nA garden.\n")


# garden h keeps a candle and knows garden g, kept by `keeper` as h knows them
write("beans/candle.md", bean("candle", "contract", "lekton", "identifier", """parties:
  hana: { who: { bean: hana }, role: holder, accepted: 2026-09-01 }
words: { form: spoken, agreed: 2026-09-01 }
clauses:
  share: { what: "the share of the candle", by: hana, amount: { count: 50, unit: percent } }
""", CROWN), g=H)
# h's own record of g's gardener: a person kept by name because the garden they keep is met here (F2)
write("beans/keeper.md", bean("keeper", "person", "empsychon", "identifier", "", PERSON_OWN), g=H)
write("beans/g-garden.md", garden_bean("g-garden", gid, "keeper"), g=H)
rc, out = save("the candle, and the garden g", ["candle", "g-garden", "keeper"], g=H, who="hana (test)")
check("garden h holds a candle and records garden g", rc == 0, out[-600:])
import socket
HOST = socket.gethostname().lower()
write("beans/this-host.md", f"""---
bean: this-host
genos: host
title: "the machine both gardens are kept on"
status: active
summary: "an invented laptop"
nature: soma
os: linux
identity: {{ status: confirmed, anchors: [ {{ key: hostname, value: "{HOST}", class: network, establishing: false }}, {{ key: serial, value: "SN-AGREE-1", class: hardware, establishing: true }} ] }}
provenance: {{ src: asserted-by-human, by: keeper, as_of: now }}
{ORG_OWN}roots:
  hgarden: {{ system: unix-filesystem, at: "{HOST}:{H}", observed: 2026-09-01 }}
---
A laptop.
""")
write("beans/hana.md", bean("hana", "person", "empsychon", "identifier", "", PERSON_OWN))
write("beans/h-garden.md", garden_bean("h-garden", hid, "hana", at="root:hgarden"))
rc, out = save("garden h recorded here", ["h-garden", "hana", "this-host"])
check("garden g records garden h, located on this host", rc == 0, out[-600:])
sys.path.insert(0, os.path.join(G, "bin"))
code, out = tool("bin/dmacross.py", "read", "h-garden", "candle:clauses.share.amount")
check("without a grant, a reading across gardens is REFUSED (NotGranted)", code == 1 and "NotGranted" in out, out)
txt = read("beans/candle.md", g=H).replace("clauses:\n", "grants:\n  to-g: { act: read, audience: { who: keeper }, why: \"garden g may read the candle's share\" }\nclauses:\n", 1)
write("beans/candle.md", txt, g=H)
rc, out = save("garden g may read the candle", ["candle"], g=H, who="hana (test)")
code, out2 = tool("bin/dmacross.py", "read", "h-garden", "candle:clauses.share.amount")
check("...granted to the person h's own garden bean for g is owned by, it is read at h's published commit", rc == 0 and
      code == 0 and "'count': 50" in out2, out + out2)
run("git", "checkout", "-qb", "side", cwd=H)
write("beans/candle.md", read("beans/candle.md", g=H).replace("count: 50", "count: 60"), g=H)
save("a share not published", ["candle"], g=H, who="hana (test)")
side = run("git", "rev-parse", "HEAD", cwd=H).stdout.strip()
run("git", "checkout", "-q", "master", cwd=H)
code, out = tool("bin/dmacross.py", "read", "h-garden", "candle:clauses.share.amount", "--commit", side)
check("...and at a commit h never published (a side branch) it is REFUSED (NotPublished)", code == 1 and "NotPublished" in out, out)
check("...and nothing was written in garden h by reading it", run("git", "status", "--porcelain", cwd=H).stdout.strip() == "", "")

shutil.rmtree(T, ignore_errors=True)
print(f"\nagreements: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
