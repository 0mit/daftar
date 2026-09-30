#!/usr/bin/env python3
"""The flow law (24.0; the Leviathan's Body 3 and Leg 1): which passes between layers are granted, how far each row is
guarded, and what the gate judges by it at every commit — a value's pointer, the journal appended and never rewritten,
the law's front matter without a story, a person's words placed only by a person, and a session's pass log where a
commit claims one.

Holds every row of `flows` to a granted and a refused pass, found from the law itself; reads each tool's `GUARDS` and
finds its label in its proof; holds each row's guard to the last release's; and grows a garden and commits an invented
bookshop's lease through its hook.
"""
import json, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'bin'))
import dmpass, dmparse                                     # noqa: E402

PY = sys.executable
FAILS, RUN = [], [0]


def check(name, cond, detail=""):
    RUN[0] += 1
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:900]))
    if not cond:
        FAILS.append(name)


def run(*a, cwd=None):
    return subprocess.run(list(a), capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd)


# ==================================== THE LAW: each row, a granted and a refused pass ====================================
LAW = dmpass.origins(ROOT).law
F = dmpass.Flows(LAW, None)
check("the flow law reads: every row names known layers, methods and grants, and one cell has one row",
      F.rows and not F.problems(), F.problems())
LAYERS = sorted(k for k in F.layers if k)


def dest(t):
    return (dmpass.ESTATE, dict(t[1])) if isinstance(t, tuple) else t


def show(s, t, m):
    return f"{m} from {s} to {t if isinstance(t, str) else json.dumps(dict(t[1]))}"


def neighbour(cell, want):
    """The pass nearest `cell` — fewest of its source, method and keeper changed, the destination kept — that the law
    decides `want` (granted or not), with its Decision; None where there is none."""
    s, t, m, k = cell
    tried = sorted(((s2 != s) + (m2 != m) + (k2 != k), s2, m2, k2)
                   for s2 in LAYERS for m2 in F.methods for k2 in (None,) + dmpass.KEEPERS)
    for n, s2, m2, k2 in tried:
        d = F.decide(s2, dest(t), m2, k2)
        if n and d.granted == want:
            return (s2, t, m2), d
    return None


for r in F.rows:
    name, grant = r.get('flow'), r.get('grant')
    for cell in F.cells(r):
        s, t, m, k = cell
        d = F.decide(s, dest(t), m, k)
        if name not in d.rows or d.grant != grant:
            check(f"flows[{name}]: {show(s, t, m)} is decided by it", False, d)
    s, t, m, k = F.cells(r)[0]
    d = F.decide(s, dest(t), m, k)
    if grant == 'granted':
        nb = neighbour((s, t, m, k), False)
        check(f"flows[{name}]: {show(s, t, m)} is GRANTED, and {show(*nb[0]) if nb else '?'} beside it is refused "
              f"({', '.join(nb[1].rows) if nb else ''}{'closed' if nb and not nb[1].rows else ''})",
              d.granted and nb is not None, (d, nb))
    elif grant == 'refused':
        nb = neighbour((s, t, m, k), True)
        check(f"flows[{name}]: {show(s, t, m)} is REFUSED, and {show(*nb[0]) if nb else '?'} beside it is granted "
              f"({', '.join(nb[1].rows) if nb else ''})", not d.granted and nb is not None, (d, nb))
    else:
        mine = dmpass.Flows(LAW, {'flows': [{'flow': 'granted-here', 'from': s, 'to': t if isinstance(t, str) else dict(t[1]),
                                             'method': m, 'grant': 'granted', 'party': 'bea', 'basis': "her signed consent",
                                             'why': "the gardener grants this party"}]})
        ok, other = mine.decide(s, dest(t), m, k, party='bea'), mine.decide(s, dest(t), m, k, party='cem')
        check(f"flows[{name}]: {show(s, t, m)} is REFUSED until the gardener grants a named party: granted to that party, "
              f"refused to another", not d.granted and ok.granted and not other.granted and not mine.problems(),
              (d, ok, other, mine.problems()))

# how a pass is decided, one rule at a time
check("a pass no row holds is REFUSED: the law is closed",
      F.decide('journal', 'public', 'serve') == (False, 'closed', ()))
