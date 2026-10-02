#!/usr/bin/env python3
"""The translator: a garden of v0.48.0 beans written in the core's statements, into a copy, with nothing lost.

Writes a small garden in today's form by hand: a person, a host and an instance with an owner, a keeper, anchors, where
it is, what it serves, what it needs, how it can fail and what it may do; a contract with two parties, a clause and a
loan; a session with its start and stop; and a procedure (a mapping). Each bean's day of knowing is named by a journal
entry, so its moment is the clock's. Translates it into a copy and checks:
- the count: every value placed and found where it was put, and every comment line kept;
- the core's engine passes the copy;
- each term went the way the map sends it;
- the garden itself is untouched, and a copy that already exists is refused;
- a value taken out of a written bean is reported as having no place.
"""
import os, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from core import read, standards, translate  # noqa: E402
from core.law import Law  # noqa: E402

FAILS = []
PY = sys.executable


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:1500]))
    if not cond:
        FAILS.append(name)


BEANS = {
    'sam': """---
bean: sam
genos: person
title: "Sam"
status: active
summary: "the gardener"
nature: soma
identity:
  status: confirmed
  anchors:
    - { key: email, value: "sam@example.invalid", class: logical, establishing: true }
provenance: { src: asserted-by-human, by: "sam (the gardener)", as_of: 2026-09-20 }
owned_by: { crown: true }
---
Sam keeps this garden.
""",
    'box': """---
bean: box
genos: host
title: "box, a small server"
status: active
summary: "a host in the rack"
nature: soma
identity:
  # the serial on the label, read by hand
  status: confirmed
  anchors:
    - { key: serial, value: "SN-0042", class: hardware, establishing: true, observed: 2026-09-20 }
provenance: { src: observed, by: "agent:a-model/core-test, over ssh", as_of: 2026-09-20 }
owned_by: { owner: { bean: sam } }
responsibility: { legal: { holder: { bean: sam } }, technical: { holder: { bean: sam } } }
via:
  - { bean: sam }
located_at:
  - { system: ipv4, openness: elsewhere, at: 192.0.2.10, note: "its address on the lan" }
  - { system: unix-filesystem, openness: elsewhere, at: "box:/srv/data", role: data }
endpoints:
  - { protocol: ssh, system: ipv4, at: 192.0.2.10, port: 22, exposure: lan, observed: 2026-09-20 }
roles:
  - { role: file-server, observed: 2026-09-20, why: "it holds the shares" }
knowledge:
  - { code: "technology:rsync", rel: uses }
  - { code: "isco-08:2511", rel: classified_as }
risks:
  disk-full:   # found on the first survey
    what: "the data volume fills"
    consequence: "the nightly copy stops"
    severity: medium
    state: live
    evidence: "df at 85%"
    found: 2026-09-20
capabilities:
  ip-forwarding: { why: "a file server routes nothing", permission: forbidden, feasibility: possible, feasibility_why: "a sysctl turns it on" }
refs:
  rack: { bean: sam, rel: kept-by }
open:
  - "label the second disk"
owns:
  shares: "projects and archive"
tags: [host, test]
details:
  note: "a box under the stairs"
---
The server.
""",
    'web': """---
bean: web
genos: instance
title: "web on box"
status: active
summary: "the web service, running on box"
nature: lekton
identity:
  status: confirmed
  anchors:
    - { key: identifier, value: "instance:web", class: logical, establishing: true }
provenance: { src: inferred, by: "agent:a-model/core-test", as_of: 2026-09-20 }
owned_by: { from: { bean: box } }
lives_in: { bean: box }
instance_of: { bean: webapp }
depends_on:
  storage: { bean: box, necessity: necessary }
consumes:
  - { bean: box }
reaches:
  backup: { protocol: ssh, to: { bean: box } }
---
""",
    'webapp': """---
bean: webapp
genos: product
title: "webapp"
status: active
summary: "a web application"
nature: lekton
identity: { status: confirmed, anchors: [ { key: identifier, value: "product:webapp", class: logical, establishing: true } ] }
provenance: { src: asserted-by-human, by: "sam", as_of: 2026-09-20 }
owned_by: { owner: { bean: sam } }
via:
  - { bean: sam }
---
""",
    'site': """---
bean: site
genos: domain
title: "site.example"
status: active
summary: "a domain the registry owns, sam answering for it"
nature: lekton
identity:
  status: confirmed
  anchors:
    - { key: fqdn, value: "site.example", class: logical, establishing: true }
    - { key: content_hash, value: "sha256:9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08", class: logical, establishing: true }
provenance: { src: observed, by: "sam", as_of: 2026-09-20 }
owned_by: { external: "the registry of .example" }
responsibility: { legal: { holder: { bean: sam } } }
---
""",
    'loan': """---
bean: loan
genos: contract
title: "a loan"
status: active
summary: "sam lent ana ten"
nature: lekton
identity: { status: confirmed, anchors: [ { key: identifier, value: "contract:loan", class: logical, establishing: true } ] }
provenance: { src: asserted-by-human, by: "sam", as_of: 2026-09-20 }
owned_by: { crown: true }
parties:
  sam: { who: { bean: sam }, role: lender, accepted: 2026-09-20 }
  ana: { external: "ana, a neighbour", role: borrower, accepted: 2026-09-20 }
  guarantor: { external: "a friend of ana", role: guarantor }
words: { form: spoken, note: "agreed at the door" }
over:
  cash: { what: "ten in cash" }
clauses:
  repay: { what: "repay the ten", by: ana, permission: required, due: 2026-12-31 }
transactions:
  lent: { what: "ten in cash", amount: { count: 10, unit: XTS }, day: 2026-09-20, paid_by: [ { party: sam } ], borne_by: [ { party: ana, share: 1 } ] }
---
""",
    'session-a': """---
bean: session-a
genos: session
title: "a session"
status: closed
summary: "one stretch of work"
nature: lekton
identity: { status: confirmed, anchors: [ { key: identifier, value: "session:session-a", class: logical, establishing: true } ] }
provenance: { src: observed, by: "agent:a-model/core-test", as_of: 2026-09-20 }
owned_by: { owner: { bean: sam } }
timing:
  start: { system: gregorian-civil, at: "2026-09-20 09:00+03:30", unit: minute }
  stop:  { system: gregorian-civil, at: "2026-09-20 11:30+03:30", unit: minute }
workspace: { host: box, system: unix-filesystem, at: "box:/srv/work", branch: main, opened_at: "2026-09-20 09:00+03:30" }
---
""",
    'note-b': """---
bean: note-b
genos: document
title: "a note"
status: active
summary: "read the day after, in no session"
nature: lekton
identity: { status: confirmed, anchors: [ { key: identifier, value: "document:note-b", class: logical, establishing: true } ] }
provenance: { src: observed, by: "agent:a-model/core-test, reading the share", as_of: 2026-09-21 }
owned_by: { owner: { bean: sam } }
---
""",
}
MAPPING = """---
mapping: restore
kind: procedure
title: "restore box"
summary: "bring box back from its copy"
provenance: { src: asserted-by-human, by: "sam", as_of: 2026-09-20 }
trigger: "the data volume is lost"
produces: "box, serving its shares again"
tool: "rsync"
steps:
  - "mount the copy"
  - "rsync it back"
---
"""
JOURNAL = """# Journal

## 2026-09-20 10:00+03:30 · sam · the garden's first beans
- action: wrote [[sam]], [[box]], [[web]], [[webapp]], [[site]], [[loan]], [[session-a]] and the mapping restore.

## 2026-09-21 12:00+03:30 · sam · a note
- action: wrote [[note-b]].
"""

