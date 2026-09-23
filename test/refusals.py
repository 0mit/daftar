#!/usr/bin/env python3
"""What the gate refuses, and that it REFUSES rather than crashes.

A refusal is the gate's whole answer to a person: what is wrong, and what to write instead. A traceback is no answer —
the commit is blocked with nothing said, and every other finding of the run is lost with it. Each case here is a value
the gate once took, or once died on; each must now be refused by name, and nothing may end in a traceback.

  the manifest       judged as itself: a gardener naming no bean, or a bean of a kind the law says keeps no garden;
                     `garden:` or `extends:` missing; a release nobody made; front matter that is a list or a word (and
                     the same for VOCAB.md and a bean) — and a fresh untagged garden still passes
  names              a name a garden gave is `<kind>:<name>`; an identifier someone else assigned is never qualified
  a garden's record  `test` belongs to a `garden` bean; a `garden` bean is never this garden itself
  one per key        two payers named `sam` in one transaction
  numbers            what YAML 1.1 reads as an integer nobody wrote (`010`, `0x64`, `1:30`, `0b11`, `1_000`), untagged or
                     tagged `!!int`, and a count or a share past the digits every reader holds
  days               a day its calendar does not have, and a year its reckoning cannot reach — where a recurrence starts
                     and ends included
  keys               a key YAML reads as a boolean or a number, beside the names it should have been
  the facets         one root, which every facet reaches
  the journal        a line that some readers would split in two
  the messages       what to do next, in a form every shell runs

Every name is neutral (sam, ali, ben) and every amount is in XTS, the code ISO 4217 keeps for testing.
"""
import os, re, sys, subprocess, tempfile, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:900]))
    if not cond:
        FAILS.append(name)


def run(*a, cwd=None):
    return subprocess.run(list(a), capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=cwd)


T = tempfile.mkdtemp(prefix="dmrefuse-")
G = os.path.join(T, "garden-a")
r = run(sys.executable, os.path.join(ROOT, "seed", "germinate.py"), G, "--gardener", "sam", cwd=T)
check("a garden germinates, kept by sam", r.returncode == 0 and os.path.isfile(os.path.join(G, "beans", "sam.md")), r.stdout + r.stderr)
run("git", "config", "user.name", "probe", cwd=G)
run("git", "config", "user.email", "probe@example.org", cwd=G)
GID = run("git", "rev-list", "--first-parent", "--max-parents=0", "HEAD", cwd=G).stdout.split()[-1][:12]
MANIFEST = open(os.path.join(G, "GARDEN.md"), encoding="utf-8").read()
TRACES = []


def put(rel, text):
    p = os.path.join(G, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def drop(rel):
    p = os.path.join(G, *rel.split("/"))
    if os.path.exists(p):
        os.remove(p)


def gate():
    r = run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G)
    out = r.stdout + r.stderr
    if "Traceback" in out:
        TRACES.append(out[-600:])
    return out


def person(bid, extra=""):
    return (f'---\nbean: {bid}\nkind: person\ntitle: "{bid}"\nstatus: active\nsummary: "a person"\nnature: living\n'
            f'owned_by: {{ legal: {{ crown: love }} }}\nresponsibility: {{ legal: {{ self: true }} }}\n'
            f'identity: {{ status: confirmed, anchors: [ {{ key: person_id, value: "person:{bid}", class: logical, establishing: true }} ] }}\n'
            f'provenance: {{ src: asserted-by-human, by: sam, as_of: 2026-09-01 }}\n{extra}---\n{bid}.\n')


def thing(bid, anchor, extra=""):
    return (f'---\nbean: {bid}\nkind: program\ntitle: "{bid}"\nstatus: active\nsummary: "a program"\nnature: metaphysical\n'
            f'owned_by: {{ legal: {{ owner: {{ bean: sam }} }} }}\nresponsibility: {{ legal: {{ holder: {{ bean: sam }} }} }}\n'
            f'identity: {{ status: confirmed, anchors: [ {{ key: program_id, value: "{anchor}", class: logical, establishing: true }} ] }}\n'
            f'provenance: {{ src: asserted-by-human, by: sam, as_of: 2026-09-01 }}\n{extra}---\nA program.\n')


