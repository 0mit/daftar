#!/usr/bin/env python3
"""expiry — a term declares which of its dates runs out, and the tool reads the LAW to find them.

WHY THIS EXISTS. `bin/dmstale.py` named `registration` and `expires` in its own source. That was never
decided: the term was born in one garden's local vocabulary and the tool was extended for it the same
day, and when the term was PROMOTED to Tier-0 nobody came back. A cold-start drill found the cost in
fifteen minutes — a stranger declared its own `rental` term for a rented server, the GATE enforced its
date exactly (refusing "early October", refusing a missing attr, citing the garden's own VOCAB as the
authority), and dmstale said nothing at all about a renewal thirteen days away. First-class to the gate,
invisible to the tool. Its verdict turned on it: "the best feature in the system only works on facts the
maintainers anticipated."

So this asserts the two halves that must both hold:
  +  a GARDEN'S OWN term with `schema.expiry` is warned about, exactly as Tier-0's registration is
  -  a term WITHOUT the declaration is never warned about, however many iso_date attrs it carries —
     nine of the ten dates in the standard are `observed` or `as_of`, and a tool that warned about all
     of them would be wrong nine times in ten
"""
import os, re, sys, subprocess, tempfile, shutil, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS = []

def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:600]))
    if not cond:
        FAILS.append(name)

def run(*a, cwd=None):
    return subprocess.run(list(a), capture_output=True, text=True, cwd=cwd)

T = tempfile.mkdtemp(prefix="dmexp-")
G = os.path.join(T, "g")
run("sh", os.path.join(ROOT, "seed", "germinate.sh"), G, cwd=ROOT)

def stale(*args):
    return run(sys.executable, os.path.join(G, "bin", "dmstale.py"), *args, cwd=G).stdout

OWN = ('owned_by: { legal: { owner: { bean: keeper } } }\n'
       'responsibility: { legal: { holder: { bean: keeper } } }\n')
open(os.path.join(G, "beans", "keeper.md"), "w").write(
    '---\nbean: keeper\nkind: person\ntitle: "the keeper"\nstatus: active\nsummary: "p"\nnature: living\n'
    'identity: { status: confirmed, anchors: [ { key: person_id, value: "person:keeper", class: logical, '
    'establishing: true } ] }\n'
    'provenance: { src: asserted-by-human, by: t, as_of: 2026-01-01 }\n'
    'owned_by: { legal: { crown: love } }\nresponsibility: { legal: { self: true } }\n---\nA person.\n')

# ---- a GARDEN'S OWN term, the drill's case, reproduced -------------------------------------------------
# Declared in local_terms with an expiry, exactly as a stranger would write it after reading
# `schema_language` — no release, no code, no Tier-0 involvement.
SOON = (datetime.date.today() + datetime.timedelta(days=13)).isoformat()
FAR  = (datetime.date.today() + datetime.timedelta(days=900)).isoformat()

def vocab(term_yaml):
    v = os.path.join(G, "VOCAB.md")
    s = open(v, encoding="utf-8").read()
    # the template's line carries a trailing comment, so match the KEY and replace the whole line
    s = re.sub(r'^local_terms: \[\].*$', 'local_terms:\n' + term_yaml.rstrip('\n'), s, count=1, flags=re.M)
    assert 'local_terms:\n' in s, "VOCAB.md template no longer holds `local_terms: []`"

    open(v, "w", encoding="utf-8").write(s)

RENTAL = """  - term: rental
    meaning: "what a rented machine costs and when it next charges"
    context_keys: ["rental"]
    schema:
      shape: mapping
      required_attrs: [provider, renews]
      attr_types: { renews: iso_date }
      attr_extents: [period]
      expiry:
        attr: renews
        notice: { of: time, measure: { count: 30, unit: day } }
        why: "a rental that lapses takes the machine with it"
    merge: { cardinality: single, order: none }
"""
vocab(RENTAL)

