#!/usr/bin/env python3
"""mycelium — three gardens, two of them on one machine, meet only by proposal (std-vocab 21.0).

WHAT IT PROVES. A garden is kept by its gardener and nothing outside it writes there; what one garden gives another
is a proposal (bin/dmpropose.py), made under an agreement both gardeners are party to, laid outside every garden,
read and taken in by the receiving garden's own agent, and ratified by its gardener's commit. A name a garden mints
is BARE until the garden qualifies it with its own id, and bin/dmmerge.py fuses a bare name only within one garden —
so a thing two gardens share is named once and seen as ONE, while the same made-up name in two gardens is a
candidate for a person and never a fusion.

THE FIXTURE, all of it synthetic and neutral. garden-a is kept by ada on machine one; garden-b (ben) and garden-c
(cai) sit side by side under one directory on machine two, each with its own repository-local git identity. Ada and
ben share a cost two to one, in XTS (ISO 4217's code for testing): garden-a records the agreement, qualifies its name,
and proposes it to garden-b with ada's own bean; garden-b takes it in. Nothing here is mocked: real germination,
real commits through the real pre-commit gate, the real tools each garden received.

Run: python3 test/mycelium.py   (0 = green)
"""
import datetime
import itertools
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'bin'))
import dmparse
import yaml

results = []


def check(name, ok, detail=''):
    results.append(bool(ok))
    print(("PASS " if ok else "*** FAIL *** ") + name + (f"  [{str(detail)[-600:]}]" if detail and not ok else ''))


TMP = tempfile.mkdtemp(prefix='dmmyc-')
ONE, TWO = os.path.join(TMP, 'machine-one'), os.path.join(TMP, 'machine-two')
os.makedirs(ONE)
os.makedirs(TWO)
A, B, C = os.path.join(ONE, 'garden-a'), os.path.join(TWO, 'garden-b'), os.path.join(TWO, 'garden-c')
WHO = {A: 'ada', B: 'ben', C: 'cai'}


def run(args, cwd):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding='utf-8')


def tool(g, name, *args):
    """A tool as the garden received it — each garden runs its own copy."""
    r = run([sys.executable, os.path.join(g, 'bin', name)] + list(args), cwd=g)
    r.out = r.stdout + r.stderr
    return r


def git(g, *args):
    return run(['git', '-C', g] + list(args), cwd=g)