def deal(extra, parties="  sam: { who: { bean: sam }, accepted: 2026-09-01 }\n  ali: { who: { bean: ali }, accepted: 2026-09-01 }\n"):
    put("beans/deal.md", '---\nbean: deal\nkind: contract\ntitle: "a deal"\nstatus: active\nsummary: "a deal"\nnature: metaphysical\n'
        'owned_by: { legal: { crown: logos } }\nresponsibility: { legal: { parties: true } }\n'
        'identity: { status: confirmed, anchors: [ { key: contract_id, value: "contract:deal", class: logical, establishing: true } ] }\n'
        'provenance: { src: asserted-by-human, by: sam, as_of: 2026-09-01 }\n'
        f'parties:\n{parties}words: {{ form: spoken, agreed: 2026-09-01 }}\n{extra}---\nA deal.\n')
    return gate()


def tx(amount="{ count: 900, unit: XTS }", paid="[ { party: sam } ]", borne=None):
    return deal("transactions:\n  t: { what: \"a thing\", amount: " + amount + ", paid_by: " + paid
                + (", borne_by: " + borne if borne else "") + " }\n")


ok = lambda out: " 0 error(s)" in out
put("beans/ali.md", person("ali"))
check("(setup) sam's garden with ali in it passes", ok(gate()), gate()[-600:])

# ---------------------------------------------------------------- THE MANIFEST, JUDGED AS ITSELF
out = gate()
check("a fresh garden's manifest passes as written, the release it runs included",
      ok(out) and re.search(r'^daftar_release: "(v\d+\.\d+\.\d+|untagged ([0-9a-f]+|unknown))"', MANIFEST, re.M), out[-400:])


def manifest(text):
    put("GARDEN.md", text)
    out = gate()
    put("GARDEN.md", MANIFEST)
    return out


out = manifest(re.sub(r'(?m)^daftar_release:.*$', 'daftar_release: "untagged 0a1b2c3"', MANIFEST))
check("...`untagged <commit>` — what germinate writes from a checkout on no tag — is a release", ok(out), out[-400:])
out = manifest(re.sub(r'(?m)^gardener:.*$', 'gardener: bob', MANIFEST))
check("a gardener naming no bean is refused, saying what to write first",
      "GARDEN.md: manifest.gardener 'bob' is not the id of a bean this garden holds" in out and "write beans/bob.md first" in out, out[-500:])
put("beans/tool.md", thing("tool", "tool"))
out = manifest(re.sub(r'(?m)^gardener:.*$', 'gardener: tool', MANIFEST))
check("a gardener of a kind the law does not let keep a garden is refused, the kinds read from the law",
      "manifest.gardener 'tool' is a program, and this attribute names a bean of kind person or org" in out, out[-500:])
drop("beans/tool.md")
out = manifest(re.sub(r'(?m)^garden:.*\n', '', MANIFEST))
check("a manifest with no `garden:` is refused", "GARDEN.md: `garden:` is missing" in out, out[-500:])
out = manifest(re.sub(r'(?m)^extends:.*\n', '', MANIFEST))
check("a manifest with no `extends:` is refused", "GARDEN.md: `extends:` is missing" in out, out[-500:])
out = manifest(re.sub(r'(?m)^garden:.*$', 'garden: "Not Kebab!"', MANIFEST))
check("a garden name that is not kebab-case is refused", "manifest.garden 'Not Kebab!' must be kebab-case" in out, out[-500:])
out = manifest(re.sub(r'(?m)^daftar_release:.*$', 'daftar_release: "bogus"', MANIFEST))
check("a release nobody made is refused", "manifest.daftar_release 'bogus' is not in the form" in out, out[-500:])
for shape, text in (("a list", "---\n- a\n- b\n---\nbody\n"), ("a word", "---\njust text\n---\nbody\n")):
    out = manifest(text)
    check(f"a manifest whose front matter is {shape} is refused by name, not a traceback",
          "GARDEN.md: its front matter does not read (not a mapping)" in out and "Traceback" not in out, out[-500:])
    VOCAB0 = open(os.path.join(G, "VOCAB.md"), encoding="utf-8").read()
    put("VOCAB.md", text)
    out = gate()
    put("VOCAB.md", VOCAB0)
    check(f"...and so is a VOCAB.md whose front matter is {shape}",
          "VOCAB.md: its front matter does not read (not a mapping)" in out and "Traceback" not in out, out[-500:])
    put("beans/odd.md", text)
    out = gate()
    drop("beans/odd.md")
    check(f"...and a bean whose front matter is {shape}", "odd: front-matter invalid (not a mapping)" in out
          and "Traceback" not in out, out[-500:])
