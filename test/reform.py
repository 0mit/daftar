#!/usr/bin/env python3
"""The law's own spelling (std-vocab 13.0): one record per attribute, and a translator that proves itself.

Grows a garden and checks that: the COOKBOOK's recipe for a new term works as written; an attribute with no
domain is refused; a garden's overlay merges per attribute; the OLD spelling is refused by name with the way
out; `bin/dmreform.py` translates it, keeps every comment, and refuses rather than guesses; and
`bin/dmupgrade.py` runs the translation for a garden crossing 13.0.
"""
import os, re, sys, subprocess, tempfile, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS = []

def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:700]))
    if not cond:
        FAILS.append(name)

def run(*a, cwd=None):
    return subprocess.run(list(a), capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd)

T = tempfile.mkdtemp(prefix="dmreform-")
G = os.path.join(T, "g")
r = run("sh", os.path.join(ROOT, "seed", "germinate.sh"), G, "--gardener", "keeper", cwd=ROOT)
check("a garden germinates", r.returncode == 0, r.stdout + r.stderr)
VOC, STD = os.path.join(G, "VOCAB.md"), os.path.join(G, "seed", "std-vocab.md")
VOC0 = open(VOC).read()

def gate():
    r = run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G)
    return r.stdout + r.stderr

def vocab(local_terms_yaml):
    assert VOC0.count("local_terms: []") == 1
    open(VOC, "w").write(VOC0.replace("local_terms: []", local_terms_yaml.rstrip("\n")))

BEAN = os.path.join(G, "beans", "rented-box.md")
def bean(extra):
    open(BEAN, "w").write("""---
bean: rented-box
genos: host
title: "a rented machine"
status: active
summary: "probe"
nature: soma
identity:
  status: confirmed
  anchors:
    - { key: serial, value: "SN-RENT-1", class: hardware, establishing: true }
provenance: { src: observed, by: probe, as_of: 2026-09-20 }
owned_by: { legal: { external: "a provider" } }
responsibility: { legal: { external: "a provider" } }
""" + extra + "---\n\nprobe.\n")

# ---------------------------------------------------------------- the cookbook's recipe, as written
RECIPE = re.search(r'<!-- example-term: VOCAB\.md -->\n```yaml\n(.*?)\n```', open(os.path.join(ROOT, "seed", "COOKBOOK.md")).read(), re.S).group(1)
vocab(RECIPE)
bean('rental: { provider: "a hosting company", renews: 2027-01-15 }\n')
out = gate()
check("the COOKBOOK's new-term recipe works as written, with no code anywhere", "0 error" in out, out[-900:])
bean('rental: { provider: "x", renews: "next January" }\n')
out = gate()
check("...and the term BITES: a date that is not a date is refused", "rental" in out and "renews" in out and "0 error" not in out, out[-600:])
bean('rental: { provider: "x", renews: 2027-01-15, it_is_quite_expensive_really: "a sentence as a key" }\n')
out = gate()
check("...and so is an attribute the term does not declare", "carries `it_is_quite_expensive_really`" in out, out[-600:])
bean('rental: { renews: 2027-01-15 }\n')
out = gate()
check("...and a missing required attribute, named as the attribute it is",
      "rental requires 'provider' (VOCAB rental.schema.attrs.provider: required)" in out, out[-600:])

# ---------------------------------------------------------------- a value added to a term that READS A REGISTRY
ROW = 'registry_additions:\n  operating_systems:\n    - { os: probe-os, family: unix, path_grammar: unix-filesystem, meaning: "a probe" }'
def vocab_tail(local_terms_yaml, tail=""):
    vocab(local_terms_yaml + ("\n" + tail if tail else ""))