def write(g, bid, text):
    with open(os.path.join(g, 'beans', bid + '.md'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)


def read(p):
    return open(p, encoding='utf-8').read()


def fm_of(path):
    return yaml.safe_load(dmparse.read(path)[0])


def commit(g, what, body):
    """Journal (the heading stamped by the tool) and commit — the commit runs the garden's own pre-commit gate."""
    j = tool(g, 'dmjournal.py', WHO[g], what, '--body', body)
    assert j.returncode == 0, j.out
    git(g, 'add', '-A')
    return git(g, 'commit', '-q', '-m', what)


def gate(g):
    r = tool(g, 'dmcheck.py')
    lines = [l for l in r.stdout.splitlines() if l.strip()]
    return r.returncode, (lines[-1] if lines else r.out)


def person(bid, title, anchor, by, body, extra=''):
    ident = (f"  status: confirmed\n  anchors:\n    - {{ key: person_id, value: \"{anchor}\", class: logical, "
             f"establishing: true }}\n") if anchor else "  status: provisional\n  anchors: []\n"
    return (f"---\nbean: {bid}\nkind: person\ntitle: \"{title}\"\nstatus: active\nsummary: \"{title}.\"\n"
            f"nature: living\nowned_by: {{ legal: {{ crown: love }} }}\nresponsibility: {{ legal: {{ self: true }} }}\n"
            f"identity:\n{ident}provenance: {{ src: asserted-by-human, by: \"{by}\", as_of: 2026-09-23 }}\n{extra}"
            f"---\n{body}\n")


def garden_bean(bid, gid, owner, by):
    return (f"---\nbean: {bid}\nkind: garden\ntitle: \"{bid} — the garden {owner} keeps\"\nstatus: active\n"
            f"summary: \"Another garden this one deals with, kept by {owner}.\"\nnature: metaphysical\n"
            f"owned_by: {{ legal: {{ owner: {{ bean: {owner} }} }} }}\n"
            f"responsibility: {{ legal: {{ holder: {{ bean: {owner} }} }} }}\n"
            f"identity:\n  status: confirmed\n  anchors:\n"
            f"    - {{ key: garden_id, value: \"{gid}\", class: logical, establishing: true }}\n"
            f"provenance: {{ src: asserted-by-human, by: \"{by}\", as_of: 2026-09-23 }}\n"
            f"---\nThe garden {owner} keeps; its id was read there with `python3 bin/dmpropose.py id`.\n")


def tree(g):
    """Every file of a garden outside .git, with its size and moment — so "writes nothing" can be checked, bytecode
    caches included."""
    out = []
    for dp, dns, fns in os.walk(g):
        dns[:] = [d for d in dns if d != '.git']
        for f in fns:
            st = os.stat(os.path.join(dp, f))
            out.append((os.path.relpath(os.path.join(dp, f), g), st.st_size, st.st_mtime_ns))
    return sorted(out)


def seeds_of(out):
    """The seeds a `dmmerge` run printed, by id."""
    lines, seeds = out.splitlines(), {}
    for i, l in enumerate(lines):
        m = re.match(r'^=== seed (\S+) ===$', l)
        if m and i + 1 < len(lines):
            seeds[m.group(1)] = json.loads(lines[i + 1])
    return seeds


def anchored(seeds, value):
    return [s for s in seeds.values() if any(a.get('value') == value for a in s['identity']['anchors'])]


# ================================================================ three gardens, two on one machine
for g in (A, B, C):
    r = run([sys.executable, os.path.join(ROOT, 'seed', 'germinate.py'), g, '--gardener', WHO[g]], cwd=ROOT)
    git(g, 'config', 'user.name', WHO[g])
    git(g, 'config', 'user.email', f'{WHO[g]}@example.org')
check("three gardens germinate, each with its gardener; two share one parent directory, each its own git identity",
      all(os.path.isfile(os.path.join(g, 'beans', WHO[g] + '.md')) for g in (A, B, C))
      and os.path.dirname(B) == os.path.dirname(C)
      and [git(g, 'config', '--local', 'user.name').stdout.strip() for g in (A, B, C)] == ['ada', 'ben', 'cai'])

ID = {}
for g in (A, B, C):
    ID[g] = str(yaml.safe_load(tool(g, 'dmpropose.py', 'id').stdout)['garden_id'])
AID, BID, CID = ID[A], ID[B], ID[C]
check("`dmpropose id` reads each garden's id from git: the germination commit, twelve hex digits, three different",
      all(re.match(r'^[0-9a-f]{12}$', i) for i in ID.values()) and len(set(ID.values())) == 3
      and all(git(g, 'rev-list', '--max-parents=0', 'HEAD').stdout.strip().startswith(ID[g]) for g in (A, B, C))
      and not any(ID[g] in read(os.path.join(g, 'GARDEN.md')) for g in (A, B, C)), ID)

# ---- a gardener's name is minted once: `mint` prints the qualified name and the command, and writes nothing
before = read(os.path.join(A, 'beans', 'ada.md'))
m = tool(A, 'dmpropose.py', 'mint', 'ada')
cmd = next((l.strip() for l in m.stdout.splitlines() if 'bin/dmsafe.py flow-set' in l), '')
check("`mint` prints the qualified name and the dmsafe command, and writes nothing (choosing an anchor is class F)",
      f"{AID}/person:ada" in m.stdout and cmd and read(os.path.join(A, 'beans', 'ada.md')) == before, m.out)
for g, bid in ((A, 'ada'), (B, 'ben')):
    line = next(l.strip() for l in tool(g, 'dmpropose.py', 'mint', bid).stdout.splitlines() if 'flow-set' in l)
    argv = shlex.split(line)
    run([sys.executable] + argv[1:], cwd=g)
    commit(g, f"qualified {bid}'s name", f"- action: [[{bid}]]'s person_id qualified by this garden's id "
                                          f"(dmpropose mint; the gardener ratified the anchor, class F).")
check("...and the command it prints qualifies the name: `<garden_id>/person:<id>`, through the gate",
      fm_of(os.path.join(A, 'beans', 'ada.md'))['identity']['anchors'][0]['value'] == f"{AID}/person:ada"
      and fm_of(os.path.join(B, 'beans', 'ben.md'))['identity']['anchors'][0]['value'] == f"{BID}/person:ben"
      and gate(A)[0] == 0 and gate(B)[0] == 0)

# ================================================================ garden-a records garden-b, and the agreement
write(A, 'ada', person('ada', 'Ada — gardener of garden-a', f"{AID}/person:ada", 'ada (gardener)', 'Ada keeps this garden.',
                       extra='details:\n  gardening_since: "2026-09-01"          # she says so\n'))
write(A, 'garden-b', garden_bean('garden-b', BID, 'neighbour-ben', 'ada (gardener)'))
write(A, 'neighbour-ben', person('neighbour-ben', 'Ben — gardener of garden-b', f"{BID}/person:ben", 'ada (gardener)',
                                 'Ben keeps garden-b, on machine two.'))
write(A, 'sam', person('sam', 'Sam — a neighbour', 'person:sam', 'ada (gardener)', 'Sam lives nearby.'))
write(A, 'ali', person('ali', 'Ali — a friend', None, 'ada (gardener)', 'Nobody has named Ali yet.'))
SHARED = f"""---
bean: shared-cost
kind: contract
title: "A shared cost of 900 XTS, borne two to one by ada and ben"
status: active
summary: "Ada paid all of it; ada bears two parts and ben one. What each owes is read from the transaction, never written."
nature: metaphysical
owned_by: {{ legal: {{ crown: logos }} }}
responsibility: {{ legal: {{ parties: true }} }}
identity:
  status: confirmed
  anchors:
    - {{ key: contract_id, value: "{AID}/contract:shared-cost", class: logical, establishing: true }}
provenance: {{ src: asserted-by-human, by: "ada (gardener)", as_of: 2026-09-23 }}
parties:
  ada: {{ who: {{ bean: ada }}, role: payer, accepted: 2026-09-20 }}
  ben: {{ who: {{ bean: neighbour-ben }}, accepted: 2026-09-20,
         provenance: {{ src: asserted-by-human, by: "ada (gardener), reporting ben's acceptance", as_of: 2026-09-23 }} }}
words: {{ form: spoken, agreed: 2026-09-20, note: "agreed aloud, both present" }}
clauses:
  ben-repays:
    what: "ben pays ada his part of the shared cost"
    by: ben
    to: ada
    state: in-force
transactions:
  the-cost:
    what: "the shared cost"
    amount: {{ count: 900, unit: XTS }}
    paid_by: [ {{ party: ada }} ]
    borne_by: [ {{ party: ada, share: 2 }}, {{ party: ben, share: 1 }} ]
---
A cost ada paid in full; ben bears one part in three.
"""
write(A, 'shared-cost', SHARED)
r = commit(A, "garden-b, ben, and what ada and ben share",
           "- action: recorded [[garden-b]] (read there with dmpropose id), [[neighbour-ben]] who keeps it, "
           "[[shared-cost]] named once by this garden, [[ada]]'s gardening_since, and two neighbours [[sam]] and "
           "[[ali]].")
check("garden-a records garden-b as a `garden` bean and the agreement minted once, qualified by garden-a's id — "
      "through its gate", r.returncode == 0 and gate(A) == (0, gate(A)[1]) and ' 0 error(s)' in gate(A)[1],
      r.stdout + r.stderr + gate(A)[1])

# ================================================================ garden-b records garden-a; garden-c holds a `sam`
write(B, 'garden-a', garden_bean('garden-a', AID, 'ada', 'ben (gardener)'))
write(B, 'ada', person('ada', 'Ada — gardener of garden-a', f"{AID}/person:ada", 'ben (gardener)',
                       'Ada keeps garden-a; ben deals with her.',
                       extra='details:\n  gardening_since: "2026-09-01 18:30+03:00"   # read off garden-a\'s first '
                             'commit\n').replace('src: asserted-by-human, by: "ben (gardener)"',
                                                 'src: inferred, by: "agent (for ben)"'))
write(B, 'garden-c', garden_bean('garden-c', CID, 'cai', 'ben (gardener)'))
write(B, 'cai', person('cai', 'Cai — gardener of garden-c', f"{CID}/person:cai", 'ben (gardener)',
                       'Cai keeps garden-c, beside this one.'))
write(B, 'house-costs', f"""---
bean: house-costs
kind: contract
title: "House costs of 300 XTS, shared equally by ben and cai"
status: active
summary: "Ben paid; ben and cai bear it equally. What each owes is read, never written."
nature: metaphysical
owned_by: {{ legal: {{ crown: logos }} }}
responsibility: {{ legal: {{ parties: true }} }}
identity:
  status: confirmed
  anchors:
    - {{ key: contract_id, value: "{BID}/contract:house-costs", class: logical, establishing: true }}
provenance: {{ src: asserted-by-human, by: "ben (gardener)", as_of: 2026-09-23 }}
parties:
  ben: {{ who: {{ bean: ben }}, role: payer, accepted: 2026-09-21 }}
  cai: {{ who: {{ bean: cai }}, accepted: 2026-09-21 }}
words: {{ form: spoken, agreed: 2026-09-21 }}
clauses:
  cai-repays:
    what: "cai pays ben her half"
    by: cai
    to: ben
transactions:
  the-costs:
    what: "the house costs"
    amount: {{ count: 300, unit: XTS }}
    paid_by: [ {{ party: ben }} ]
    borne_by: [ {{ party: ben, share: 1 }}, {{ party: cai, share: 1 }} ]
---
What ben and cai share.
""")
r = commit(B, "garden-a and garden-c, their gardeners, and the house costs",
           "- action: recorded [[garden-a]] and [[garden-c]] (their ids read there), [[ada]] (inferred by the agent), "
           "[[cai]], and [[house-costs]] shared with cai.")
write(C, 'sam', person('sam', 'Sam — a neighbour', 'person:sam', 'cai (gardener)', 'Sam lives nearby.'))
r2 = commit(C, "a neighbour", "- action: recorded [[sam]] under a name this garden made up.")
check("garden-b records garden-a (and garden-c) the same way, and garden-c a `sam` under the same BARE name as "
      "garden-a's", r.returncode == 0 and r2.returncode == 0 and ' 0 error(s)' in gate(B)[1],
      r.stdout + r.stderr + r2.stdout + r2.stderr + gate(B)[1])

# ================================================================ make — and what it refuses
def proposals(d):
    return sorted(f for f in os.listdir(d) if f.startswith('PROPOSAL-'))


jA = read(os.path.join(A, 'log', 'journal.md'))
r = tool(A, 'dmpropose.py', 'make', '--to', 'garden-b', '--under', 'shared-cost', 'sam')
check("make REFUSES a bean known only by a BARE minted name — with the mint hint — and writes nothing",
      r.returncode == 1 and 'BARE' in r.out and 'dmpropose.py mint sam' in r.out and not proposals(ONE)
      and read(os.path.join(A, 'log', 'journal.md')) == jA, r.out)
r = tool(A, 'dmpropose.py', 'make', '--to', 'garden-b', '--under', 'shared-cost', 'ali')
check("...and an ANCHORLESS bean the same way: it would identify nothing beyond this garden",
      r.returncode == 1 and 'dmpropose.py mint ali' in r.out and not proposals(ONE), r.out)
r = tool(A, 'dmpropose.py', 'make', '--to', 'garden-b', '--under', 'shared-cost', '--out', os.path.join(B, 'inbox'),
         'shared-cost', 'ada')
check("...and an --out inside a garden: a proposal is laid beside gardens, never in one",
      r.returncode == 1 and 'never in' in r.out and not os.path.exists(os.path.join(B, 'inbox')), r.out)

r = tool(A, 'dmpropose.py', 'make', '--to', 'garden-b', '--under', 'shared-cost', 'shared-cost', 'ada')
made = proposals(ONE)
P = os.path.join(ONE, made[0]) if made else ''
env = yaml.safe_load(dmparse.read(P)[0]) if P else {}
check("make lays ONE proposal beside the garden, PROPOSAL-<garden>-<YYYYMMDD-HHMM>.md, inside no garden",
      r.returncode == 0 and len(made) == 1 and re.match(r'^PROPOSAL-garden-a-\d{8}-\d{4}\.md$', made[0]), r.out)
check("...its envelope: from garden-a's id and gardener at its pin, to garden-b's id, under the qualified agreement",
      env.get('from', {}).get('garden') == AID and env['from'].get('gardener') == 'ada'
      and env['from'].get('pin') == fm_of(os.path.join(A, 'GARDEN.md'))['extends']
      and env.get('to') == {'garden': BID} and env.get('under') == {'contract_id': f"{AID}/contract:shared-cost"}
      and env.get('beans') == ['shared-cost', 'ada'] and env.get('stubs') == ['neighbour-ben']
      and str(env.get('fingerprint', '')).startswith('sha256:'), env)
body = read(P) if P else ''
blk = re.search(r'```daftar-bean shared-cost\n(.*?)```', body, re.S)
carried = yaml.safe_load(dmparse.split_front_matter(blk.group(1))[0]) if blk else {}
check("...each offered bean as committed, `provenance.garden` stamped on the COPY's records — bean and entry alike — "
      "and never in garden-a's own file",
      carried.get('provenance') == {'src': 'asserted-by-human', 'by': 'ada (gardener)',
                                    'as_of': datetime.date(2026, 9, 23), 'garden': AID}
      and carried['parties']['ben']['provenance'].get('garden') == AID
      and 'A cost ada paid in full' in blk.group(1) and read(os.path.join(A, 'beans', 'shared-cost.md')) == SHARED,
      carried)
check("...and a STUB, identity only, for the bean it refers to and does not carry",
      re.search(r'```daftar-stub neighbour-ben\n', body) and f"{BID}/person:ben" in body
      and 'Ben keeps garden-b' not in body)
jA2 = read(os.path.join(A, 'log', 'journal.md'))
check("...and a journal entry in garden-a, stamped by the tool, naming what left, to which garden, under what, "
      "the fingerprint — uncommitted",
      jA2.startswith(jA) and '[[garden-b]]' in jA2[len(jA):] and env.get('fingerprint') in jA2[len(jA):]
      and 'journal.md' in git(A, 'status', '--porcelain').stdout, jA2[len(jA):])
commit(A, "the proposal to garden-b, made", "- action: the proposal of [[shared-cost]] and [[ada]] to garden-b left.")

# ---- the medium between machines: a copy of one file
PB = os.path.join(TWO, made[0])
shutil.copyfile(P, PB)

# ================================================================ read — writes nothing
statusB = git(B, 'status', '--porcelain').stdout
treeB = tree(B)
r = tool(B, 'dmpropose.py', 'read', PB)
treeB2 = tree(B)
check("read in garden-b: the agreement is NEW, ada FUSES WITH garden-b's ada, the stub RESOLVES TO ben",
      re.search(r'shared-cost\s+NEW', r.stdout) and re.search(r'ada\s+FUSES WITH ada', r.stdout)
      and re.search(r'neighbour-ben\s+RESOLVES TO ben', r.stdout) and 'verified' in r.stdout, r.out)
check("...the one disagreement is named, both values kept for the gardener; the gate on a scratch copy with it "
      "taken: 0 errors",
      'CONFLICT details.gardening_since' in r.stdout and re.search(r'GATE .*: .* 0 error\(s\)', r.stdout)
      and r.returncode == 1, r.out)
check("...and read wrote nothing in garden-b — not a file, not a bytecode cache",
      git(B, 'status', '--porcelain').stdout == statusB and treeB2 == treeB,
      sorted(set(treeB2) ^ set(treeB))[:6])

r = tool(C, 'dmpropose.py', 'read', PB)
check("read REFUSES a proposal in the wrong garden: 'this proposal is for another garden'",
      r.returncode == 1 and 'this proposal is for another garden' in r.out, r.out)

TAMPERED = os.path.join(TWO, 'tampered.md')
open(TAMPERED, 'w', encoding='utf-8').write(read(PB).replace('count: 900, unit: XTS', 'count: 9000, unit: XTS'))
r = tool(B, 'dmpropose.py', 'read', TAMPERED)
check("read REFUSES a tampered proposal: the fingerprint does not match", r.returncode == 1 and 'fingerprint does not '
      'match' in r.out and 'GATE' not in r.stdout, r.out)
PINNED = os.path.join(TWO, 'pinned.md')
open(PINNED, 'w', encoding='utf-8').write(read(PB).replace(f"pin: {env['from']['pin']}", 'pin: std-vocab@20.0'))
r = tool(B, 'dmpropose.py', 'read', PINNED)
check("read REFUSES a proposal whose pin differs (MERGE.md §5.2: different pins block)",
      r.returncode == 1 and 'pins differ' in r.out, r.out)

# ---- a rehearsal: a clone of garden-a (the same garden) marked as a test garden proposes the same thing
REH = os.path.join(ONE, 'rehearsal-of-a')
git(ONE, 'clone', '-q', A, REH)
gtxt = read(os.path.join(REH, 'GARDEN.md')).replace('---\n# ', 'test: "a rehearsal of garden-a"\n---\n# ', 1)
open(os.path.join(REH, 'GARDEN.md'), 'w', encoding='utf-8').write(gtxt)
os.makedirs(os.path.join(TWO, 'rehearsals'))
r = tool(REH, 'dmpropose.py', 'make', '--to', 'garden-b', '--under', 'shared-cost', '--out',
         os.path.join(TWO, 'rehearsals'), 'shared-cost', 'ada')
PT = os.path.join(TWO, 'rehearsals', proposals(os.path.join(TWO, 'rehearsals'))[0]) if r.returncode == 0 else ''
rr = tool(B, 'dmpropose.py', 'read', PT) if PT else r
rt = tool(B, 'dmpropose.py', 'take', PT) if PT else r
check("a test garden's proposal carries `from.test`; read flags it and take REFUSES it into a garden that is not a "
      "test garden without --as-test",
      PT and yaml.safe_load(dmparse.read(PT)[0])['from'].get('test') == 'a rehearsal of garden-a'
      and 'FROM A TEST GARDEN' in rr.stdout and rt.returncode == 1 and '--as-test' in rt.out
      and git(B, 'status', '--porcelain').stdout == statusB, r.out + rr.out + rt.out)

# ================================================================ take — in the working tree, never committed
headB = git(B, 'rev-parse', 'HEAD').stdout
r = tool(B, 'dmpropose.py', 'take', PB)
check("take applies it in garden-b's working tree and commits nothing; the gate: 0 errors",
      r.returncode == 0 and re.search(r'GATE: .* 0 error\(s\)', r.stdout)
      and git(B, 'rev-parse', 'HEAD').stdout == headB, r.out)
sc = fm_of(os.path.join(B, 'beans', 'shared-cost.md'))
check("...the NEW agreement is written with its reference moved from the stub to the local bean (neighbour-ben -> ben)",
      sc and sc['parties']['ben']['who'] == {'bean': 'ben'} and sc['parties']['ada']['who'] == {'bean': 'ada'}
      and sc['identity']['anchors'][0]['value'] == f"{AID}/contract:shared-cost", sc)
check("...provenance crosses UNCHANGED, with `garden` stamped once — on the bean and on the entry",
      sc['provenance'] == dict(fm_of(os.path.join(A, 'beans', 'shared-cost.md'))['provenance'], garden=AID)
      and sc['parties']['ben']['provenance']['by'] == "ada (gardener), reporting ben's acceptance"
      and sc['parties']['ben']['provenance']['garden'] == AID, sc.get('provenance'))
ada_b = fm_of(os.path.join(B, 'beans', 'ada.md'))
got = (ada_b.get('details') or {}).get('gardening_since')
check("THE GUARD ACROSS GARDENS: an INFERRED finer reading in garden-b does not swallow garden-a's ASSERTED one — "
      "both kept, the bean marked unclean",
      isinstance(got, dict) and sorted(map(str, got.get('conflict') or [])) == ['2026-09-01', '2026-09-01 18:30+03:00']
      and ada_b.get('merge_open') is True, ada_b)
pv = (ada_b.get('provenance_of') or {}).get('details.gardening_since') or []
check("...and who said each value is kept beside it: asserted-by-human from garden-a, inferred here",
      {(str(x['value']), x['src'], tuple(x['seen_in'])) for x in pv}
      == {('2026-09-01', 'asserted-by-human', (AID,)), ('2026-09-01 18:30+03:00', 'inferred', (BID,))}, pv)
gb = fm_of(os.path.join(B, 'beans', 'garden-a.md'))
cap = (gb.get('capture') or {}).get(env['proposal']) or {}
held = os.path.join(B, 'captures', 'proposals', 'garden-a', env['proposal'] + '.md')
check("...the proposal is kept as a `capture` on garden-a's `garden` bean, staleness-keyed by its fingerprint, the "
      "file itself kept whole",
      cap.get('source') == 'dmpropose take' and cap.get('staleness_key') == env['fingerprint']
      and cap.get('holds') == f"file:captures/proposals/garden-a/{env['proposal']}.md"
      and isinstance(cap.get('taken_at'), int) and os.path.isfile(held) and read(held) == read(PB), cap)
jB = read(os.path.join(B, 'log', 'journal.md'))
entry = jB[jB.rfind('\n## '):]
check("...and a journal entry, stamped, naming every bean it changed and quoting the proposal's own journal as data",
      all(f'[[{b}]]' in entry for b in ('shared-cost', 'ada', 'garden-a')) and '  > - proposed by: ada' in entry
      and f"took in proposal {env['proposal']}" in entry, entry)
r = git(B, 'add', '-A')
r = git(B, 'commit', '-q', '-m', 'took in the proposal from garden-a')
check("ben's commit is the ratification: it passes garden-b's own pre-commit gate", r.returncode == 0
      and ' 0 error(s)' in gate(B)[1], r.stdout + r.stderr + gate(B)[1])
r = tool(B, 'dmpropose.py', 'read', PB)
check("a proposal taken in once is refused the second time", r.returncode == 1 and 'taken in already' in r.out, r.out)

# ================================================================ the merge: one agreement, not two, not four
r = tool(A, 'dmmerge.py', A, B)
seeds = seeds_of(r.stdout)
one = anchored(seeds, f"{AID}/contract:shared-cost")
check("dmmerge of garden-a and garden-b yields ONE canonical agreement — not two, not four",
      len(one) == 1 and one[0]['gardens'] == ['garden-a', 'garden-b']
      and len([s for s in seeds.values() if s['kind'] == 'contract']) == 2, sorted(seeds))
ada_seed = anchored(seeds, f"{AID}/person:ada")
check("...ada is one being in both, and her asserted day survives the merge beside the inferred reading",
      len(ada_seed) == 1 and '2026-09-01"' in json.dumps(ada_seed[0]['facts'].get('details'))
      and 'conflict' in json.dumps(ada_seed[0]['facts'].get('details')), ada_seed)

import dmmerge as M
gA, gB, gC = M.load_garden(A, 'garden-a'), M.load_garden(B, 'garden-b'), M.load_garden(C, 'garden-c')
check("each input carries its garden: the garden_id read from git for a garden directory",
      {b['garden_id'] for b in gA} == {AID} and {b['garden_id'] for b in gC} == {CID})
r = tool(A, 'dmmerge.py', A, C)
sams = anchored(seeds_of(r.stdout), 'person:sam')
check("a BARE `person:sam` in garden-a and in garden-c is a CANDIDATE, reported for a person — and never fused",
      'CANDIDATES — a person decides (class J)' in r.stdout and re.search(r'person_id person:sam — garden-a:sam, '
                                                                          r'garden-c:sam', r.stdout)
      and len(sams) == 2 and all(s['identity'].get('id_collision') for s in sams), r.stdout[-800:])
cands = M.candidates(gA + gC)
check("...the library says the same", [(c['key'], c['value']) for c in cands] == [('person_id', 'person:sam')]
      and len(anchored(M.merge_gardens([gA, gC]), 'person:sam')) == 2, cands)
gR = M.load_garden(REH, 'rehearsal-of-a')
check("a bare name fuses WITHIN one garden: a clone of garden-a is garden-a, and its `sam` is the same `sam`",
      {b['garden_id'] for b in gR} == {AID} and not M.candidates(gA + gR)
      and len(anchored(M.merge_gardens([gA, gR]), 'person:sam')) == 1)
NEWHIST = os.path.join(ONE, 'copy-of-a')
shutil.copytree(A, NEWHIST, ignore=shutil.ignore_patterns('.git'))
git(NEWHIST, 'init', '-q')
git(NEWHIST, 'add', '-A')
git(NEWHIST, '-c', 'user.name=x', '-c', 'user.email=x@example.org', 'commit', '-q', '--no-verify', '-m', 'copy')
gN = M.load_garden(NEWHIST, 'copy-of-a')
check("...while a copy given a new history is ANOTHER garden: its `sam` is a candidate, its qualified names still fuse",
      {b['garden_id'] for b in gN} not in ({AID}, {None})
      and [c['value'] for c in M.candidates(gA + gN)] == ['person:sam']
      and len(anchored(M.merge_gardens([gA, gN]), f"{AID}/contract:shared-cost")) == 1)
fps = {M.fingerprint(M.merge_gardens(list(p)))[0] for p in itertools.permutations([gA, gB, gC])}
cps = {json.dumps(M.candidates([b for lst in p for b in lst])) for p in itertools.permutations([gA, gB, gC])}
check("MERGE INVARIANTS: the same seeds and the same candidates in every order of the three gardens (6 orders)",
      len(fps) == 1 and len(cps) == 1, (fps, cps))
check("...idempotent: a garden merged with itself is itself",
      M.fingerprint(M.merge_gardens([gA, gA]))[0] == M.fingerprint(M.merge_gardens([gA]))[0])
check("...and an input whose garden nobody can name is a garden of its own: its bare names fuse with no other's",
      len(anchored(M.merge_gardens([[dict(b, garden_id=None) for b in gA],
                                    [dict(b, garden_id=None, garden='x') for b in gA]]), 'person:sam')) == 2)

# ================================================================ what garden-b may pass on
r = tool(B, 'dmpropose.py', 'make', '--to', 'garden-c', '--under', 'house-costs', 'shared-cost')
check("garden-b may NOT pass garden-a's own records on to garden-c: a third garden's word is not its to give",
      r.returncode == 1 and 'not this garden\'s to pass on' in r.out and AID in r.out
      and not [f for f in proposals(TWO) if f.startswith('PROPOSAL-garden-b')], r.out)
r = tool(B, 'dmpropose.py', 'make', '--to', 'garden-a', '--under', 'shared-cost', 'shared-cost')
mine = [f for f in proposals(TWO) if f.startswith('PROPOSAL-garden-b')]
back = read(os.path.join(TWO, mine[0])) if mine else ''
blk = re.search(r'```daftar-bean shared-cost\n(.*?)```', back, re.S)
bfm = yaml.safe_load(dmparse.split_front_matter(blk.group(1))[0]) if blk else {}
check("...but may give it back to garden-a, whose record it is — and `garden` is stamped ONCE: still garden-a's, "
      "never re-stamped as garden-b's",
      r.returncode == 0 and bfm.get('provenance', {}).get('garden') == AID and BID not in json.dumps(
          bfm.get('provenance'), default=str), r.out)
r = tool(B, 'dmpropose.py', 'make', '--to', 'garden-c', '--under', 'house-costs', 'house-costs')
check("...and garden-b's own agreement with cai goes to garden-c, beside garden-b and inside neither garden",
      r.returncode == 0 and len([f for f in proposals(TWO) if f.startswith('PROPOSAL-garden-b')]) == 2
      and not proposals(B) and not proposals(C), r.out)

shutil.rmtree(TMP, ignore_errors=True)
print(f"\nmycelium: {sum(results)}/{len(results)} checks passed")
sys.exit(0 if all(results) else 1)