out = manifest(MANIFEST.replace("\n---", "\nseeds_from: []\n---", 1))
check("a retired manifest key is refused, saying where it went", "`seeds_from` is no key of the manifest" in out
      and "retired: nothing" in out, out[-500:])

# ---------------------------------------------------------------- A NAME A GARDEN GAVE, AND ONE IT DID NOT
put("beans/postfix.md", thing("postfix", "postfix"))
out = gate()
check("an identifier someone else assigned, written as they assigned it, passes", ok(out), out[-500:])
put("beans/postfix.md", thing("postfix", f"{GID}/postfix"))
out = gate()
check("...and is never qualified: a garden's id before it is refused, as not this garden's to qualify",
      "is not a name a garden gave" in out and "not this garden's to qualify" in out, out[-500:])
put("beans/postfix.md", thing("postfix", f"{GID}/nothing-known:postfix"))
out = gate()
check("...a remainder whose `<kind>` is no kind the garden knows is not a name a garden gave",
      "is not a name a garden gave" in out, out[-500:])
put("beans/postfix.md", thing("postfix", f"{GID}/program:postfix"))
out = gate()
check("a name this garden minted, `<kind>:<name>`, may be qualified by its id", ok(out), out[-500:])
drop("beans/postfix.md")

# ---------------------------------------------------------------- A GARDEN'S OWN RECORD OF ANOTHER
out = (put("beans/ali.md", person("ali", 'test: "a rehearsal"\n')), gate())[1]
check("`test` on a person is refused: only a garden bean carries it",
      "ali: test is carried only by a bean of kind garden" in out, out[-500:])
put("beans/ali.md", person("ali"))


def garden_bean(gid, extra=""):
    return (f'---\nbean: garden-b\nkind: garden\ntitle: "the garden ben keeps"\nstatus: active\nsummary: "another garden"\n'
            f'nature: metaphysical\nowned_by: {{ legal: {{ owner: {{ bean: ben }} }} }}\nresponsibility: {{ legal: {{ holder: {{ bean: ben }} }} }}\n'
            f'identity: {{ status: confirmed, anchors: [ {{ key: garden_id, value: "{gid}", class: logical, establishing: true }} ] }}\n'
            f'provenance: {{ src: asserted-by-human, by: sam, as_of: 2026-09-01 }}\n{extra}---\nben\'s garden.\n')


put("beans/ben.md", person("ben"))
put("beans/garden-b.md", garden_bean("0123456789ab", 'test: "a rehearsal of ben\'s household"\n'))
out = gate()
check("...and on the `garden` bean for another garden it passes: the receiver's own record that it is a rehearsal", ok(out), out[-500:])
put("beans/garden-b.md", garden_bean(GID))
out = gate()
check("a `garden` bean anchored by this garden's own id is refused — a clone is the same garden",
      "a `garden` bean anchored by this garden's own id" in out, out[-500:])
drop("beans/garden-b.md"); drop("beans/ben.md")

