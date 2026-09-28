#!/usr/bin/env python3
"""Every profile with every other, and analytic accounting in the field's words (std-vocab 28.1).

Grows a garden that extends EVERY profile the law offers, keeps an analytic scheme of its own, and distributes a rent
across two plans. Checks that the law's profiles compose (and that a law whose profiles collide is refused, each way it
can collide); that a distribution is judged plan by plan; that an attribute a profile adds is refused, with the profile
named, in a garden that does not extend it; and that the reckoner reads where each amount belongs — exact, rolled up to
the plans, and in the currency's cents by the largest remainders.
"""
import os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:900]))
    if not cond:
        FAILS.append(name)


def run(*a, cwd=None):
    return subprocess.run(list(a), capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd)


sys.path.insert(0, os.path.join(ROOT, "bin"))
import dmparse  # noqa: E402
LAW_TEXT = open(os.path.join(ROOT, "seed", "std-vocab.md"), encoding="utf-8").read()
LAW = dmparse.loads(dmparse.split_front_matter(LAW_TEXT)[0])
PROFILES = list(LAW["profiles"])

T = tempfile.mkdtemp(prefix="dmprof-")
G = os.path.join(T, "g")
r = run("sh", os.path.join(ROOT, "seed", "germinate.sh"), G, "--gardener", "sam", cwd=ROOT)
check("a garden germinates", r.returncode == 0, r.stdout + r.stderr)
VOC = os.path.join(G, "VOCAB.md")
_voc = open(VOC).read()
EXTRA = """extends_profiles: [%s]
registry_additions:
  knowledge_schemes:
    - scheme: analytic
      classifies: where this garden's amounts belong
      holding: extract
      publisher: the gardener
      url: "file:extracts/analytic.tsv"
      levels: [ { level: plan }, { level: account } ]
      neighbours: none
      sources: extracts/analytic.tsv
registry_files:
  - { registry: analytic, file: extracts/analytic.tsv, key: code }
""" % ", ".join(PROFILES)
_h, _sep, _rest = _voc.partition("\n---\n")
open(VOC, "w").write(_h + "\n" + EXTRA.rstrip("\n") + _sep + _rest)
os.makedirs(os.path.join(G, "extracts"), exist_ok=True)
open(os.path.join(G, "extracts", "analytic.tsv"), "w").write(
    "code\tlevel\tparent\tname\nprojects\tplan\t\tProjects\ndepartments\tplan\t\tDepartments\n"
    "orchard\taccount\tprojects\torchard\nworkshop\taccount\tprojects\tworkshop\nbench\taccount\tprojects\tbench\n"
    "engineering\taccount\tdepartments\tEngineering\n")
open(os.path.join(G, "beans", "ali.md"), "w").write("""---
bean: ali
genos: person
title: "ali"
status: active
summary: "probe"
nature: empsychon
identity: { status: confirmed, anchors: [ { key: identifier, value: "person:ali", class: logical, establishing: true } ] }
provenance: { src: asserted-by-human, by: "sam", as_of: 2026-09-28 }
owned_by: { legal: { crown: agape } }
responsibility: { legal: { self: true } }
consent: { bean: server-rent }
---
a
""")
RENT = """---
bean: server-rent
genos: contract
title: "server-rent"
status: active
summary: "the server's rent, shared out"
nature: lekton
identity: { status: confirmed, anchors: [ { key: identifier, value: "contract:server-rent", class: logical, establishing: true } ] }
provenance: { src: asserted-by-human, by: "sam", as_of: 2026-09-28 }
owned_by: { legal: { crown: logos } }
responsibility: { legal: { parties: true } }
parties:
  sam: { who: { bean: sam }, accepted: 2026-09-01 }
  ali: { who: { bean: ali }, accepted: 2026-09-01 }
words: { form: spoken }
transactions:
  september:
    what: "the server's rent for September"
    amount: { count: "100.00", unit: TRY }
    day: 2026-09-01
    paid_by: [ { party: sam } ]
    analytic_distribution:
      - { code: analytic:orchard, share: 60 }
      - { code: analytic:workshop, share: 40 }
      - { code: analytic:engineering, share: 1 }
---
r
"""
BEAN = os.path.join(G, "beans", "server-rent.md")


def gate(old=None, new=None):
    assert old is None or old in RENT, old
    open(BEAN, "w").write(RENT if old is None else RENT.replace(old, new, 1))
    r = run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G)
    return r.stdout + r.stderr


out = gate()
check(f"a garden may extend every profile the law offers ({', '.join(PROFILES)}) and keep its accounts: 0 errors",
      " 0 error(s), 0 warning(s)" in out and len(PROFILES) >= 6, out[-900:])
check("...and its rules show the core term with what a profile adds to it",
      re.search(r"^  transactions +\[tier0\+profile:accounting\]", run(sys.executable, os.path.join(G, "bin", "dmrules.py"),
                                                                     cwd=G).stdout, re.M))

# ---- a distribution is judged plan by plan --------------------------------------------------------------------------------
TWO = ("      - { code: analytic:orchard, share: 60 }\n      - { code: analytic:workshop, share: 40 }\n")
out = gate(TWO, '      - { code: analytic:orchard, amount: { count: "70.00", unit: TRY } }\n'
                '      - { code: analytic:workshop, amount: { count: "30.00", unit: TRY } }\n')