vocab_tail("local_terms: []", ROW); bean("os: probe-os\n"); out = gate()
check("a registry-fed term takes a new value as a ROW of its registry, and nothing else is needed", "0 error" in out, out[-700:])
bean(""); out = gate()
check("...and the garden ACCOUNTS for the row it added: unused, it is refused like any position nobody occupies",
      "os.values: position 'probe-os' is declared but NO bean occupies it" in out, out[-700:])
vocab_tail("local_terms:\n  - term: os\n    schema: { values_add: [probe-os] }"); bean("os: probe-os\n"); out = gate()
check("`values_add` on such a term adds nothing — the term holds no list of its own — and the refusal says what it needs instead",
      "os 'probe-os' not in" in out and "registry_additions: { operating_systems: [...] }" in out and "values_add" not in out, out[-900:])

# ---------------------------------------------------------------- every attribute says what it is a position IN
bean('rental: { provider: "x", renews: 2027-01-15 }\n')
vocab(RECIPE.replace("note:     { in: prose,", "note:     {"))
out = gate()
check("an attribute that states no `in:` is refused — an oversight and a decision must not look alike",
      "attribute `note` states no domain" in out, out[-600:])
vocab(RECIPE.replace("in: prose,              meaning: \"who", "in: telepathy,          meaning: \"who"))
out = gate()
check("...and so is a domain the language does not offer", "attribute `provider` states no domain" in out, out[-600:])

# ---------------------------------------------------------------- a garden's overlay merges PER ATTRIBUTE
vocab("""local_terms:
  - term: risks
    schema:
      attrs:
        remedy: { in: prose, meaning: "what would settle it, and whose move it is" }
""")
bean('''risks:
  rent-lapses:
    what: "w"
    consequence: "c"
    severity: low
    state: latent
    evidence: "e"
    remedy: "pay it"
''')
out = gate()
check("a garden adds ONE attribute to a standard term without restating the rest", "0 error" in out, out[-900:])
bean('''risks:
  rent-lapses:
    what: "w"
    severity: enormous
    state: latent
    evidence: "e"
    remedy: "pay it"
''')
out = gate()
check("...and the standard's own attributes still bite under the overlay",
      "missing ['consequence']" in out and "'enormous' not in" in out, out[-900:])
os.remove(BEAN)

# ---------------------------------------------------------------- the OLD spelling: refused by name, translated by tool
OLD = """local_terms:
  - term: rental
    meaning: "what a rented machine is rented from"
    context_keys: [rental]
    schema:
      shape: open_map_of_entries
      key_form: kebab
      entry_required_attrs: [provider, renews]      # both, always: a rental with no date is a guess
      entry_values:
        billing: [monthly, yearly]
      entry_types: { renews: iso_date }
      # a provider is a being where one exists
      entry_ref_fields: [paid_by]
      on_aspect:
        - { aspect: capability, attr: permission, default: permitted }
      entry_required_if:
        - { attr: billing, equals: yearly, requires: [note] }
    entry_attrs:
      provider: "who it is rented from"
      renews:   "ABSOLUTE date the next payment is due"
      note:     "optional remark"
    merge: { cardinality: multi, order: by-key }
vacancies:
  - { at: rental.billing, position: monthly, reason: prediction, why: "probe" }
  - { at: rental.billing, position: yearly, reason: prediction, why: "probe" }
"""
assert VOC0.count("vacancies: []") <= 1
_v = VOC0.replace("vacancies: []\n", "") if "vacancies: []" in VOC0 else VOC0
open(VOC, "w").write(_v.replace("local_terms: []", OLD.rstrip("\n")))
out = gate()
check("the old spelling is refused BY NAME, and the refusal says how to get out",
      "schema key `entry_required_attrs` was RETIRED at std-vocab 13.0" in out and "bin/dmreform.py" in out, out[-900:])