# ---------------------------------------------------------------- ONE ENTRY PER PARTY
out = tx(paid="[ { party: sam, amount: { count: 400, unit: XTS } }, { party: sam, amount: { count: 500, unit: XTS } } ]")
check("two payers named sam in one transaction are refused: one entry per party (keyed_by)",
      "paid_by holds two entries for party 'sam'" in out, out[-500:])
out = tx(borne="[ { party: ali, share: 1 }, { party: ali, share: 2 } ]")
check("...and so are two bearers named ali", "borne_by holds two entries for party 'ali'" in out, out[-500:])
out = tx(borne="[ { party: ali, share: 2 }, { party: sam, share: 1 } ]")
check("...while bearers in any order pass", ok(out), out[-500:])

# ---------------------------------------------------------------- A NUMBER IS WHAT WAS WRITTEN
for spelling, what in (("010", "eight, in octal"), ("0x64", "a hundred, in hex"), ("1:30", "ninety, in base sixty"),
                       ("0b11", "three, in binary"), ("1_000", "a thousand, with an underscore")):
    out = tx(amount="{ count: %s, unit: XTS }" % spelling)
    check(f"a count written `{spelling}` — {what} to YAML 1.1 — is refused by name, never read as a number nobody wrote",
          f"amount.count '{spelling}' must be a whole number" in out, out[-500:])
for spelling, what in (("!!int 010", "eight"), ("!!int 0x64", "a hundred"), ("!!int 1:30", "ninety"),
                       ('!!int "1_000"', "a thousand, though quoted")):
    out = tx(amount="{ count: %s, unit: XTS }" % spelling)
    check(f"a count tagged `{spelling}` — {what} to YAML 1.1's constructor — is refused by name: the tag asks the same "
          f"question as the untagged text", "amount.count '%s' must be a whole number" % spelling.split()[1].strip('"') in out, out[-500:])
out = tx(amount="{ count: !!int 900, unit: XTS }")
check("...while `!!int 900`, plain decimal, is nine hundred and passes", ok(out), out[-500:])
sys.path.insert(0, os.path.join(ROOT, "bin"))
import dmparse
_tagged = 'a: !!int 010\nb: !!int 12\nc: !!int 0x2\nd: !!int "12\\n"\n'
check("dmparse reads `!!int 010` as the text written, and `!!int 12` as twelve — and a quoted \"12\\n\" is not twelve",
      dmparse.loads(_tagged) == {"a": "010", "b": 12, "c": "0x2", "d": "12\n"}, dmparse.loads(_tagged))
out = tx(amount='{ count: "%s", unit: XTS }' % ("9" * 41))
check("a count of forty-one digits is refused: past what every reader holds exactly", "amount.count '99999" in out
      and "at most forty digits" in out, out[-500:])
out = tx(amount='{ count: %s, unit: XTS }' % ("9" * 41))
check("...written bare as an integer too", "amount.count 99999" in out and "at most forty digits" in out, out[-500:])
out = tx(amount='{ count: "%s", unit: XTS }' % ("9" * 40))
check("...and forty digits pass", ok(out), out[-500:])
out = tx(amount='{ count: "100\\n", unit: XTS }')
check("a count with a trailing newline is refused — `$` is the end of the value", "must be a whole number" in out, out[-500:])
for spelling in ("010", "0x10", '"%s"' % ("1" * 41), "!!int 0x2", "!!int 010"):
    out = tx(borne="[ { party: sam, share: %s }, { party: ali, share: 1 } ]" % spelling)
    check(f"a share written {spelling[:12]} is refused", "share '" in out and "is not in the form this term declares" in out, out[-500:])

# ---------------------------------------------------------------- A DAY ITS CALENDAR HAS
def due(d):
    return deal("clauses:\n  rent: { what: \"rent\", by: ali, to: sam, amount: { count: 100, unit: XTS }, due: %s, "
                "every: { of: time, in: persian-calendar, each: month } }\n" % d)


