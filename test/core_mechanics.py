#!/usr/bin/env python3
"""core_mechanics — the mechanics (core 4.2): the core's verb `join` and its tables, the made scheme of concepts, the one
matcher `fits` calls for a concept, and the law's refusal of a second row of one signature.

- the law: the core's compliances (4), pairs (13, each lower pair with the freedoms it leaves) and closures (5); `join`'s
  row; the made scheme, shipped, at device and component, of the knowledge profile's form `concept`: 46 rows, 13 forms
  and 33 roles, each pattern in its form and no two of one signature; the codes of machine-elements.tsv (0mit/daftar#264)
  kept on the rows of the same concepts; the law's proof reads no problem of them;
- the signature: a copy of a row under new names of its nodes is the row; one limit more is another concept of the same
  topology; three groups of one topology are told apart by their limits alone;
- the self-check: `core/check.py --law` refuses a second row of one signature, and each fault of a pattern's form;
- the matcher on the generic seed (test/mechanics-seed.yaml): every concept tried on every node, each fit expected found
  and none unexpected — a role of the least whole, an absence never read of a body not drawn whole; the held-out pump,
  written after the concepts, the same;
- a garden: joints written with `join` stand; a join of a sayable, by a pair or a closure the core has not, or with no
  `to`, is refused by rule valency; a concept said of a being whose root it is known not to fit is refused by rule
  bearer — a device's of one body, one body's of a device, a body's own of a fiat part — and one said where nothing
  drawn contradicts it stands; a reading's `fits: {concept: ...}` selects the beings said to be of it, as the store's
  SQL does, and a drawing of the garden reads a role a garden cannot draw yet nowhere (no compliance, no feature's kind
  is said); a garden's own scheme of concepts is held to the form beside the release's, a row of the release's
  signature refused by rule profile.

Run: python3 test/core_mechanics.py   (0 = green)
"""
import os, shutil, subprocess, sys, tempfile

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, 'bin')):
    sys.path.insert(0, _p)
from core import engine, lines, mechanics, read, reckon  # noqa: E402
from core.law import Law  # noqa: E402

FAILS = []
PY = sys.executable
LAW_DIR = os.path.join(ROOT, 'core', 'law')
CASES = read.data(os.path.join(ROOT, 'test', 'core-cases.yaml'))
LAW = Law.load(('VOCAB.md', CASES['vocab']))
T = tempfile.mkdtemp(prefix='core-mechanics-')


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:1500]))
    if not cond:
        FAILS.append(name)


def drawing_of(asm):
    """A drawing of one assembly of the seed, written as the matcher reads one: each fact the fixture states."""
    nodes = []
    for nid, a in asm['nodes'].items():
        n = mechanics.Node(nid, device=bool(a.get('device')), compliance=a.get('compliance'),
                           features={k: {kk: str(vv) for kk, vv in f.items()} for k, f in a['features'].items()}
                           if a.get('features') is not None else None,
                           limits={k: str(a[k]) for k in mechanics.LIMITS if k in a},
                           said={f"made:{a['said']}"} if a.get('said') else (), whole=not a.get('external'),
                           fiat_of=a.get('fiat_of'))
        n.parts, n.fiat = list(a.get('parts') or []), list(a.get('fiat') or [])
        nodes.append(n)
    joints = []
    for j in asm['joints']:
        (x, _, xf), (y, _, yf) = (str(j[0]).partition('#'), str(j[1]).partition('#'))
        joints.append({'x': x, 'xf': xf or None, 'y': y, 'yf': yf or None, 'pair': j[2], 'closures': list(j[3])})
    return mechanics.Drawing(nodes, joints)


def fits_all(asms, M, codes):
    """(expected found, said among them, unexpected, missed, lines) of every concept tried on every node."""
    tp = said = 0
    extra, miss = [], []
    for name, asm in asms.items():
        d = drawing_of(asm)
        for nid, a in asm['nodes'].items():
            got = {c: r for c in codes if (r := M.fits(d, nid, c))}
            want = {f"made:{c}" for c in a.get('expect') or []}
            tp += len(want & set(got))
            said += sum(1 for c in want & set(got) if got[c] == 'said')
            extra += [f"{name}.{nid}: {c}" for c in sorted(set(got) - want)]
            miss += [f"{name}.{nid}: {c}" for c in sorted(want - set(got))]
    return tp, said, extra, miss