def host(rental_block, bean="vps"):
    open(os.path.join(G, "beans", f"{bean}.md"), "w").write(
        f'---\nbean: {bean}\nkind: host\ntitle: "a rented machine"\nstatus: active\nsummary: "s"\n'
        'nature: physical\n'
        'identity: { status: confirmed, anchors: [ { key: fqdn, value: "' + bean + '.example.org", '
        'class: logical, establishing: true } ] }\n'
        'provenance: { src: observed, by: t, as_of: 2026-01-01 }\n' + OWN + rental_block +
        f'---\nA machine.\n')

host(f'rental: {{ provider: "someone", renews: "{SOON}" }}\n')
out = stale()
check("a GARDEN'S OWN term with an expiry is warned about — no release, no code",
      "EXPIRING" in out and "vps.rental" in out and "renews " + SOON in out, out[-700:])
check("...and the warning carries the CONSEQUENCE the term declared, not just a date",
      "a rental that lapses takes the machine with it" in out, out[-700:])

# The term's own horizon governs: 13 days is inside rental's 30 and would be inside a domain's 90 too,
# so push it out to a date only the term's own horizon could judge.
host(f'rental: {{ provider: "someone", renews: "{FAR}" }}\n')
check("a date beyond the TERM's own horizon is quiet", "EXPIRING" not in stale(), stale()[-400:])
check("...and --days overrides every term's horizon at once",
      "EXPIRING" in stale("--days", "1000") and "overriding every term" in stale("--days", "1000"),
      stale("--days", "1000")[-500:])

# ---- the negative half: silence is not free, it is DECLARED --------------------------------------------
# Take the SAME term and delete only its two `expiry:` lines — nothing else moves, so the difference
# between warned-about and silent is exactly the declaration and cannot be anything else.
v = os.path.join(G, "VOCAB.md")
_s = open(v, encoding="utf-8").read()
_DECL = ('      expiry:\n        attr: renews\n        notice: { of: time, measure: { count: 30, unit: day } }\n        why: "a rental that lapses takes the machine with it"\n')
assert _DECL in _s, "the expiry declaration was not where this test put it"
open(v, "w", encoding="utf-8").write(_s.replace(_DECL, ""))
host(f'rental: {{ provider: "someone", renews: "{SOON}" }}\n')
out = stale()
check("a term WITHOUT the declaration is never warned about, though its date is an enforced iso_date",
      "vps.rental" not in out, out[-500:])
check("...and the gate still enforces that date, so the silence is the TOOL's, not a gap in the law",
      "0 error" in run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G).stdout,
      "gate should pass")

# ---- and the standard's own dates stay quiet, which is why this is not inferred from iso_date ----------
import yaml
sys.path.insert(0, os.path.join(G, "bin"))
import dmparse
sv = yaml.safe_load(dmparse.read(os.path.join(G, "seed", "std-vocab.md"))[0])
terms = list(sv["terms"]) + [x for p in sv["profiles"].values() for x in p["terms"]]
dated, declared = [], []
for t_ in terms:
    s = (t_.get("schema") or {})
    if [k for k, v in list((s.get("attr_types") or {}).items())
        + list((s.get("entry_types") or {}).items()) if v == "iso_date"]:
        dated.append(t_["term"])
    if (s.get("expiry") or {}).get("attr"):
        declared.append(t_["term"])
check("the standard carries many dates and declares few expiries — the reason nothing is inferred",
      len(dated) > len(declared) and declared, f"dated={sorted(dated)} declared={sorted(declared)}")