for d, why in (("'persian:1404-12-30'", "Esfand 1404 has twenty-nine days"), ("'2026-02-30'", "February has no thirtieth"),
               ("'julian:2026-02-29'", "2026 is no Julian leap year"), ("'coptic:1742-13-99'", "no Coptic month has 99 days"),
               ("'persian:9999-01-01'", "a year the Persian reckoning cannot reach")):
    out = due(d)
    check(f"due {d} is refused — {why}", f"due {d}" in out and "— a date is a day its calendar has" in out, out[-500:])
out = due("'persian:1404-12-30'")
check("...and the refusal names the day the position would silently have moved to", "persian:1405-01-01" in out, out[-500:])
for d in ("'persian:1404-12-29'", "'hebrew:5787-01-09'", "'2026-W53-1'", "2026-09-01"):
    out = due(d)
    check(f"due {d} — a day its calendar has — passes", ok(out), out[-500:])

def every(rec):
    return deal("clauses:\n  rent: { what: \"rent\", by: ali, to: sam, amount: { count: 100, unit: XTS }, due: 2026-09-01, "
                "every: { of: time, %s } }\n" % rec)


for rec, want, why in (("in: gregorian-civil, each: month, to: '2026-02-30'", "every.to '2026-02-30' is no day",
                        "a monthly clause ending on a thirtieth of February"),
                       ("in: persian-calendar, each: month, from: 'persian:1404-12-30'",
                        "every.from 'persian:1404-12-30' is no day of persian-calendar", "a monthly clause starting on a day Esfand 1404 lacks"),
                       ("in: gregorian-civil, each: month, to: 'persian:1404-12-29'",
                        "every.to 'persian:1404-12-29' is not a position in the form system 'gregorian-civil' writes",
                        "a Gregorian repetition ending on a Persian day"),
                       ("in: gregorian-civil, each: month, to: 'garbage'", "every.to 'garbage' is not a position in the form",
                        "a repetition ending on no position at all")):
    out = every(rec)
    check(f"{why} is refused — where a repetition starts and ends is a position like any other",
          want in out, out[-500:])
out = every("in: persian-calendar, each: month, from: 'persian:1404-12-29', to: 'persian:1405-12-29'")
check("...while one that starts and ends on days its calendar has passes", ok(out), out[-500:])

# ---------------------------------------------------------------- THE PARTS OF A WHOLE, AND WHAT A REFUSAL SAYS
out = tx(paid="[ sam ]")
check("a sole payer written as a bare name is refused as an entry, not a traceback",
      "paid_by[t/0] must be a mapping" in out and "Traceback" not in out, out[-500:])
out = tx(amount='{ count: "300.00", unit: XTS }',
         paid="[ { party: sam, amount: { count: 100, unit: XTS } }, { party: ali, amount: { count: 150, unit: XTS } } ]")
check("parts that do not add up are refused, and the refusal says both amounts",
      "paid_by adds up to 250 XTS, and amount is 300 XTS" in out, out[-500:])
out = deal("transactions:\n  t: { what: \"a thing\", amount: { count: 900, unit: XTS }, paid_by: [ { party: sam } ], "
           "borne_by: [ { party: sam, share: 2 }, { party: bo, share: 1 } ] }\n",
           parties='  sam: { who: { bean: sam } }\n  yes: { external: "Bo" }\n')
check("a key YAML reads as a boolean beside a party that is missing is refused, not crashed on",
      "is no key of `parties`" in out and "key parties.True is not text" in out and "Traceback" not in out, out[-600:])
put("beans/deal.md", open(os.path.join(G, "beans", "deal.md"), encoding="utf-8").read()
    .replace("owned_by: { legal: { crown: logos } }", "owned_by: { legal: { crown: logos }, 1: { crown: logos } }"))
out = gate()
check("a facet key YAML reads as a number is refused as a key, not crashed on in sorting the facets",
      "key owned_by.1 is not text" in out and "Traceback" not in out, out[-600:])