r = run(sys.executable, os.path.join(G, "bin", "dmreform.py"), VOC, cwd=G)
new = open(VOC).read()
check("bin/dmreform.py translates the garden's own terms", r.returncode == 0 and "1 term(s) rewritten — rental" in r.stdout, r.stdout + r.stderr)
check("...into one record per attribute", 'renews:' in new and 'in: { type: iso_date }' in new
      and 'in: { aspect: capability, default: permitted }' in new and 'entry_attrs' not in new, new[-1500:])
check("...conditionals became cells", '{ when: { billing: yearly }, requires: [note] }' in new, new[-1200:])
check("...and NO COMMENT WAS LOST — the reasons travel with the law",
      "both, always: a rental with no date is a guess" in new and "a provider is a being where one exists" in new, new[-1500:])
out = gate()
check("the translated vocabulary passes the gate", "0 error" in out, out[-900:])
r = run(sys.executable, os.path.join(G, "bin", "dmreform.py"), "--check", VOC, cwd=G)
check("...and --check finds nothing left to translate", r.returncode == 0, r.stdout)
r = run(sys.executable, os.path.join(G, "bin", "dmreform.py"), VOC, cwd=G)
check("translating twice is a no-op, not a second rewrite", open(VOC).read() == new, r.stdout)

# a contradiction the translator must REFUSE rather than resolve by guessing
open(VOC, "w").write(_v.replace("local_terms: []", """local_terms:
  - term: rental
    meaning: "m"
    context_keys: [rental]
    schema:
      shape: open_map_of_entries
      key_form: kebab
      entry_required_attrs: [a, b]
      entry_types: { b: iso_date, a: iso_date }
    merge: { cardinality: multi, order: by-key }"""))
before = open(VOC).read()
r = run(sys.executable, os.path.join(G, "bin", "dmreform.py"), VOC, cwd=G)
check("two constructs that order the same attributes differently are REPORTED, and the file is left alone",
      r.returncode == 1 and "contradictory orders" in r.stdout and open(VOC).read() == before, r.stdout + r.stderr)

# ---------------------------------------------------------------- the standard itself
sys.path.insert(0, os.path.join(ROOT, "bin"))
import dmreform
check("the standard uses none of the constructs it retired", dmreform.uses_old_constructs(open(os.path.join(ROOT, "seed", "std-vocab.md")).read()) == [])

# ---------------------------------------------------------------- nothing a release SHIPS still reads the old spelling
# v0.22.0 shipped test/fast.py reading `entry_pattern` and `entry_ref_fields` an hour after 13.0 retired them: the
# move of "every reader" onto the form had looked only under bin/. One read made the commit hook refuse every
# garden with a cached analysis; the other came back EMPTY and silently weakened a check. So the guard covers
# everything `seed/LANGUAGE` ships, not a directory somebody remembered.
import fnmatch, io, tokenize
_pats = [l.strip() for l in open(os.path.join(ROOT, "seed", "LANGUAGE")) if l.strip() and not l.startswith("#")]
_shipped = [os.path.relpath(os.path.join(d, f), ROOT) for d, _ds, fs in os.walk(ROOT) if ".git" not in d for f in fs]
_shipped = [f for f in _shipped if f.endswith(".py") and any(fnmatch.fnmatch(f, p) for p in _pats)]
_KNOWS_THE_OLD_SPELLING = {os.path.join("bin", "dmreform.py")}      # the translator, and only the translator
_RETIRED = set(dmreform.OLD_SCHEMA_KEYS) | {"entry_attrs"}
_gate_src = open(os.path.join(ROOT, "bin", "dmcheck.py"), encoding="utf-8").read().split("\n")
_lo = next(i for i, l in enumerate(_gate_src, 1) if l.startswith("RETIRED_CONSTRUCTS = ("))
_hi = next(i for i, l in enumerate(_gate_src, 1) if i >= _lo and l.rstrip().endswith(")"))
_hits = []
for f in sorted(set(_shipped) - _KNOWS_THE_OLD_SPELLING):
    for tok in tokenize.generate_tokens(io.StringIO(open(os.path.join(ROOT, f), encoding="utf-8").read()).readline):
        if tok.type == tokenize.STRING and tok.string.strip("'\"") in _RETIRED:
            # the gate NAMES the retired constructs, once, in the tuple it refuses them by; that is not a read
            if f == os.path.join("bin", "dmcheck.py") and _lo <= tok.start[0] <= _hi:
                continue
            # ONE LEFTOVER, NAMED RATHER THAN HIDDEN: `alt_form: { key, ref_fields }` kept its sub-key's old name at
            # 13.0, because `alt_form` itself was not rewritten. It is a sub-key of a living construct, not a
            # retired one; renaming it is a spelling change of its own.
            if f == os.path.join("bin", "dmform.py") and tok.string.strip("'\"") == "ref_fields" and "alt.get(" in tok.line:
                continue
            _hits.append(f"{f}:{tok.start[0]} {tok.string}")