check("the nearest row decides: a peer's value taken is granted, the same copied by hand refused",
      F.decide('other-garden', dmpass.ESTATE, 'take').granted and not F.decide('other-garden', dmpass.ESTATE, 'edit').granted)
check("an origin is nearer than a layer: a closed list's word read on a guide is the law's (law-owned), a guide's "
      "amount an example's (examples-are-not-facts)",
      F.decide('guide', (dmpass.ESTATE, {'act': 'said', 'by': 'law'}), 'edit').rows == ('law-owned',)
      and F.decide('guide', (dmpass.ESTATE, {'act': 'said', 'nature': ['lekton', 'soma']}), 'edit').rows
      == ('examples-are-not-facts',))
_tie = dict(LAW, flows=list(LAW['flows']) + [{'flow': 'words-doubted', 'from': 'words', 'to': {'act': 'said'},
                                               'method': 'take-down', 'grant': 'refused', 'why': "a second word"}])
_T = dmpass.Flows(_tie, None)
check("of two rows as near, a REFUSAL — and the law that holds them is refused for it (one cell, one row)",
      not _T.decide('words', (dmpass.ESTATE, {'act': 'said'}), 'take-down').granted
      and any('one cell, one row' in w for _s, w in _T.problems()), _T.problems())
check("a row kept by the release holds only for a file the release keeps",
      F.decide('law', 'public', 'publish', 'release').granted and not F.decide('law', 'public', 'publish').granted)
_L = dmpass.Flows(LAW, {'flows': [{'flow': 'no-derived-from-history', 'from': 'history', 'to': {'act': 'derived'},
                                   'method': 'derive', 'grant': 'refused', 'why': "this garden derives nothing from a capture"}]})
check("a garden's own row refuses what the standard grants",
      F.decide('history', (dmpass.ESTATE, {'act': 'derived'}), 'derive').granted
      and not _L.decide('history', (dmpass.ESTATE, {'act': 'derived'}), 'derive').granted and not _L.problems())
_U = dmpass.Flows(LAW, {'flows': [{'flow': 'guide-is-fact', 'from': 'guide', 'to': 'estate', 'method': 'edit',
                                   'grant': 'granted', 'party': 'bea', 'basis': "none", 'why': "unguarding"},
                                  {'flow': 'nameless', 'from': 'request', 'to': 'remote', 'method': 'send',
                                   'grant': 'granted', 'why': "no party"}]})
_up = [w for _s, w in _U.problems()]
check("a garden never unguards the standard: its grant where the standard refuses is refused, and a grant names its "
      "party and basis", any('guide-is-fact' in w and 'ratified' in w for w in _up)
      and any('nameless' in w and 'party' in w for w in _up), _up)
check("a pointer is judged by the row nearest the value, whatever its method: a said value pointed at another bean "
      "meets copied-is-not-said, not the merge's row for the estate",
      F.direction(dmpass.ESTATE, (dmpass.ESTATE, {'act': 'said'})).rows == ('copied-is-not-said',)
      and F.direction('other-garden', (dmpass.ESTATE, {'act': 'said'})).granted
      and F.direction(dmpass.ESTATE, (dmpass.ESTATE, {'act': 'derived'})).granted)

# the pass record
_ok = {'from': {'file': 'words/offer.md'}, 'to': {'bean': 'lease', 'at': 'parties.bea.accepted'},
       'method': 'take-down', 'metadata': {'form': F.forms[0] if F.forms else None, 'characters': 120,
                                           'oid': '0' * 40, 'turn': 3}}
check("a pass is {from, to, method, metadata}, its metadata counts, locators, object ids and the words' form",
      F.forms and not F.pass_problems(_ok), (F.forms, F.pass_problems(_ok)))
check("a pass that carries the material, or a key beside the four, is not a pass",
      F.pass_problems(dict(_ok, metadata={'text': 'the shop is let from May'}))
      and F.pass_problems(dict(_ok, note='x')) and F.pass_problems(dict(_ok, method='whisper')))
check("an endpoint is a file, a bean, a garden, or a layer that holds no files",
      F.endpoint({'layer': 'instructions'}) == 'instructions' and F.endpoint({'garden': 'x'}) == 'other-garden'
      and isinstance(F.endpoint({'layer': 'estate'}), str)
      and F.endpoint({'bean': 'lease', 'at': 'parties.bea.accepted'})[1].get('act') == 'said')