check("a plan's parts may be amounts, which make the transaction's amount", " 0 error(s)" in out, out[-700:])
out = gate(TWO, '      - { code: analytic:orchard, amount: { count: "70.00", unit: TRY } }\n'
                '      - { code: analytic:workshop, amount: { count: "20.00", unit: TRY } }\n')
check("...and are refused, plan by plan, where they do not", "analytic_distribution in the plan projects adds up to 90 TRY, "
      "and amount is 100 TRY" in out, out[-700:])
out = gate(TWO, '      - { code: analytic:orchard, amount: { count: "70.00", unit: TRY } }\n'
                '      - { code: analytic:workshop, share: 40 }\n')
check("...a plan stated partly in amounts and partly in shares is no whole anyone can judge", "in the plan projects states "
      "`amount` for some of its parts and not for others" in out, out[-700:])
out = gate("code: analytic:engineering, share: 1 }", 'code: analytic:engineering, share: 1, amount: { count: "100.00", unit: TRY } }')
check("...an entry states its share or its amount, not both", "states `share` and `amount`" in out, out[-700:])
out = gate("code: analytic:engineering", "code: analytic:nowhere")
check("...and names an account the garden's scheme holds", "'nowhere' is not a code of analytic" in out, out[-700:])

# ---- a key a profile adds, where it is not extended ------------------------------------------------------------------------
gate()
_all = open(VOC).read()
open(VOC, "w").write(_all.replace("extends_profiles: [%s]" % ", ".join(PROFILES),
                                  "extends_profiles: [%s]" % ", ".join(p for p in PROFILES if p != "accounting")))
out = run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G)
out = out.stdout + out.stderr
check("a garden that does not extend `accounting` is told the profile adds `analytic_distribution`, and how to extend it",
      "carries `analytic_distribution`, which the profile `accounting` adds to `transactions`" in out and "--extend accounting" in out,
      out[-900:])
open(VOC, "w").write(_all)

# ---- the reckoner reads where each amount belongs ----------------------------------------------------------------------------
def reading(extra, name):
    p = os.path.join(T, name + ".yaml")
    open(p, "w").write('steps:\n  - { id: rent, op: select, entries: "transactions.*" }\n'
                       '  - { id: where, op: apportion, of: rent, amount: amount, over: analytic_distribution%s }\n' % extra)
    r = run(sys.executable, os.path.join(G, "bin", "dmreckon.py"), "--ad-hoc", p, cwd=G)
    return dict(re.findall(r"^  ([a-z-]+): (.*)$", r.stdout, re.M)), r.stdout + r.stderr
got, out = reading("", "per-account")
check("apportion reads each account's part exactly: 60 and 40 of the projects, the whole to engineering",
      got == {"orchard": "60 TRY", "workshop": "40 TRY", "engineering": "100 TRY"}, out[-600:])
got, out = reading(", level: plan", "per-plan")
check("...rolled up to the plans, each plan holds the whole", got == {"projects": "100 TRY", "departments": "100 TRY"}, out[-600:])
gate(TWO, "      - { code: analytic:orchard, share: 1 }\n      - { code: analytic:workshop, share: 1 }\n"
          "      - { code: analytic:bench, share: 1 }\n")
got, out = reading("", "thirds")
check("...a split that is no whole number of cents is kept exact", got.get("orchard") == "100/3 TRY", out[-600:])
got, out = reading(", digits: true", "thirds-cents")
check("...and written in the currency's cents, the cent left over going to the largest remainder, the first code first",
      (got.get("orchard"), got.get("workshop"), got.get("bench")) == ("33.34 TRY", "33.33 TRY", "33.33 TRY"), out[-600:])

# ---- a law whose profiles collide is refused, each way ---------------------------------------------------------------------
STD = os.path.join(G, "seed", "std-vocab.md")
law = open(STD).read()
def law_gate(mut, want, why):
    old, new = mut
    assert old in law, old
    open(STD, "w").write(law.replace(old, new, 1))
    r = run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G)
    out = r.stdout + r.stderr
    check("every profile composes with every other: " + why, want in out, [l for l in out.splitlines() if l.startswith("ERROR")][:4])
open(BEAN, "w").write(RENT)
law_gate(("    overlays:\n      - term: transactions\n", "    overlays:\n      - term: transactions\n        schema: { attrs: { amount: { in: prose } } }\n      - term: transactions\n"),
         "overlays[transactions]: `amount` is the core term's own attribute", "a profile that would rewrite a core attribute is refused")
law_gate(("    overlays:\n      - term: located_at\n", "    overlays:\n      - term: transactions\n        schema: { attrs: { analytic_distribution: { in: prose } } }\n      - term: located_at\n"),
         "`analytic_distribution` is also added by profile accounting", "two profiles adding one attribute to one term are refused")
law_gate(("    - term: git_remote\n", "    - term: transactions\n      meaning: \"x\"\n    - term: git_remote\n"),
         "its term `transactions` is named as a core term", "a profile term named as a core term is refused")
law_gate(("    overlays:\n      - term: transactions\n", "    overlays:\n      - term: nothing-here\n        schema: { attrs: { x: { in: prose } } }\n      - term: transactions\n"),
         "`nothing-here` is no term of the core", "an overlay of a term the core does not have is refused")
open(STD, "w").write(law)

shutil.rmtree(T, ignore_errors=True)
print("\nprofiles: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
