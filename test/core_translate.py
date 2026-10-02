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
sys.path.append(os.path.join(ROOT, 'test'))
import grow  # noqa: E402

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
    # WHAT PART 12b CARRIES: an agent, a party that declined, a payment charged in another currency settling one
    # occurrence of a clause, grants over readings and of part of a bean, a weighing; a host's channels, links, a reach,
    # treatments, a reading disputed and heard, a boundary it marks; a member who agreed (v1 part 12b)
    'cem': """---
bean: cem
genos: person
title: "Cem"
status: active
summary: "a member of the club"
nature: soma
identity: { status: confirmed, anchors: [ { key: identifier, value: "person:cem", class: logical, establishing: true } ] }
provenance: { src: asserted-by-human, by: "sam", as_of: 2026-09-20 }
owned_by: { crown: true }
---
""",
    'club': """---
bean: club
genos: contract
title: "a club"
status: active
summary: "a reading club"
nature: lekton
identity: { status: confirmed, anchors: [ { key: identifier, value: "contract:club", class: logical, establishing: true } ] }
provenance: { src: asserted-by-human, by: "sam", as_of: 2026-09-20 }
owned_by: { crown: true }
parties:
  sam: { who: { bean: sam }, role: host, accepted: 2026-09-20 }
  cem: { who: { bean: cem }, role: member, accepted: 2026-09-20 }
  aide: { external: "cem's aide", role: member, acting_for: cem, accepted: 2026-09-20 }
  dora: { external: "a neighbour", role: member, declined: 2026-09-21 }
words: { form: spoken }
clauses:
  fee: { what: "each member pays a fee for each book", by_role: member, permission: required, each: books }
transactions:
  repairs: { what: "the shelves mended", amount: { count: "100.00", unit: TRY }, day: 2026-09-23, paid_by: [ { party: sam } ], analytic_distribution: [ { code: "analytic:orchard", share: 60 }, { code: "analytic:workshop", share: 40 } ] }
  paid: { what: "the first fee", amount: { count: "10.00", unit: USD }, charged: { count: "9.25", unit: EUR }, day: 2026-09-22, paid_by: [ { party: cem } ], settles: [ { clause: fee, occurrence: box, amount: { count: "10.00", unit: USD } } ] }
selections:
  books: { what: "the books", steps: [ { id: b, op: select, genos: document } ] }
  members: { what: "the members", steps: [ { id: m, op: select, genos: person } ] }
grants:
  members-read: { act: read, over: books, positions: [ { path: title }, { path: observations } ], audience: { selection: members }, reason: asked, why: "members read the books' titles and readings" }
  no-sites: { act: read, over: books, positions: [ { path: located_at } ], audience: { who: cem }, permission: forbidden, why: "where a book is kept is the club's" }
  wide: { act: read, over: books, positions: [ { path: identity.anchors } ], audience: { who: cem }, why: "a part the core has no word for: kept whole, opening nothing" }
weighings:
  picks: { for: improvements, judge: sam, criteria: [ { name: short, what: "read in a month" }, { name: new, what: "new to the club" }, { name: cheap, what: "costs little" } ], pairwise: [ { a: short, b: new, judged: "2" }, { a: short, b: cheap, judged: "4" }, { a: new, b: cheap, judged: "2" } ] }
---
""",
    'edge': """---
bean: edge
genos: host
title: "edge"
status: active
summary: "the club's router"
nature: soma
identity: { status: confirmed, anchors: [ { key: serial, value: "EDGE-1", class: hardware, establishing: true } ] }
provenance: { src: asserted-by-human, by: "sam", as_of: 2026-09-20 }
owned_by: { owner: { bean: sam } }
endpoints:
  - { protocol: smtp, system: ipv4, at: 192.0.2.30, port: "25", exposure: link, confidentiality: cleartext, permission: required, plane: data, observed: 2026-09-20, via_link: wg0 }
  - { protocol: ssh, system: unix-filesystem, at: "edge:/run/ssh.sock", exposure: loopback, confidentiality: encrypted }
links:
  wan: { protocol: pppoe, confidentiality: cleartext, observed: 2026-09-20 }
  wg0: { protocol: wireguard, peer: { bean: box, field: lan_ip }, carried_by: wan, confidentiality: encrypted, observed: 2026-09-20 }
reaches:
  dns: { protocol: dns, to: { bean: box }, necessity: necessary, via_link: wg0 }
treatments:
  - { kind: nat, what: "port 25 to box", to: { bean: box, field: lan_ip }, permission: required, why: "mail stops arriving", observed: 2026-09-20 }
  - { kind: mangle, what: "mark mail going out", why: "the sender's name fails" }
  - { kind: route, what: "default via the wan", why: "nothing leaves" }
observations:
  weight: { property: mass, value: { count: "1.2", unit: kilogram }, at: 2026-09-22, by: sam }
  second: { answers: "edge:observations.weight", answer: disputes, by: cem, at: 2026-09-23 }
hearings:
  weight: { over: [ { path: "edge:observations.weight" }, { path: "edge:observations.second" } ], heard: [ { speaker: sam, said: "I weighed it", at: 2026-09-24 }, { speaker: cem, said: "the scale was off", at: 2026-09-24 } ], ruling: { by: sam, what: "weigh it again", at: 2026-09-24 } }
fixes:
  meghalayan: { system: ics-chronostrat, boundary: Meghalayan, level: "EPSG:4326;25.262222,91.715" }
---
""",
}
INTAKE = """---
mapping: intake
kind: checklist
title: "intake"
summary: "what a member brings"
provenance: { src: asserted-by-human, by: "sam", as_of: 2026-09-20 }
items:
  - { id: card, do: "a library card", by: member }
  - { id: id-a, do: "a passport", by: member, one_of: identity }
  - { id: id-b, do: "an identity card", by: member, one_of: identity }
  - { id: fee-paid, do: "the first fee", by: member, needed_when: "club:members", met_by: "club:books" }
---
"""
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
- action: wrote [[cem]], [[club]], [[edge]] and the mapping intake (v1 part 12b).

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
    with open(os.path.join(G, 'mappings', 'intake.md'), 'w', encoding='utf-8') as fh:
        fh.write(INTAKE)
    with open(os.path.join(G, 'log', 'journal.md'), 'w', encoding='utf-8') as fh:
        fh.write(JOURNAL)
    with open(os.path.join(G, 'GARDEN.md'), 'w', encoding='utf-8') as fh:
        fh.write("---\ngarden: core-translate\nextends: std-vocab@32.0\ngardener: sam\nzone: Asia/Tehran\n---\n")
    with open(os.path.join(G, 'VOCAB.md'), 'w', encoding='utf-8') as fh:
        fh.write("---\nvocab: core-translate\nextends: std-vocab@32.0\nextends_profiles: [knowledge, network, accounting]\n"
                 "registry_files:\n  - { registry: analytic, file: extracts/analytic.tsv, key: code }\n"
                 "registry_additions:\n  knowledge_schemes:\n"
                 "    - { scheme: analytic, classifies: \"where the club's money goes\", holding: extract, licence: CC0-1.0, "
                 "publisher: the club, url: \"https://example.org/analytic\", levels: [ { level: plan }, { level: account } ], "
                 "neighbours: none, sources: extracts/analytic.tsv }\n"
                 "  units:\n"
                 "    - { unit: gigabyte-per-day, quantity: data-rate, factor: [312500, 27] }\n"
                 "    - { unit: rack-unit, quantity: length, factor: [889, 20000] }\n"
                 "vacancies:\n"
                 "  - { at: 'registry:units', position: gigabyte-per-day, reason: prediction, why: 'the rate of a backup, to come' }\n"
                 "  - { at: 'registry:units', position: rack-unit, reason: prediction, why: 'a rack, to come' }\n---\n")
    os.makedirs(os.path.join(G, 'extracts'))
    with open(os.path.join(G, 'extracts', 'analytic.tsv'), 'w', encoding='utf-8') as fh:
        fh.write("code\tlevel\tparent\tname\nprojects\tplan\t\tProjects\norchard\taccount\tprojects\tThe orchard\n"
                 "workshop\taccount\tprojects\tThe workshop\n")
    grow.today_file('seed/std-vocab.md', os.path.join(G, 'seed', 'std-vocab.md'))   # today's law, the garden's own copy
    shutil.copytree(os.path.join(ROOT, 'seed', 'knowledge'), os.path.join(G, 'seed', 'knowledge'))
    before = {p: open(os.path.join(G, p), encoding='utf-8').read() for p in
              [f"beans/{b}.md" for b in BEANS] + ['mappings/restore.md', 'VOCAB.md']}

    r = subprocess.run([PY, os.path.join(ROOT, 'core', 'translate.py'), 'garden', G, C], capture_output=True, text=True,
                       encoding='utf-8')
    last = r.stdout.strip().split('\n')[-1]
    check("the garden is translated into a copy with nothing lost: every value placed and found there, every comment kept",
          r.returncode == 0 and '— 0 problem(s)' in last and '13 beans' in last, r.stdout + r.stderr)
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
    # WHAT PART 12b CARRIES
    _fm, club = st('club')
    one = lambda xs, v, **kw: [r for vv, r in xs if vv == v and all(r.get(k) == x for k, x in kw.items())]  # noqa: E731
    check("acting_for → represent; declined → its `agree` offered and its `decline`, the day said (v1 part 12b)",
          one(club, 'represent', by='unknown', of='cem') and one(club, 'decline', by='unknown', at='2026-09-21')
          and one(club, 'decline')[0].get('of') in [r.get('id') for r in one(club, 'agree', by='unknown')], club)
    check("charged → the payment's `charged`; settles → its `settles`, each occurrence of a clause by its id",
          one(club, 'pay', id='paid', charged={'count': '9.25', 'unit': 'EUR'},
              settles=[{'clause': 'fee', 'occurrence': 'box', 'amount': {'count': '10.00', 'unit': 'USD'}}]), club)
    check("grants → grant: over a reading its `of`, to the members of one its `to`, the parts it opens and the reason it "
          "asks its `cover`; one forbidden a ceiling; one whose part the core has no word for kept whole in details",
          one(club, 'grant', id='members-read', to=['members'], of=['books'], cover={'parts': ['title', 'measure'],
                                                                                    'reason': 'asked'})
          and one(club, 'grant', id='no-sites', to=['cem'], cover={'parts': ['be.location']})
          and one(club, 'forbidden', of='no-sites') and not one(club, 'grant', id='wide')
          and 'wide' in (_fm.get('details') or {}).get('grants', {}), club)
    check("analytic_distribution → book: each account the payment is booked to, in a share (the accounting profile)",
          one(club, 'book', of='repairs', to='analytic:orchard', share='60')
          and one(club, 'book', of='repairs', to='analytic:workshop', share='40'), club)
    check("weighings → weigh, by the judge, to what it orders, its criteria and judgments its form",
          one(club, 'weigh', id='picks', by='sam', to='improvements') and
          len(one(club, 'weigh')[0]['weighing'].get('pairwise') or []) == 3, club)
    _fm, edge = st('edge')
    smtp = one(edge, 'serve', through='smtp')
    check("endpoints → serve and its channel (exposure, confidentiality, plane, the day checked); a permission its "
          "position on the square; a socket path a position with no port",
          smtp and smtp[0].get('channel') == {'exposure': 'link', 'confidentiality': 'cleartext', 'plane': 'data',
                                              'observed': '2026-09-20'}
          and one(edge, 'obligatory', of=smtp[0].get('id'), through='unknown')
          and one(edge, 'serve', through='ssh', at=['edge:/run/ssh.sock']), edge)
    check("links → carry, through the protocol, to the other end; what rides a link is its `of` (carried_by, via_link)",
          one(edge, 'carry', id='wan', through='pppoe', of=['wg0']) and
          one(edge, 'carry', id='wg0', through='wireguard', to='box') and
          set(one(edge, 'carry', id='wg0')[0].get('of') or []) == {smtp[0].get('id') if smtp else None, 'reaches-dns'},
          edge)
    check("reaches → need and how badly, a position on the necessity square; treatments → translate, route as a mark, "
          "route", one(edge, 'necessary', of='reaches-dns', through='self')
          and one(edge, 'translate', to='box', **{'from': 'unknown'}) and one(edge, 'route', **{'as': 'mangle'})
          and one(edge, 'route', of='default via the wan', to='unknown'), edge)
    check("observations → measure; one answering another → respond, its verdict; a hearing → respond in each side's "
          "words, and the ruling a rule; fixes → mark",
          one(edge, 'measure', id='weight', by='sam', value={'count': '1.2', 'unit': 'kg'})
          and one(edge, 'respond', id='second', by='cem', of=['weight'], **{'as': 'disputes'})
          and len(one(edge, 'respond', of=['weight', 'second'])) == 2
          and one(edge, 'rule', by='sam', of=['weight', 'second'], note='weigh it again')
          and one(edge, 'mark', of='ics:Meghalayan'), edge)
    _fm, intake = st('intake', 'mappings')
    check("items → need, from whom, alternatives sharing an `as`, needed while a reading holds; met_by → meet",
          one(intake, 'need', id='card', of='a library card', **{'from': 'member'})
          and len(one(intake, 'need', **{'as': 'identity'})) == 2
          and one(intake, 'need', id='fee-paid', **{'while': 'club#members'})
          and one(intake, 'meet', by='club#books', of='fee-paid'), intake)
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
          "name kept as the code, saying why, each with the factor it said; a unit the garden said is vacant stays so, "
          "with its reason",
          {'unit': 'GBy/d', 'name': 'gigabyte-per-day', 'quantity': 'data-rate', 'factor': ['312500', '27'],
           'vacant': 'prediction: the rate of a backup, to come'} in v2.get('units', [])
          and any(u.get('unit') == 'rack-unit' and u.get('ucum') == 'false' and u.get('why') for u in v2.get('units', [])),
          v2.get('units'))
    vt = open(os.path.join(C, 'VOCAB.md'), encoding='utf-8').read()
    old_v = translate.dmparse.loads(translate.dmparse.split_front_matter(open(os.path.join(G, 'VOCAB.md'),
                                                                               encoding='utf-8').read())[0])
    check("...its front matter the core's rows alone, today's keys none of them; today's front matter kept whole in its "
          "body, read by no rule (v1 part 13b)",
          set(v2) <= {'kinds', 'namespaces', 'units', 'profiles', 'schemes', 'files', 'systems', 'tables'}
          and translate.kept_words(vt) == old_v and 'registry_additions' in old_v, sorted(v2))

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