# ==================================== THE GUARDS: computed from where each check runs ====================================
REGS, BAD = dmpass.guards(ROOT)
NAMES = {r.get('flow') for r in F.rows}
check("every tool's `GUARDS` and `EVIDENCE` is a dict literal of {checks, proof, label, when?}", not BAD, BAD)
check("no registration names a row the law does not hold", all(g[0] in NAMES for g in REGS),
      sorted({g[0] for g in REGS} - NAMES))
_missing = []
for flow, tool, place, when, reg in REGS:
    try:
        with open(os.path.join(ROOT, *reg['proof'].split('/')), encoding='utf-8') as fh:
            _txt = fh.read()
    except OSError:
        _txt = ''
    if reg['label'] not in _txt:
        _missing.append((flow, tool, reg['proof'], reg['label']))
check("each registration's proof holds a check of its label, word for word", not _missing, _missing)
STATUS = dmpass.status(F, REGS)
_by = {}
for _n, (_p, _w, _t) in STATUS.items():
    _by.setdefault(_p, []).append(_n)
check("every row has a guard, computed: " + ', '.join(f"{len(_by.get(p, []))} {p}" for p in reversed(dmpass.PLACES)),
      set(STATUS) == NAMES)
check("a check run by the pre-commit hook guards at every commit, and dmpublic's, run by the pre-push hook, at a push",
      STATUS.get('journal-rewritten', ('',))[0] == 'commit' and STATUS.get('kept-private', ('',))[0] == 'push', STATUS)

# fix 5: a check is shown where it runs — a tool the hooks do not name guards in that tool alone
_X = tempfile.mkdtemp(prefix="dmpasses-")
os.makedirs(os.path.join(_X, 'bin', 'hooks'))
with open(os.path.join(_X, 'bin', 'hooks', 'pre-commit'), 'w') as fh:
    fh.write('python3 "$REPO/bin/gatekeep.py" --staged\n')
for _t, _w in (('gatekeep', "'when': 'claimed'"), ('savekeep', '')):
    with open(os.path.join(_X, 'bin', _t + '.py'), 'w') as fh:
        fh.write("GUARDS = {'journalled': {'checks': 'x', 'proof': 'test/x.py', 'label': 'x'%s}}\n"
                 % (', ' + _w if _w else ''))
_xr, _xb = dmpass.guards(_X)
_xs = dmpass.status(F, _xr)
check("fix 5: a check only on the save road is shown as the tool's, not the commit's; one the hook runs on a condition "
      "is the commit's, conditional — and outranks the tool's",
      sorted((g[1], g[2], g[3]) for g in _xr) == [('bin/gatekeep.py', 'commit', 'claimed'), ('bin/savekeep.py', 'tool', None)]
      and _xs['journalled'][:2] == ('commit', 'claimed') and _xs['journal-rewritten'][0] == 'hoped', (_xr, _xs))
shutil.rmtree(_X, ignore_errors=True)

# the ratchet: a row checked at one release is checked at the next
_tag = run("git", "describe", "--tags", "--abbrev=0", cwd=ROOT).stdout.strip()
_old = run("git", "show", f"{_tag}:seed/std-vocab.md", cwd=ROOT).stdout if _tag else ''
_oldlaw = dmparse.loads(dmparse.split_front_matter(_old)[0] or '') if _old else None
if not (isinstance(_oldlaw, dict) and _oldlaw.get('flows')):
    print(f"SKIP  the ratchet: {_tag or 'no tag'}'s law has no `flows`, so no row was guarded before this release")
else:
    _O = tempfile.mkdtemp(prefix="dmpasses-old-")
    _a = subprocess.run(["git", "archive", _tag], capture_output=True, cwd=ROOT)
    subprocess.run(["tar", "-x", "-C", _O], input=_a.stdout)
    _before = dmpass.status(dmpass.Flows(_oldlaw, None), dmpass.guards(_O)[0])
    _fell = [(n, _before[n][:2], STATUS[n][:2]) for n in _before if n in STATUS
             and dmpass.rank(*STATUS[n][:2]) < dmpass.rank(*_before[n][:2])]
    check(f"the ratchet: no row is guarded less than at {_tag}", not _fell, _fell)
    shutil.rmtree(_O, ignore_errors=True)