drop("beans/deal.md")
put("beans/ali.md", person("ali", 'details: { 2026: "moved to the new flat" }\n'))
out = gate()
check("...and a year written as a key of `details` is refused as a key, not crashed on",
      "key details.2026 is not text" in out and "Traceback" not in out, out[-600:])
put("beans/ali.md", person("ali"))

# ---------------------------------------------------------------- THE FACETS HAVE ONE ROOT
VOCAB = open(os.path.join(G, "VOCAB.md"), encoding="utf-8").read()
put("VOCAB.md", VOCAB.replace("local_kinds: []", 'local_kinds: []\nregistry_additions: { facets: [ { facet: rogue, depends_on: [], meaning: "x" } ] }\n'
                              'vacancies: [ { at: "registry:facets", position: rogue, reason: prediction, why: "x" } ]', 1))
out = gate()
check("a facet that depends on nothing is a second root, and is refused", "2 rows name no `depends_on` (legal, rogue)" in out, out[-500:])
put("VOCAB.md", VOCAB.replace("local_kinds: []", 'local_kinds: []\nregistry_additions: { facets: [ { facet: moral, depends_on: [technical], meaning: "x" } ] }\n'
                              'vacancies: [ { at: "registry:facets", position: moral, reason: prediction, why: "x" } ]', 1))
out = gate()
check("...and one that reaches `legal` through another passes", ok(out), out[-500:])
put("VOCAB.md", VOCAB)

# ---------------------------------------------------------------- THE JOURNAL, AND WHAT A REFUSAL TELLS A PERSON TO RUN
def commit_with(bean_text, body):
    put("beans/ali.md", bean_text)
    j = run(sys.executable, os.path.join(G, "bin", "dmjournal.py"), "sam", "ali again", "--body", body, cwd=G)
    run("git", "add", "-A", cwd=G)
    c = run("git", "commit", "-q", "-m", "ali again", cwd=G)
    out = c.stdout + c.stderr
    if c.returncode != 0:
        run("git", "reset", "-q", "--hard", cwd=G)
    return c.returncode, out, j


run("git", "add", "-A", cwd=G)
run(sys.executable, os.path.join(G, "bin", "dmjournal.py"), "sam", "ali", "--body", "- action: added [[ali]].", cwd=G)
run("git", "add", "-A", cwd=G)
c = run("git", "commit", "-q", "-m", "ali", cwd=G)
check("(setup) ali is committed through the gate", c.returncode == 0, c.stdout + c.stderr)
for ch, name in (("\x1c", "a file separator"), ("\u2028", "a Unicode line separator"), ("\x0b", "a vertical tab"),
                 ("\r", "a carriage return in the middle of a line")):
    rc, out, _j = commit_with(person("ali").replace("ali.\n", f"ali, {len(name)}.\n"),
                              f"- action: changed [[ali]].{ch}## 2026-09-23 07:00+03:00 · sam · a heading nobody wrote{ch}- sam: x")
    check(f"a journal line holding {name} before a typed heading is refused at commit",
          rc != 0 and "log/journal.md: an added line holds" in out, out[-600:])
rc, out, _j = commit_with(person("ali").replace("ali.\n", "ali, once more.\n"), "- action: changed [[ali]] once more.")
check("...while an ordinary entry commits", rc == 0, out[-600:])
put("beans/ali.md", person("ali").replace("ali.\n", "ali, typed.\n"))
with open(os.path.join(G, "log", "journal.md"), "a", encoding="utf-8", newline="\n") as fh:
    fh.write("\n## 2026-09-23 07:00+03:00 · sam · typed\n- action: changed [[ali]].\n")
run("git", "add", "-A", cwd=G)
c = run("git", "commit", "-q", "-m", "typed", cwd=G)
out = c.stdout + c.stderr
_py = 'python' if os.name == 'nt' else 'python3'
check("a typed heading is refused with the command that works in every shell: `--body`, never `< entry.md`",
      c.returncode != 0 and "was not written by bin/dmjournal.py" in out
      and f'{_py} bin/dmjournal.py "<who>" "<what>" --body "' in out and "< entry.md" not in out, out[-600:])