check("no shipped program reads a retired construct — only the translator knows the old spelling",
      len(_shipped) > 10 and not _hits, f"{len(_shipped)} shipped; hits: {_hits[:8]}")

# and the hook's own suite runs green on a garden that HAS what it inspects: a codebase with a cached analysis
_vc = (VOC0.replace("extends_profiles: []", "extends_profiles: [code]") if "extends_profiles: []" in VOC0
       else VOC0.replace("extends_profiles: [", "extends_profiles: [code, ", 1) if "extends_profiles: [" in VOC0
       else VOC0.replace("\n---", "\nextends_profiles: [code]\n---", 1))
assert "extends_profiles: [code" in _vc, "the garden did not opt into the code profile"      # a no-op edit is a bug
open(VOC, "w").write(_vc)
open(os.path.join(G, "beans", "a-tool.md"), "w").write("""---
bean: a-tool
genos: codebase
title: "a tool"
status: active
summary: "probe"
nature: lekton
identity: { status: confirmed, anchors: [ { key: git_remote, value: "host-a:git/a-tool.git", class: logical, establishing: true } ] }
provenance: { src: observed, by: probe, as_of: 2026-09-20 }
owned_by: { legal: { external: "someone" } }
responsibility: { legal: { external: "someone" } }
code_paths:
  - { path: "root:a-tool", role: own-source, scan_policy: index }
analysis_cache:
  code-structure: { produced_by: probe, as_of: 2026-09-20, staleness_key: "a-tool@abc1234", policy: index, form: inline, covers_paths: ["root:a-tool"] }
---

probe.
""")
r = run(sys.executable, os.path.join(G, "test", "fast.py"), "-v", cwd=G)       # -v: the line of each check it passed
check("test/fast.py — which the commit hook runs — reads the staleness pattern from the law as it is now spelled",
      "PASS every cache entry carries a checkable staleness key" in r.stdout and "*** FAIL ***" not in r.stdout
      and "neither set is empty" in r.stdout, (r.stdout + r.stderr)[-900:])

shutil.rmtree(T, ignore_errors=True)
# ---------------------------------------------------------------- 18.0: a vacancy is addressed AT the registry
import dmreform as _R
_old = """---
extends: std-vocab@17.0
vacancies:
  - at: unit.values
    position: hour
    reason: prediction
    why: "nothing here is held to the hour yet"
  - { at: facets.values, position: financial, reason: prediction, why: "x" }
local_terms: []
---
"""
check("the detector sees a vacancy addressed at a retired owner term", ("vacancies", ["unit.values"]) in _R.uses_old_constructs(_old))
_new, _done = _R.rewrite_text(_old)
check("...and the translator re-addresses it at the registry, touching nothing else",
      'at: "registry:units"' in _new and "at: facets.values" in _new and "unit.values" not in _new and _done == ["vacancies"], _new)
check("...once: a translated overlay is left alone", _R.rewrite_text(_new)[0] == _new and not _R.uses_old_constructs(_new))

print("\nreform: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