try:
    # ---- THE LAW
    verbs = read.data(os.path.join(LAW_DIR, 'verbs.yaml'))
    check("the core's compliances: rigid, elastic, tension, pressure",
          [r['compliance'] for r in verbs['compliances']] == ['rigid', 'elastic', 'tension', 'pressure'])
    pairs = {r['pair']: r for r in verbs['pairs']}
    check("the core's 13 pairs, each lower pair with the rotations and translations it leaves, the five higher marked",
          list(pairs) == ['fixed', 'revolute', 'prismatic', 'cylindrical', 'helical', 'spherical', 'planar', 'universal',
                          'rolling', 'meshing', 'cam', 'wrapping', 'pressing']
          and (pairs['fixed']['r'], pairs['fixed']['t'], pairs['spherical']['r'], pairs['planar']['t']) == ('0', '0', '3', '2')
          and pairs['helical'].get('coupled') == 'true'
          and [p for p, r in pairs.items() if r.get('higher') == 'true'] == ['rolling', 'meshing', 'cam', 'wrapping', 'pressing']
          and all(('r' in r) != (r.get('higher') == 'true') for r in pairs.values()), pairs)
    check("the core's closures: form, force, friction, material, chain",
          [r['closure'] for r in verbs['closures']] == ['form', 'force', 'friction', 'material', 'chain'])
    j = LAW.verbs['join']
    check("`join`, a verb of the core: two bodies (by, to), at their features, as a pair, its closures a qualifier",
          j['home'] == 'core' and j['required'] == ['by', 'to', 'as']
          and j['roles']['by'] == {'shape': 'being', 'nature': ['body']} and j['roles']['to'] == j['roles']['by']
          and j['roles']['at'] == {'shape': 'position', 'many': 'true'}
          and j['roles']['as'] == {'shape': 'row', 'table': 'pairs'}
          and j['qualifiers']['closure'] == {'shape': 'row', 'table': 'closures', 'many': 'true'}, j)
    check("the tables are the law's: a pair, a closure, a compliance are rows of them",
          LAW.has('pairs', 'wrapping') == '' and LAW.has('closures', 'material') == '' and LAW.has('compliances', 'tension') == ''
          and LAW.has('pairs', 'glued') != '')
    reg = read.data(os.path.join(LAW_DIR, 'registries.yaml'))
    made = next(r for r in reg['knowledge_schemes'] if r['scheme'] == 'made')
    check("the made scheme: shipped, CC BY 4.0, at device and component, its levels form and role, of the form `concept`",
          made['holding'] == 'shipped' and made['licence'] == 'CC-BY-4.0' and made['at'] == ['device', 'component']
          and made['levels'] == [{'level': 'form'}, {'level': 'role'}] and made['form'] == 'concept', made)
    C = LAW.concepts()
    check("its 46 concepts: 13 forms and 33 roles", len(C) == 46
          and sum(r['level'] == 'form' for r in C.values()) == 13 and sum(r['level'] == 'role' for r in C.values()) == 33,
          len(C))
    p = subprocess.run([PY, 'core/check.py', '--law'], cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
    check("the law's proof reads no problem of them", p.returncode == 0 and '0 error(s)' in p.stdout, p.stdout[-800:])
    check("no form problem, no second signature", not LAW.form_problems(), LAW.form_problems()[:4])
    cw = {c.split(':')[1]: (r.get('wikidata'), r.get('etim'), r.get('cpv')) for c, r in C.items()}
    check("the crosswalk of machine-elements.tsv kept on its concepts' rows, a word of one concept on one row",
          cw['pulley'] == (['Q48378', 'Q1057381'], 'EC003882', '42141400') and cw['bush'] == ('Q12832024', None, None)
          and cw['o-ring'] == ('Q942417', 'EC010584', '44425200') and cw['circlip'] == ('Q2144243', 'EC002383', None)
          and cw['hydraulic-cylinder'] == ('Q2318337', 'EC012253', '42121100')
          and 'sheave' in C['made:pulley']['synonyms'] and 'bushing' in C['made:bush']['synonyms'], cw)
    check("no family a role is: transmission, bearing, seal, fastener, fluid power, damping are what bodies do",
          not {f"made:{x}" for x in ('transmission', 'bearing', 'seal', 'fastener', 'fluid-power', 'damping')} & set(C))

    # ---- THE SIGNATURE
    rr = C['made:retaining-ring']['pattern']
    ren = {'G': 'Q', 'R': 'Z'}
    renamed = {'root': rr['root'], 'nodes': {ren[k]: v for k, v in rr['nodes'].items()},
               'edges': [dict(e, x=ren.get(e['x'], e['x']), y=ren.get(e['y'], e['y'])) for e in reversed(rr['edges'])]}
    limited = dict(rr, root={'shape': 'wire-ring'})
    check("a copy of a row under new names of its nodes, its edges in another order, is the row: one signature",
          mechanics.signature(renamed) == mechanics.signature(rr))
    check("one limit more is another concept, of the same topology",
          mechanics.signature(limited) != mechanics.signature(rr)
          and mechanics.signature(limited, limits=False) == mechanics.signature(rr, limits=False))
    tops = {}
    for c, r in C.items():
        tops.setdefault(mechanics.signature(r['pattern'], limits=False), []).append(c.split(':')[1])
    groups = sorted(sorted(v) for v in tops.values() if len(v) > 1)
    check("three groups of one topology, told apart by their limits alone: seals by section, belts by section, pulleys "
          "by what they are on", groups == [['crankshaft-pulley', 'power-steering-pump-pulley', 'water-pump-pulley'],
                                            ['lip-seal', 'o-ring', 'x-ring'], ['poly-v-belt', 'v-belt']], groups)
    check("46 distinct signatures", len({mechanics.signature(r['pattern']) for r in C.values()}) == 46)

    # ---- THE SELF-CHECK, planted in a copy of the release
    tree = os.path.join(T, 'tree')
    shutil.copytree(ROOT, tree, ignore=shutil.ignore_patterns('.git', '__pycache__', 'node_modules'))
    with open(os.path.join(tree, 'seed', 'knowledge', 'made.yaml'), 'a', encoding='utf-8') as fh:
        fh.write("  - code: snap-ring-copy\n    level: role\n    name: \"snap ring copy\"\n    pattern:\n"
                 "      root: {}\n      nodes: { Z: { compliance: rigid }, Q: { compliance: rigid } }\n      edges:\n"
                 "        - { x: Z, y: Q, pair: [fixed, revolute, prismatic, cylindrical] }\n"
                 "        - { x: root, y: Z, pair: [fixed], closure: [form] }\n"
                 "        - { x: root, y: Q, pair: [fixed], closure: [form], b: { kind: groove } }\n"
                 "  - code: wire-snap-ring\n    level: role\n    name: \"wire snap ring\"\n    pattern:\n"
                 "      root: { shape: wire-ring }\n      nodes: { G: { compliance: rigid }, R: { compliance: rigid } }\n"
                 "      edges:\n        - { x: root, y: G, pair: [fixed], closure: [form], b: { kind: groove } }\n"
                 "        - { x: root, y: R, pair: [fixed], closure: [form] }\n"
                 "        - { x: R, y: G, pair: [fixed, revolute, prismatic, cylindrical] }\n"
                 "  - code: bad-one\n    level: kind\n    name: \"bad one\"\n    pattern:\n"
                 "      root: { compliance: soft, colour: red }\n      nodes: { A: { fits: no-such }, B: {}, root: {} }\n"
                 "      edges:\n        - { x: root, y: A, pair: [glued], closure: [tape] }\n"
                 "        - { x: A, y: C, rel: near }\n        - { x: root, y: A, pair: [fixed], link: [fixed] }\n"
                 "        - { x: root, y: A, rel: part, closure: [form] }\n"
                 "      not:\n        - { x: E, y: F, pair: [fixed] }\n")
    p = subprocess.run([PY, 'core/check.py', '--law'], cwd=tree, capture_output=True, text=True, encoding='utf-8')
    out = p.stdout
    check("--law refuses a second row of one signature, naming the first; a limit more stands",
          p.returncode != 0 and "snap-ring-copy: its pattern and limits are made:retaining-ring's" in out
          and 'wire-snap-ring' not in out, out[-1500:])
    for what, says in (("a level that is neither form nor role", "bad-one: level: a concept is a form"),
                       ("a compliance the core has not", "compliance 'soft' is no row of the core's `compliances`"),
                       ("a constraint no node takes", "`colour` is no constraint of a node"),
                       ("`fits` naming no concept", "fits 'no-such', which is no concept of the law"),
                       ("`root` among the other nodes", "`root` is the pattern's own node"),
                       ("a pair the core has not", "pair glued: no row of the core's `pairs`"),
                       ("a closure the core has not", "closure tape: no row of the core's `closures`"),
                       ("an edge to no node", "y 'C' is no node of the pattern"),
                       ("a relation that is not read", "rel 'near' is none of the relations read"),
                       ("an edge both a pair and a link", "one of the three"),
                       ("a closure on a relation read", "a relation read holds no closure"),
                       ("a node no edge reaches", "pattern.nodes.B: no edge reaches it from the root"),
                       ("a not-edge between two nodes the root does not reach", "pattern.not[0]: an edge that must not")):
        check(f"--law refuses a pattern's fault: {what}", says in out, out[-1500:])

    # ---- THE MATCHER ON THE SEED
    with open(os.path.join(ROOT, 'test', 'mechanics-seed.yaml'), encoding='utf-8') as fh:
        SEED = yaml.safe_load(fh)
    M, codes = LAW.matcher(), sorted(C)
    bodies = sum(1 for a in SEED['seed'].values() for n in a['nodes'].values() if n.get('compliance'))
    joints = sum(len(a['joints']) for a in SEED['seed'].values())
    check("the seed in the basic set alone: 6 assemblies, 49 bodies, 70 joints, each pair and closure the core's",
          (len(SEED['seed']), bodies, joints) == (6, 49, 70)
          and all(j[2] in pairs and set(j[3]) <= set(LAW.tables['closures']) for a in SEED['seed'].values()
                  for j in a['joints'])
          and all(n.get('compliance') in (None, *LAW.tables['compliances']) for a in SEED['seed'].values()
                  for n in a['nodes'].values()), (len(SEED['seed']), bodies, joints))
    tp, said, extra, miss = fits_all(SEED['seed'], M, codes)
    check("the seed: every concept tried on every node, 67 fits expected found (3 of them said), none unexpected, none "
          "missed", (tp, said, extra, miss) == (67, 3, [], []), (tp, said, extra[:8], miss[:8]))
    tp, said, extra, miss = fits_all(SEED['heldout'], M, codes)
    check("the held-out pump, written after the concepts: 7 fits expected found (1 said), none unexpected, none missed",
          (tp, said, extra, miss) == (7, 1, [], []), (tp, said, extra, miss))
    d = drawing_of(SEED['seed']['damper-pulley'])
    check("a role is read of the least whole that bears it: the damper is a pulley, its ring is a pulley's rim, never "
          "a pulley itself", M.fits(d, 'damper', 'made:pulley') == 'read' and M.fits(d, 'ring', 'made:pulley') is False
          and M.fits(d, 'ring', 'made:pulley-rim') == 'read')
    d = drawing_of(SEED['seed']['idler-metal'])
    d.nodes['idler'].whole = False
    check("an absence is never read of a body not drawn whole: the idler, not drawn whole, is no idler pulley read",
          M.fits(d, 'idler', 'made:idler-pulley') is False)
    check("a concept the drawing does not hold the facts of fits nothing: a body of no compliance is no hub",
          M.fits(mechanics.Drawing([mechanics.Node('x')], []), 'x', 'made:o-ring') is False)

    # ---- A GARDEN: join, and the concepts said
    SAY = {'say': {'by': 'sam', 'at': 'now'}}

    def bean(bid, kind, *statements):
        return engine.Bean(bid, header={'bean': bid, 'kind': kind, 'title': bid, 'statements': [SAY, *statements]})

    def judged(*beans):
        g = engine.Garden({b.id: b for b in (bean('sam', 'person'), *beans)}, CASES['zone'],
                          files=['VOCAB.md', 'GARDEN.md', 'log/journal.md'], manifest={'gardener': 'sam'})
        return engine.Judge(LAW, g), g

    damper = [bean('damper', 'host',
                   {'join': {'by': 'hub', 'to': 'rubber', 'at': ['hub#seat', 'rubber#bore'], 'as': 'fixed',
                             'closure': ['material']}},
                   {'join': {'by': 'rubber', 'to': 'ring', 'at': ['rubber#seat', 'ring#bore'], 'as': 'fixed',
                             'closure': ['material']}},
                   {'join': {'by': 'hub', 'to': {'someone': 'component'}, 'at': ['hub#bore'], 'as': 'fixed',
                             'closure': ['friction', 'form']}},
                   {'classify': {'of': 'self', 'as': 'made:torsional-vibration-damper'}}),
              bean('hub', 'component', {'part': {'by': 'self', 'of': 'damper'}}),
              bean('rubber', 'component', {'part': {'by': 'self', 'of': 'damper'}},
                   {'classify': {'of': 'self', 'as': 'made:x-ring'}}),
              bean('ring', 'component', {'part': {'by': 'self', 'of': 'damper'}}),
              bean('wheel', 'component'),
              bean('w-rim', 'component', {'part': {'by': 'self', 'of': 'wheel'}})]
    J, g = judged(*damper)
    found = [f for f in J.run() if f[0] in ('valency', 'bearer', 'profile', 'frame')]
    check("a garden: joints at their bodies' features, their closures, a concept said of what nothing drawn "
          "contradicts — a device's of a device, a form of one body of a component — stand", not found, found[:6])
    D = LAW.garden_drawing(g)
    check("its drawing: the bodies and the device, the parts of the device, a part of a component a fiat part of it, "
          "each joint with its features at their bodies, the neighbour outside a node of its own",
          set(D.nodes) >= {'damper', 'hub', 'rubber', 'ring', 'wheel', 'w-rim'} and D.nodes['damper'].device is True
          and D.nodes['hub'].device is False and sorted(D.nodes['damper'].parts) == ['hub', 'ring', 'rubber']
          and D.nodes['w-rim'].fiat_of == 'wheel' and len(D.joints) == 3
          and D.joints[0]['xf'] == 'seat' and D.joints[0]['yf'] == 'bore' and D.nodes['rubber'].said == {'made:x-ring'}
          and any(n.startswith('{someone: component}') for n in D.nodes), (sorted(D.nodes), D.joints[:1]))
    check("a role a garden cannot draw yet is read of nothing: no word says a body's compliance or a feature's kind",
          not [n for n in D.nodes for c in codes if M.fits(D, n, c) == 'read'])
    for bid, kind, st, says in (
            ('d-sayable', 'document', {'join': {'by': 'self', 'to': 'hub', 'as': 'fixed'}}, "takes a being that is body"),
            ('d-glued', 'host', {'join': {'by': 'hub', 'to': 'ring', 'as': 'glued'}}, "glued"),
            ('d-tape', 'host', {'join': {'by': 'hub', 'to': 'ring', 'as': 'fixed', 'closure': ['tape']}}, "tape"),
            ('d-alone', 'host', {'join': {'by': 'hub', 'as': 'fixed'}}, "to")):
        J, _ = judged(*damper, bean(bid, kind, st))
        found = [f for f in J.run() if f[0] == 'valency' and bid in f[1]]
        check(f"rule valency refuses a join: {bid}", found and says in found[0][2], found)
    for bid, kind, code, says in (
            ('c-cylinder', 'component', 'made:hydraulic-cylinder', "a made:hydraulic-cylinder is a device, bodies "
                                                                    "joined, and this is one body"),
            ('c-oring', 'host', 'made:o-ring', "a device is bodies joined, with no compliance of its own"),
            ('c-bearing', 'component', 'made:deep-groove-ball-bearing', "is a device, bodies joined"),
            ('w-rim', 'component', 'made:pulley', "a body of its own, and this is a fiat part of wheel"),
            ('w-rim', 'component', 'made:crankshaft-pulley', "a fiat part of wheel")):
        extra = [b for b in damper if b.id != bid] + [bean(bid, kind, {'classify': {'of': 'self', 'as': code}},
                                                           *([{'part': {'by': 'self', 'of': 'wheel'}}] if bid == 'w-rim' else []))]
        J, _ = judged(*extra)
        found = [f for f in J.run() if f[0] == 'bearer' and bid in f[1]]
        check(f"rule bearer refuses {code} said of a {kind}{' that is a fiat part' if bid == 'w-rim' else ''}",
              found and says in found[0][2], found)
    J, g = judged(*damper)
    rk = reckon.Reckoner(reckon.Judged(J), rules_law=LAW)
    rk.run(lines.worded({'steps': [{'id': 'b', 'op': 'select', 'beans': 'all'},
                                   {'id': 'out', 'op': 'select', 'of': 'b',
                                    'where': [{'path': 'bean', 'fits': {'concept': 'made:torsional-vibration-damper'}}]}]}))
    check("a reading's `fits: {concept: ...}` selects the beings said to be of it",
          [m.bean for m in rk.env['out']] == ['damper'], [getattr(m, 'bean', m) for m in rk.env['out']])
    import json, sqlite3
    from core import union
    db = sqlite3.connect(':memory:')
    U = union.Union(db, J, [])
    spec = json.dumps({'concept': 'made:torsional-vibration-damper'})
    got = [r[0] for r in db.execute("SELECT x FROM (SELECT 'damper' AS x UNION SELECT 'hub' UNION SELECT 'w-rim') "
                                    "WHERE dm_fits(x, ?) = 1", (spec,))]
    check("the store's SQL calls the same matcher: `dm_fits` of a concept over the garden's drawing", got == ['damper'], got)
    got = reckon.check_selection('r', {'steps': [{'id': 'a', 'op': 'select', 'beans': 'all',
                                                   'where': [{'path': 'bean', 'fits': {'concept': 7}}]}]},
                                 lines.law_view(LAW))
    check("...and a reading's check refuses a concept named by no code", any('`fits` names one row' in t for _l, t in got),
          got)
    # ---- A GROWN GARDEN: its own scheme of concepts, held to the form beside the release's
    sys.path.append(os.path.join(ROOT, 'test'))
    import grow  # noqa: E402
    REL = grow.release(os.path.join(T, 'release'))
    G = os.path.join(T, 'garden')
    r = grow.garden(REL, G, 'sam', '--profile', 'knowledge')
    check("a garden grows with the knowledge profile", r.returncode == 0, r.out[-600:])

    def write(rel, text):
        os.makedirs(os.path.dirname(os.path.join(G, rel)), exist_ok=True)
        with open(os.path.join(G, rel), 'w', encoding='utf-8') as fh:
            fh.write(text)

    write('VOCAB.md', "---\nprofiles: [knowledge]\nschemes:\n  - { scheme: shop, classifies: \"the seals this shop "
                      "cuts\", holding: extract, licence: CC0-1.0, publisher: the gardener, url: "
                      "\"https://example.org/shop\", levels: [ { level: form }, { level: role } ], neighbours: none, "
                      "sources: extracts/shop.yaml, at: [component], form: concept }\nfiles:\n  - { registry: shop, file: "
                      "extracts/shop.yaml, key: code, format: yaml }\n---\n# the garden's own rows\n")
    write('extracts/shop.yaml', "- code: ring-seal\n  level: form\n  name: \"a ring seal\"\n  pattern:\n    root: { "
                                "compliance: elastic, shape: ring, section: round }\n- code: square-ring\n  level: form\n"
                                "  name: \"a square ring\"\n  pattern:\n    root: { compliance: elastic, shape: ring, "
                                "section: square }\n")
    write('beans/seal-a.md', "---\nbean: seal-a\nkind: component\ntitle: \"a seal\"\nstatements:\n  - read: { by: sam, "
                             "at: now }\n  - classify: { of: self, as: \"shop:square-ring\" }\n---\nA seal.\n")
    p = grow.run(PY, 'core/check.py', '.', cwd=G)
    found = [ln for ln in p.out.splitlines() if ln and not ln.startswith('core check')]
    check("rule profile: a garden's own concept of the release's signature is refused, the release's row standing "
          "first; its own new concept stands, and is said of a component",
          len(found) == 1 and "shop ring-seal: its pattern and limits are made:o-ring's" in found[0], found)
    try:
        LAW.fits({'concept': 'made:no-such'}, 'damper', D)
        check("`fits` refuses a code no concept of the law has", False)
    except ValueError as e:
        check("`fits` refuses a code no concept of the law has", 'no concept of the law' in str(e), e)
    try:
        LAW.fits({'concept': 'made:pulley'}, 'damper')
        check("`fits` of a concept is read over a garden's drawing, never of a bare value", False)
    except ValueError as e:
        check("`fits` of a concept is read over a garden's drawing, never of a bare value", 'drawing' in str(e), e)
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\n{len(FAILS)} failed" if FAILS else "\n0 failed")
sys.exit(1 if FAILS else 0)