# ---- EXTENT: the region `figures` declared possible, and every rule read from the aspect ---------------
# Each negative below is refused for a reason the ASPECT gives, not one written into the gate — which is
# the whole claim. A new aspect gets regions with no code change; an aspect that should not have them
# refuses them in its own words.
def period(block, bean="vps2"):
    open(os.path.join(G, "beans", f"{bean}.md"), "w").write(
        f'---\nbean: {bean}\nkind: host\ntitle: "a rented machine"\nstatus: active\nsummary: "s"\n'
        'nature: physical\n'
        'identity: { status: confirmed, anchors: [ { key: fqdn, value: "' + bean + '.example.org", '
        'class: logical, establishing: true } ] }\n'
        'provenance: { src: observed, by: t, as_of: 2026-01-01 }\n' + OWN +
        f'rental: {{ provider: "someone", renews: "{FAR}", period: {block} }}\n'
        '---\nA machine.\n')
    return run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G).stdout

# put the declaration back for this half
_s = open(v, encoding="utf-8").read()
if "expiry:" not in _s:
    open(v, "w", encoding="utf-8").write(_s.replace("      attr_extents: [period]\n",
                                                    "      attr_extents: [period]\n" + _DECL))

check("a LENGTH with no fixed ends is a region — 'for N days', which most real durations are",
      "0 error" in period('{ of: time, measure: { count: 204, unit: day } }'),
      period('{ of: time, measure: { count: 204, unit: day } }')[-400:])
check("...and so is a region bounded at both ends",
      "0 error" in period('{ of: time, from: "2026-01-01", to: "2026-03-31" }'),
      period('{ of: time, from: "2026-01-01", to: "2026-03-31" }')[-400:])
check("...and one open at an end",
      "0 error" in period('{ of: time, from: "2026-01-01" }'),
      period('{ of: time, from: "2026-01-01" }')[-400:])

out = period('{ of: time }')
check("a region with neither bound and no length is refused", "at least one of from / to / measure" in out,
      out[-400:])
out = period('{ of: necessity, measure: { count: 3, unit: day } }')
check("a region on an OPPOSITION is refused IN THE FIGURE'S OWN WORDS — modalities have no between",
      "carries no region" in out and "modalities" in out, out[-400:])
out = period('{ of: walk, measure: { count: 3, unit: day } }')
check("a length on an UNMETERED aspect is refused — a stretch of a walk has no duration",
      "metered: none" in out, out[-400:])
out = period('{ of: time, measure: { count: 1, unit: month } }')
check("a unit the registry does not hold is refused — a month is 28 to 31 days and is not a measure",
      "not in the `units` registry" in out, out[-400:])
out = period('{ of: time, measure: { count: 0, unit: day } }')
check("a non-positive count is refused", "positive whole number" in out, out[-400:])
out = period('{ of: time, from: "early October" }')
check("a boundary that is no position in the aspect's domain is refused",
      "is not a position in any system" in out, out[-400:])
out = period('{ of: teleportation, measure: { count: 1, unit: day } }')
check("an aspect that does not exist is refused, and the message lists the ones that do",
      "names no aspect" in out, out[-400:])

# ---- and the LAW's own extents are judged by the same rule -------------------------------------------
# Put a VALID region back first: the last negative left a broken bean, and an error from it would mask
# the one this check is about — a test that passes on the wrong error has proved nothing.
period('{ of: time, measure: { count: 204, unit: day } }')
# The garden's OWN term is the right target: this garden does not opt into the `domain` profile, so
# Tier-0's `registration` is not in force here — and a check that fired only on the standard would miss
# exactly the case this release is for, which is a garden writing its own rule.
_v = open(v, encoding="utf-8").read()
open(v, "w", encoding="utf-8").write(
    _v.replace("notice: { of: time, measure: { count: 30, unit: day } }",
               "notice: { of: time, measure: { count: 30, unit: fortnight } }", 1))
out = run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G).stdout
check("an extent the LAW ITSELF writes is checked — a rule the gate cannot see is the defect, not the fix",
      "VOCAB rental.schema.expiry.notice" in out and "units` registry" in out, out[-500:])
open(v, "w", encoding="utf-8").write(_v)

shutil.rmtree(T, ignore_errors=True)
print("\nexpiry: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