# ==================================== THE GATE: a garden, committed through its hook ====================================
T = tempfile.mkdtemp(prefix="dmpasses-")
G = os.path.join(T, "g")
r = run("sh", os.path.join(ROOT, "seed", "germinate.sh"), G, "--gardener", "keeper", cwd=ROOT)
check("a garden germinates from the release, and the flow law loads in it", r.returncode == 0 and "0 error" in r.stdout,
      r.stdout + r.stderr)


def write(rel, text):
    p = os.path.join(G, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def read(rel):
    with open(os.path.join(G, *rel.split("/")), encoding="utf-8") as fh:
        return fh.read()


def save(what):
    """Save through bin/dmsave.py, the entry naming each bean the step changed."""
    names = sorted({os.path.basename(l[3:].strip())[:-3] for l in run("git", "status", "--porcelain", "-uall", "beans",
                                                                        cwd=G).stdout.splitlines() if l.endswith(".md")})
    body = "- action: " + (" ".join(f"[[{n}]]" for n in names) or "the garden") + " — " + what
    r = run(PY, "bin/dmsave.py", "keeper (test)", what, "--body", body, cwd=G)
    return r.returncode, r.stdout + r.stderr


def commit(*paths):
    """Stage `paths` and commit through the hook, as a writer who skips the save would."""
    run("git", "add", *paths, cwd=G)
    r = run("git", "-c", "user.name=keeper", "-c", "user.email=keeper@example.org", "commit", "-q", "-m", "by hand", cwd=G)
    return r.returncode, r.stdout + r.stderr


def restore(to="HEAD"):
    run("git", "reset", "-q", "--hard", to, cwd=G)
    run("git", "clean", "-qfd", cwd=G)


def gate():
    r = run(PY, "bin/dmcheck.py", "--all", cwd=G)
    return r.stdout + r.stderr


KEEPER = read("beans/keeper.md")
write("words/offer.md", "Bea's offer, as she wrote it: the shop on the corner, let from the first of May.\n")
write("notes/plan.md", "The agent's plan: take the lease down from Bea's offer.\n")
write("beans/keeper.md", KEEPER.replace("provenance:", """standing:
  - { doc: "file:words/*", standing: words, why: "what a person gave this garden, kept as they gave it" }
  - { doc: "file:notes/*", standing: work, why: "an agent's own notes" }
provenance:""", 1))
write("beans/bea.md", """---
bean: bea
genos: org
title: "Corner Lets"
status: active
summary: "The company that lets the shop."
nature: lekton
owned_by: { owner: { bean: keeper } }
identity: { status: provisional, anchors: [] }
provenance: { src: asserted-by-human, by: keeper, as_of: now }
---
The company that lets the shop on the corner.
""")
write("beans/laptop.md", """---
bean: laptop
genos: host
title: "the shop's laptop"
status: active
summary: "the machine the shop's garden is kept on"
nature: soma
os: linux
identity: { status: confirmed, anchors: [ { key: hostname, value: "shop-laptop", class: network, establishing: false }, { key: serial, value: "SN-SHOP-1", class: hardware, establishing: true } ] }
provenance: { src: asserted-by-human, by: keeper, as_of: now }
owned_by: { owner: { bean: keeper } }
---
The laptop in the back room of the shop.
""")
write("beans/work-session.md", """---
bean: work-session
genos: session
title: "a session taking the lease down"
status: active
summary: "An agent's session that takes Bea's offer into the garden."
nature: lekton
provenance: { src: generated-by-tool, by: "the session's harness", as_of: now }
owned_by: { owner: { bean: keeper } }
timing: { start: { system: gregorian-civil, at: "2026-04-21 10:00+03:00", unit: minute } }
workspace: { host: { bean: laptop }, system: unix-filesystem, at: "shop-laptop:/home/keeper/garden", branch: master }
pass_log:
  main: { holds: "file:captures/passes/work-session.jsonl" }
---
An agent's session that took the lease down from Bea's offer.
""")
rc, out = save("a words file and a work file placed, Bea, a laptop, and a session")
check("`words` placed by a standing entry on the gardener's own record, and `work` beside it: committed", rc == 0, out)
check("a journal appended to, and nothing before it changed: passes", rc == 0 and "log/journal.md" in
      run("git", "show", "--name-only", "--format=", "HEAD", cwd=G).stdout, out)

# a person's words are placed only by a person
write("beans/work-session.md", read("beans/work-session.md").replace("pass_log:", """standing:
  - { doc: "file:notes/*", standing: words, why: "the agent says so" }
pass_log:""", 1))
rc, out = save("an agent places its notes in words")
check("`words` placed on a bean whose record is a tool's: refused", rc != 0 and "only a person makes material" in out, out)
restore()

# the journal is appended, and never rewritten
_j = read("log/journal.md")
_first = next(l for l in _j.split("\n") if l.strip() and not l.startswith("#"))
write("log/journal.md", _j.replace(_first, _first + " (corrected)", 1))
rc, out = commit("log/journal.md")
check("a journal line rewritten after the fact: refused", rc != 0 and "a journal is appended and never rewritten" in out, out)
restore()

# the law carries no story
_v = read("VOCAB.md")
write("VOCAB.md", _v.replace("---\n", "---\n# we chose this after the lease went wrong\n", 1))
out = gate()
check("a comment in VOCAB.md's front matter: refused", "a comment in the law's front matter" in out, out)
write("VOCAB.md", _v.replace("---\n", "---\n# == this garden's own ==\n", 1))
out = gate()
check("...and a section title `# == <title> ==` stays", "a comment in the law's front matter" not in out, out)
restore()

# a value's pointer, where one is kept
LEASE = """---
bean: lease
genos: contract
title: "the shop lease"
status: active
summary: "Bea lets the shop to the keeper."
nature: lekton
identity:
  status: confirmed
  anchors:
    - { key: identifier, value: "contract:lease", class: logical, establishing: true }
provenance: { src: asserted-by-human, by: keeper, as_of: now }
owned_by: { crown: true }
responsibility: { legal: { parties: true } }
parties:
  bea: { who: { bean: bea }, accepted: 2026-04-20 }
  keeper: { who: { bean: keeper }, accepted: 2026-04-21 }
words: { form: spoken, agreed: 2026-04-21 }
%s---
The shop on the corner, let from the first of May.
"""


def pointed(at):
    return LEASE % f"provenance_of:\n  parties.bea.accepted: [ {{ value: 2026-04-20, src: asserted-by-human, at: {at} }} ]\n"


BASE = run("git", "rev-parse", "HEAD", cwd=G).stdout.strip()
write("beans/lease.md", pointed('"file:seed/COOKBOOK.md"'))
rc, out = save("the lease, its day pointed at a guide")
check("a value whose pointer names a guide: refused", rc != 0 and "examples-are-not-facts" in out, out)
restore()
write("beans/lease.md", pointed("{ bean: keeper, field: title }"))
rc, out = save("the lease, its day pointed at another bean")
check("a said value pointed at another bean: refused", rc != 0 and "copied-is-not-said" in out, out)
restore()
write("beans/lease.md", pointed('"file:words/nowhere.md"'))
rc, out = save("the lease, its day pointed at nothing")
check("a pointer to a file the tree does not hold: refused", rc != 0 and "resolves to no file" in out, out)
restore()
write("beans/lease.md", pointed('"file:words/offer.md"'))
rc, out = save("the lease, its day pointed at Bea's words")
check("a said value pointed at a person's words: committed", rc == 0, out)
restore(BASE)

# a session's pass log: what a commit that claims it owes
SAID = ["parties.bea.who", "parties.bea.accepted", "parties.keeper.who", "parties.keeper.accepted", "words.form",
        "words.agreed"]


def pass_(src, at, method="take-down"):
    return json.dumps({"from": src, "to": {"bean": "lease", "at": at}, "method": method,
                       "metadata": {"form": "written"} if method == "take-down" else {}})


def claim(lines):
    write("captures/passes/work-session.jsonl", "".join(l + "\n" for l in lines))
    write("beans/lease.md", LEASE % "")
    return save("the lease, taken down from Bea's offer, its session's passes logged")


WORDS = {"file": "words/offer.md"}
rc, out = claim([pass_(WORDS, p) for p in SAID])
check("a claimed commit whose said value has its pass from words: passes", rc == 0, out)
_head = run("git", "rev-parse", "HEAD", cwd=G).stdout.strip()
restore(BASE)
rc, out = claim([pass_(WORDS, p) for p in SAID[1:]])
check("a said value the claimed commit adds with no pass into it: refused", rc != 0 and "parties.bea.who" in out
      and "no granted pass" in out, out)
restore()
rc, out = claim([pass_({"file": "notes/plan.md"}, SAID[1])] + [pass_(WORDS, p) for p in SAID])
check("a pass from work into a said value: refused", rc != 0 and "model-output-is-no-word" in out, out)
restore()
rc, out = claim([pass_({"file": "seed/COOKBOOK.md"}, SAID[1])] + [pass_(WORDS, p) for p in SAID])
check("a pass from a guide into a said value: refused", rc != 0 and "examples-are-not-facts" in out, out)
restore()
rc, out = claim([pass_({"bean": "keeper"}, p, "edit") for p in SAID])
check("a claimed commit whose person's record has no pass from words or instructions: refused",
      rc != 0 and "has no pass from `words` or `instructions`" in out, out)
restore()
rc, out = claim([json.dumps({"from": WORDS, "to": {"bean": "lease", "at": SAID[1]}, "method": "take-down",
                             "metadata": {"text": "let from the first of May"}})] + [pass_(WORDS, p) for p in SAID])
check("a pass that carries the material into the log: refused", rc != 0 and "not a pass" in out, out)
restore()
run("git", "reset", "-q", "--hard", _head, cwd=G)
write("captures/passes/work-session.jsonl", "")
rc, out = commit("captures/passes/work-session.jsonl")
check("a pass log cut back: refused — it only grows", rc != 0 and "does not extend its copy at HEAD" in out, out)
restore()
write("captures/passes/stray.jsonl", pass_(WORDS, SAID[1]) + "\n")
rc, out = save("a log no session names")
check("a pass log no session bean names: refused", rc != 0 and "no session bean's `pass_log` names" in out, out)
restore()
write("beans/bea.md", read("beans/bea.md").replace('summary: "The company that lets the shop."',
                                                   'summary: "The company that lets the shop on the corner."'))
rc, out = save("Bea's summary, in a commit that claims no session")
check("a commit that claims no session owes none of it", rc == 0, out)

# THE TOOLS READ A GARDEN'S ROWS AS THE GATE DOES: its restated registry, and the rows it adds
sys.path.insert(0, os.path.join(ROOT, "bin"))
import dmpass as _dp
_o = _dp.Origins({"natures": [{"nature": "soma"}]}, {"registry_additions": {"natures": [{"nature": "ergon"}]}})
check("the origins read a nature a garden adds, as the gate reads it", _o.natures == ["soma", "ergon"], _o.natures)
_v = open(os.path.join(G, "VOCAB.md"), encoding="utf-8").read()
open(os.path.join(G, "VOCAB.md"), "w", encoding="utf-8", newline="\n").write(re.sub(r"(?m)^registry_additions:.*\n", "", _v).replace(
    "\n---\n", "\nregistry_additions:\n  anchor_systems: [ { system: office-grid, dimension: place, levels: open, neighbours: none, "
    "meaning: \"a grid of desks\", pattern: \"^[a-z][0-9]+$\", establishes: false } ]\n"
    "  leaf_orders: [ { order: office-rank, suffix: _desk, exact: [], why: \"a test's order\" } ]\n---\n", 1))
_r = subprocess.run([sys.executable, "-c", "import sys; sys.path.insert(0, 'bin'); import dmmerge as M; "
                     "print('office-grid' in M.SYSTEM_ROWS, any(r.get('order') == 'office-rank' for r in M.LEAF_ORDERS))"],
                    capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=G)
open(os.path.join(G, "VOCAB.md"), "w", encoding="utf-8", newline="\n").write(_v)
check("...and the merge reads a system and an order a garden adds, as its gate does",
      _r.stdout.strip() == "True True", _r.stdout + _r.stderr[-600:])

shutil.rmtree(T, ignore_errors=True)
print(f"\npasses: {RUN[0] - len(FAILS)}/{RUN[0]} checks passed, {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