run("git", "reset", "-q", "--hard", cwd=G)
put("beans/ali.md", person("ali").replace("ali.\n", "ali, unjournalled.\n"))
run("git", "add", "-A", cwd=G)
c = run("git", "commit", "-q", "-m", "no entry", cwd=G)
out = c.stdout + c.stderr
check("a bean staged with no journal entry is told to run the tool, not to type a date",
      c.returncode != 0 and "--body" in out and "date '+%Y" not in out, out[-600:])
run("git", "reset", "-q", "--hard", cwd=G)

out = deal("", parties="  sam: { who: { bean: sam } }\n  bob: { who: { bean: bob } }\n")
check("a party naming no bean says what to write: the bean first, or in the same commit",
      "parties -> bean 'bob' does not exist (dangling) — write beans/bob.md first, or in the same commit" in out, out[-500:])
drop("beans/deal.md")
put("beans/statement.md", '---\nbean: statement\nkind: document\ntitle: "a statement"\nstatus: active\nsummary: "a statement"\n'
    'nature: metaphysical\nowned_by: { legal: { owner: { bean: sam } } }\nresponsibility: { legal: { holder: { bean: sam } } }\n'
    'identity: { status: confirmed, anchors: [ { key: doc_id, value: "document:statement", class: logical, establishing: true } ] }\n'
    'provenance: { src: asserted-by-human, by: sam, as_of: 2026-09-01 }\n'
    'located_at: [ { system: windows-filesystem, openness: here, at: "laptop:C:/Users/ali/statement.pdf" } ]\n---\nA statement.\n')
out = gate()
check("a Windows path in the wrong form is refused with the pattern as the law writes it, and the form in words",
      "is not in the one canonical form 'windows-filesystem' declares" in out and ":[A-Za-z]:\\\\.*)$:" in out
      and "\\\\\\\\" not in out and "<host>:<Drive>:" in out, out[-600:])
put("beans/statement.md", open(os.path.join(G, "beans", "statement.md"), encoding="utf-8").read()
    .replace('"laptop:C:/Users/ali/statement.pdf"', "'laptop:C:\\Users\\ali\\statement.pdf'"))
out = gate()
check("...and the form it asks for passes, single-quoted", ok(out), out[-500:])
drop("beans/statement.md")

# ---------------------------------------------------------------- WHAT IS REFUSED IS LISTED: dmrules says every rule above
r = run(sys.executable, os.path.join(G, "bin", "dmrules.py"), cwd=G)
rules = r.stdout
check("dmrules shows what a minted name is — the form, the kinds, the qualified pattern — not 'no rule to check'",
      r.returncode == 0 and "minted:" in rules and "^[a-z][a-z0-9-]*:.+$" in rules
      and re.search(r"(?m)^  person_id +\[tier0\]  anchor term, MINTED", rules), rules[:600])
check("...the sums, one entry per party, and a key of the parties",
      "sums: each entry's paid_by.amount add up EXACTLY" in rules and "ONE per `party`" in rules
      and "is a key of `parties`" in rules, [l for l in rules.splitlines() if "transactions" in l or "paid_by" in l][:4])
check("...a count's form and each quantity's units, and the digits a currency is written in",
      re.search(r"(?m)^  count: \^", rules) and "decimal places" in rules and re.search(r"(?m)^  ratio +units", rules), rules[-1500:])
check("...and the manifest, the retired names and the provenance record, each in a section of its own",
      all(h in rules for h in ("MANIFEST — GARDEN.md, judged as itself", "RETIRED — names the law took back",
                               "PROVENANCE RECORD — on a bean, an anchor or an entry")) and "seeds_from" in rules
      and "carried ONLY on kinds ['garden']" in rules, rules[-900:])

check("NOTHING above ended in a traceback: every case is a refusal or a pass", not TRACES, TRACES[:2])
shutil.rmtree(T, ignore_errors=True)
print("\nrefusals: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