T = tempfile.mkdtemp(prefix='dmcoretr-')
G, C = os.path.join(T, 'g'), os.path.join(T, 'copy')
try:
    for d in ('beans', 'mappings', 'log', 'seed'):
        os.makedirs(os.path.join(G, d))
    for bid, text in BEANS.items():
        with open(os.path.join(G, 'beans', bid + '.md'), 'w', encoding='utf-8') as fh:
            fh.write(text)
    with open(os.path.join(G, 'mappings', 'restore.md'), 'w', encoding='utf-8') as fh:
        fh.write(MAPPING)
    with open(os.path.join(G, 'log', 'journal.md'), 'w', encoding='utf-8') as fh:
        fh.write(JOURNAL)
    with open(os.path.join(G, 'GARDEN.md'), 'w', encoding='utf-8') as fh:
        fh.write("---\ngarden: core-translate\nextends: std-vocab@32.0\ngardener: sam\nzone: Asia/Tehran\n---\n")
    with open(os.path.join(G, 'VOCAB.md'), 'w', encoding='utf-8') as fh:
        fh.write("---\nvocab: core-translate\nextends: std-vocab@32.0\nregistry_additions:\n  units:\n"
                 "    - { unit: gigabyte-per-day, quantity: data-rate, factor: [312500, 27] }\n"
                 "    - { unit: rack-unit, quantity: length, factor: [889, 20000] }\n"
                 "vacancies:\n"
                 "  - { at: 'registry:units', position: gigabyte-per-day, reason: prediction, why: 'the rate of a backup, to come' }\n"
                 "  - { at: 'registry:units', position: rack-unit, reason: prediction, why: 'a rack, to come' }\n---\n")
    shutil.copy(os.path.join(ROOT, 'seed', 'std-vocab.md'), os.path.join(G, 'seed', 'std-vocab.md'))
    shutil.copytree(os.path.join(ROOT, 'seed', 'knowledge'), os.path.join(G, 'seed', 'knowledge'))
    before = {p: open(os.path.join(G, p), encoding='utf-8').read() for p in
              [f"beans/{b}.md" for b in BEANS] + ['mappings/restore.md', 'VOCAB.md']}

    r = subprocess.run([PY, os.path.join(ROOT, 'core', 'translate.py'), 'garden', G, C], capture_output=True, text=True,
                       encoding='utf-8')
    last = r.stdout.strip().split('\n')[-1]
    check("the garden is translated into a copy with nothing lost: every value placed and found there, every comment kept",
          r.returncode == 0 and '— 0 problem(s)' in last and '9 beans' in last, r.stdout + r.stderr)
    n = int(last.split('; ')[1].split(' values')[0])
    placed = int(last.split('values, ')[1].split(' placed')[0])
    check(f"...the count: {n} values before, {placed} placed", n == placed and n > 150, last)
    check("...2 comment lines kept", '2 comment lines kept' in last, last)
    r = subprocess.run([PY, os.path.join(ROOT, 'core', 'check.py'), C], capture_output=True, text=True, encoding='utf-8')
    check("the core's engine passes the copy", r.returncode == 0 and '— 0 error(s)' in r.stdout, r.stdout)
    check("the garden itself is untouched",
          all(open(os.path.join(G, p), encoding='utf-8').read() == t for p, t in before.items()))
    r = subprocess.run([PY, os.path.join(ROOT, 'core', 'translate.py'), 'garden', G, C], capture_output=True, text=True,
                       encoding='utf-8')
    check("a copy that exists already is refused, never written over", r.returncode != 0 and 'exists' in r.stdout + r.stderr,
          r.stdout + r.stderr)

    def st(bid, d='beans'):
        fm, _b = read.document(os.path.join(C, d, bid + '.md'))
        return fm, [(next(iter(s)), next(iter(s.values()))) for s in fm.get('statements') or []]
    fm, box = st('box')
    verbs = [v for v, _r in box]
    has = lambda v, **kw: any(vv == v and all(r.get(k) == x for k, x in kw.items()) for vv, r in box)  # noqa: E731
    check("provenance → a knowing act at the moment of the entry naming the bean; an agent's is its session's, the one "
          "whose start and stop hold that moment, and its reading is `derive`; the agent's prose its note",
          box[0][0] == 'derive' and box[0][1].get('at') == '2026-09-20 10:00+03:30' and box[0][1].get('by') == 'session-a'
          and box[0][1].get('from') == 'unknown' and 'agent:a-model' in box[0][1].get('note', ''), box[0])
    _fm, nb = st('note-b')
    check("...an agent's act no session holds is `read` by `unknown`, its prose the note",
          nb[0][0] == 'read' and nb[0][1].get('by') == 'unknown' and nb[0][1].get('at') == '2026-09-21 12:00+03:30'
          and 'reading the share' in nb[0][1].get('note', ''), nb[0])
    check("identity → name, by the anchor's key as a namespace", has('name', by='anchor-serial', of='self', **{'as': 'SN-0042'}), box)
    check("owned_by → own; responsibility → answer, before the law the owner's derived and not written",
          has('own', by='sam', of='self') and has('answer', by='sam', **{'as': 'keeping'}) and not has('answer', **{'as': 'law'}), box)
    check("via → come; located_at → be, a position in its system's one form",
          has('come', by='self') and has('be', at='192.0.2.10', **{'as': 'location'}) and has('be', at='box:/srv/data'), box)
    check("endpoints → serve at an address and a port; roles → do; knowledge → use and classify",
          has('serve', at=['192.0.2.10', 'tcp-port:22'], through='ssh') and has('do', **{'as': 'file-server'})
          and has('use', of='technology:rsync') and has('classify', **{'as': 'isco-08:2511'}), box)
    check("risks → fail; capabilities → can, forbidden and possible", has('fail', id='disk-full', at='2026-09-20')
          and has('can', id='ip-forwarding') and 'forbidden' in verbs and 'possible' in verbs, box)
    d = fm.get('details') or {}
    check("what fits no verb is kept whole in details: refs, open, owns, status; the old details' own keys; the comments",
          d.get('refs', {}).get('rack', {}).get('rel') == 'kept-by' and d.get('open') == ['label the second disk']
          and d.get('owns') == {'shares': 'projects and archive'} and d.get('status') == 'active'
          and d.get('note') == 'a box under the stairs' and len(d.get('comments') or []) == 2, d)
    check("...and what is left of an entry a verb took stays under its statement's id; what a placement holds there is "
          "its form, `placed` (v1 part 7)",
          d.get('risks', {}).get('disk-full', {}).get('severity') == 'medium'
          and any(v == 'be' and (r.get('placed') or {}).get('openness') == 'elsewhere' for v, r in box), (d, box))
    _fm, web = st('web')
    wv = {v for v, _r in web}
    check("inferred → derive, its source unknown; lives_in → be as habitat; instance_of → run; depends_on, consumes, reaches → need",
          web[0][0] == 'derive' and web[0][1].get('from') == 'unknown' and {'be', 'run', 'need'} <= wv
          and any(v == 'own' and r.get('from') == 'box' for v, r in web), web)
    _fm, loan = st('loan')
    lv = [v for v, _r in loan]
    check("parties, over and words → agree; clauses → can, obligatory through the agreement; transactions → pay and bear",
          lv.count('agree') == 2 and 'obligatory' in lv and 'pay' in lv and 'bear' in lv
          and any(v == 'agree' and r.get('by') == 'unknown' and r.get('note') == 'ana, a neighbour' for v, r in loan)
          and any(v == 'pay' and r.get('of') == {'count': '10', 'unit': 'XTS'} for v, r in loan), loan)
    _fm, ses = st('session-a')
    check("timing start and stop → be, present over the extent; workspace.opened_at → open",
          any(v == 'be' and r.get('at') == '2026-09-20 09:00+03:30/2026-09-20 11:30+03:30' and r.get('as') == 'presence'
              for v, r in ses) and any(v == 'open' for v, r in ses), ses)
    mfm, mp = st('restore', 'mappings')
    check("a mapping is a bean of its kind, its steps and trigger kept in details; what it produces is `produce`",
          mfm.get('bean') == 'restore' and mfm.get('kind') == 'procedure' and mp[0][0] == 'say'
          and mfm.get('details', {}).get('steps') == ['mount the copy', 'rsync it back']
          and ('produce', {'id': 'produces', 'by': 'self', 'of': ['box, serving its shares again']}) in mp, mp)
    site = [next(iter(x.items())) for x in read.document(os.path.join(C, 'beans', 'site.md'))[0]['statements']]
    web = [next(iter(x.items())) for x in read.document(os.path.join(C, 'beans', 'web.md'))[0]['statements']]
    loan = [next(iter(x.items())) for x in read.document(os.path.join(C, 'beans', 'loan.md'))[0]['statements']]
    check("the guides' forms: an fqdn that establishes is a name `dns` gives, a content hash the bare digest `sha-256` "
          "gives; a name the garden minted for the bean itself is the bean, and no statement; an owner outside the "
          "ledger is someone nobody named here; and a party with no acceptance on record is no `agree`",
          ('name', {'id': 'fqdn', 'by': 'dns', 'of': 'self', 'as': 'site.example'}) in site
          and any(v == 'name' and r.get('by') == 'sha-256' and r.get('as', '').startswith('9f86') for v, r in site)
          and not any(v == 'name' for v, r in web)
          and any(v == 'own' and r.get('by') == {'someone': 'org'} for v, r in site)
          and sum(1 for v, _r in loan if v == 'agree') == 2, (site, web, loan))
    v2 = read.document(os.path.join(C, 'VOCAB.md'))[0]
    check("VOCAB.md gains the garden's rows: the mapping's kind, and the namespaces its names are given in",
          {'kind': 'procedure', 'nature': 'sayable'} in v2.get('kinds', [])
          and {'namespace': 'anchor-serial', 'once': 'true'} in v2.get('namespaces', []), v2)
    check("...and its own units: in UCUM where their names are made of the law's (gigabyte-per-day is GBy/d), else the "
          "name kept as the code, saying why; a unit the garden said is vacant stays so, with its reason",
          {'unit': 'GBy/d', 'name': 'gigabyte-per-day', 'quantity': 'data-rate',
           'vacant': 'prediction: the rate of a backup, to come'} in v2.get('units', [])
          and any(u.get('unit') == 'rack-unit' and u.get('ucum') == 'false' and u.get('why') for u in v2.get('units', [])),
          v2.get('units'))

    # A VALUE TAKEN OUT IS SEEN: the proof reads the written bean back
    text, b = translate.translate_bean(os.path.join(G, 'beans', 'box.md'), 'beans/box.md',
                                       translate.Context(G, Law.load(), standards.here()))
    check("the proof of one bean finds nothing missing", translate.verify(b, text) == [], translate.verify(b, text))
    cut = text.replace("    shares: projects and archive\n", "")
    probs = translate.verify(b, cut)
    check("...and a value taken out of the written bean is reported as not where it was put",
          any('owns.shares' in p for p in probs), probs)
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\ncore_translate: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
