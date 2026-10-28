#!/usr/bin/env python3
"""classifier — a classifier measured against a person's responses to its suggestions (core 4.9; bin/knowledge.py
gold): per scheme, precision beside recall at k, over the latest N responses, and a classifier's graduation as a need
whose probe is that reading.

Grows a garden of the core from a release made of this tree (test/grow.py). An invented classifier suggests the
fields of four documents, ranked as it wrote them; a person confirms, disputes or abstains, and classes one document
themselves; one suggestion and its response are kept in a store. Then:

  - `gold --by` gives, per scheme, the responses read and, at each k, precision (of its first k suggestions the person
    judged, the share right) and recall (of the codes the person holds, the share among its first k) — exactly;
  - `--latest 2` reads only the two latest responses; a store's suggestion and response are read beside the beans';
  - the finder's gold set gives precision beside recall at k, per scheme, its recall at 5 as before;
  - `probe --json` reads a graduation need — of 500 responses from the person — for each input its reading names,
    and bin/routines.py reads the need held at one floor and not at a higher one.

Invented beings; nothing here is a fact.

Run: python3 test/classifier.py   (0 = green)
"""
import json
import os
import shutil
import socket
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'bin'))
sys.path.append(os.path.join(ROOT, 'test'))
import machine  # noqa: E402
machine.ensure()
import grow  # noqa: E402

FAILS = []
PY = sys.executable
T = tempfile.mkdtemp(prefix='classifier-')
G = os.path.join(T, 'garden')


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-1500:]))
    if not cond:
        FAILS.append(name)


def write(rel, text):
    p = os.path.join(G, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)


def save(what, body):
    return grow.run(PY, 'bin/save.py', 'sam', what, '--body', body, cwd=G)


def bean(bid, kind, *statements):
    return (f'---\nbean: {bid}\nkind: {kind}\ntitle: "{bid}"\nstatements:\n'
            + ''.join(f'  - {s}\n' for s in statements) + '---\nInvented.\n')


def doc(bid, suggestions, responses, own=()):
    """A document: the classifier's suggestions (in its rank), the person's responses to them (`(id, verdict, day)`),
    and her own classes."""
    st = ['say: { by: sam, of: [p], at: now }', 'produce: { id: p, by: sam, of: self, at: "2026-09-01" }']
    st += [f'classify: {{ id: s{n}, by: topic-model, of: self, as: "{c}" }}' for n, c in enumerate(suggestions, 1)]
    st.append(f"derive: {{ by: topic-model, of: [{', '.join(f's{n}' for n in range(1, len(suggestions) + 1))}], "
              "from: [p], at: now }")
    st += [f'respond: {{ id: r{n}, by: sam, of: [{s}], as: {v}, at: "2026-10-{d}T10:00:00+00:00" }}'
           for n, (s, v, d) in enumerate(responses, 1)]
    st += [f'classify: {{ id: o{n}, by: sam, of: self, as: "{c}" }}' for n, c in enumerate(own, 1)]
    mine = [f'r{n}' for n in range(1, len(responses) + 1)] + [f'o{n}' for n in range(1, len(own) + 1)]
    if mine:
        st.append(f"say: {{ by: sam, of: [{', '.join(mine)}], at: now }}")
    return bean(bid, 'document', *st)


def gold(*a):
    r = grow.run(PY, 'bin/knowledge.py', 'gold', *a, cwd=G)
    return r, r.out


try:
    REL = grow.release(os.path.join(T, 'release'))
    r = grow.garden(REL, G, 'sam', '--gardener-name', 'Sam')
    check("a garden of the core grows", r.returncode == 0, r.out[-600:])
    S = os.path.join(T, 'stores')
    os.makedirs(S)
    me = socket.gethostname().lower().split('.')[0]
    write('beans/nas.md', '---\nbean: nas\nkind: host\ntitle: "nas"\nstatements:\n  - say: { by: sam, at: now }\n'
          f'  - name: {{ by: dns, of: self, as: "{me}.example.org" }}\ndetails:\n  roots:\n    test:\n'
          f'      system: unix-filesystem\n      at: "{me}:{S}"\n  stores:\n    t:\n      at: "root:test/t.sqlite"\n'
          '      form: sqlite\n---\nA host.\n')
    vocab = open(os.path.join(G, 'VOCAB.md'), encoding='utf-8').read()
    write('VOCAB.md', vocab.replace('---\n', '---\nprofiles: [knowledge]\n', 1))
    write('beans/knowledge-tool.md', bean('knowledge-tool', 'program', 'make: { by: sam, at: now }'))
    write('beans/topic-model.md', bean('topic-model', 'model', 'make: { by: sam, at: now }'))
    # isced-f-2013: 0532 earth sciences, 0231 language acquisition, 1013 hotel, restaurants and catering
    write('beans/doc-1.md', doc('doc-1', ['isced-f-2013:0532', 'isced-f-2013:0231'],
                                [('s1', 'confirms', '01'), ('s2', 'disputes', '02')]))
    write('beans/doc-2.md', doc('doc-2', ['isced-f-2013:0231', 'isced-f-2013:1013'], [('s1', 'disputes', '03')],
                                own=['isced-f-2013:1013']))
    write('beans/doc-3.md', doc('doc-3', ['isced-f-2013:1013'], [('s1', 'abstains', '04')]))
    r = save('RULE-CHANGE: the knowledge profile, a classifier, and three documents it classed',
             '- action: RULE-CHANGE — VOCAB.md takes the profile knowledge; wrote [[nas]], [[knowledge-tool]], '
             '[[topic-model]], [[doc-1]], [[doc-2]], [[doc-3]]\n- ratified_by: sam')
    check("suggestions, responses and a person's own classes pass the gate", r.returncode == 0, r.out[-1500:])

    sys.path.insert(0, G)
    os.chdir(G)
    import store as dmstore  # noqa: E402
    st = dmstore.open_store('t', root=G)
    st.being('doc-4', 'document', title='doc-4')
    made = st.put('topic-model', 'derive', {'id': 'run-1', 'by': 'topic-model', 'from': ['doc-1#p'],
                                            'at': '2026-10-05T09:00:00+00:00'})
    sid = st.put('doc-4', 'classify', {'by': 'topic-model', 'of': 'doc-4', 'as': 'isco-08:2522'}, act=f'topic-model#{made}')
    said = st.put('sam', 'say', {'id': 'sam-1', 'by': 'sam', 'at': '2026-10-06T09:00:00+00:00'})
    st.put('doc-4', 'respond', {'by': 'sam', 'of': [f'doc-4#{sid}'], 'as': 'confirms'}, act=f'sam#{said}')
    st.db.commit()
    st.close()

    r, out = gold('--by', 'sam', '--k', '1,3')
    want = ["gold: topic-model in isced-f-2013 — sam's latest 4 response(s) to its suggestions (confirms 1, disputes 2, "
            "abstains 1)",
            "at 1: precision 1/2 = 0.500   recall 1/2 = 0.500",
            "at 3: precision 2/4 = 0.500   recall 2/2 = 1.000"]
    check("gold: per scheme, the responses read and, at each k, precision beside recall — exactly as hand-counted",
          r.returncode == 0 and all(w in out for w in want), out)
    check("...a store's suggestion and its response read beside the beans' (one universe), in their own scheme",
          "gold: topic-model in isco-08 — sam's latest 1 response(s)" in out
          and out.split('isco-08')[1].count('precision 1/1 = 1.000   recall 1/1 = 1.000') == 2, out)
    r, out = gold('--by', 'sam', '--k', '1,3', '--latest', '2', '--of', 'topic-model')
    check("gold: --latest 2 reads only the two latest responses in each scheme",
          r.returncode == 0 and "isced-f-2013 — sam's latest 2 response(s) to its suggestions (confirms 0, disputes 1, "
          "abstains 1)" in out and "at 1: precision 0/1 = 0.000   recall 0/1 = 0.000" in out
          and "at 3: precision 1/2 = 0.500   recall 1/1 = 1.000" in out, out)
    r, out = gold('--by', 'ana')
    check("gold: a person who gave no response says so", r.returncode == 1 and 'no response' in out, out)
    r, out = gold(os.path.join(G, 'test', 'gold', 'finder.tsv') if os.path.isfile(os.path.join(G, 'test', 'gold', 'finder.tsv'))
                  else os.path.join(ROOT, 'test', 'gold', 'finder.tsv'), '--k', '1,5')
    check("gold: the finder's gold set gives precision beside recall at k, per scheme, and its recall at 5 as before",
          r.returncode == 0 and 'isco-08 (' in out and 'at 5: precision' in out and 'recall@5 = 20/24' in out, out[-800:])

    # ---- graduation: a need of the classifier, its probe that reading
    reading = ('reckon: { id: graduated, reading: { what: "its precision at 1 in the fields of knowledge is at least the '
               'floor, over the latest responses", inputs: [ { name: precision-at-1-isced-f-2013, origin: { act: read, '
               'nature: soma, by: knowledge-tool }, quantity: ratio }, { name: responses-isced-f-2013, origin: { act: '
               'read, nature: soma, by: knowledge-tool }, quantity: number } ], steps: [ { id: floor, op: constant, '
               'value: { count: "FLOOR", unit: "1" } }, { id: ok, op: compare, of: precision-at-1-isced-f-2013, with: '
               'floor, is: at-least } ] } }')
    write('beans/topic-model.md', bean('topic-model', 'model', 'make: { by: sam, at: now }',
                                       'need: { id: graduation, by: self, of: { count: "500", unit: "{response}" }, '
                                       'from: sam, note: "suggests alone once its precision holds" }',
                                       'meet: { by: graduated, of: graduation }', reading.replace('FLOOR', '0.5')))
    r = save('the classifier graduates by a need', '- action: wrote [[topic-model]]: its graduation, a need')
    check("graduation: a need of 500 responses from the person, met by a reading of the measure, passes the gate",
          r.returncode == 0, r.out[-1200:])
    r = grow.run(PY, 'bin/knowledge.py', 'probe', '--json', cwd=G)
    try:
        doc_ = json.loads(r.stdout)
    except ValueError:
        doc_ = {}
    got = {x['key']: x for x in doc_.get('readings', [])}
    check("probe: each input its reading names, read over the person's latest 500 responses",
          got.get('precision-at-1-isced-f-2013', {}).get('value') == {'count': '0.5', 'unit': '1'}
          and got.get('responses-isced-f-2013', {}).get('value') == {'count': '4', 'unit': '{response}'}
          and all(x['being'] == 'topic-model' for x in got.values()), (doc_, r.out[-600:]))
    pj = os.path.join(T, 'probe.json')
    with open(pj, 'w', encoding='utf-8') as fh:
        fh.write(r.stdout)
    r = grow.run(PY, 'bin/routines.py', 'needs', 'topic-model', '--readings', pj, '--json', cwd=G)
    try:
        held = {x['need']: x['holds'] for x in json.loads(r.stdout)}
        whys = [x.get('why') for x in json.loads(r.stdout)]
    except (ValueError, TypeError, KeyError):
        held, whys = {}, r.out[-800:]
    check("graduation: bin/routines.py reads the need held at a floor of 0.5", held.get('graduation') is True,
          (held, whys))
    write('beans/topic-model.md', open(os.path.join(G, 'beans', 'topic-model.md'), encoding='utf-8').read()
          .replace('count: "0.5", unit: "1"', 'count: "0.95", unit: "1"'))
    r = grow.run(PY, 'bin/routines.py', 'needs', 'topic-model', '--readings', pj, '--json', cwd=G)
    try:
        held = {x['need']: x['holds'] for x in json.loads(r.stdout)}
    except (ValueError, TypeError, KeyError):
        held = {}
    check("...and not held at a floor of 0.95", held.get('graduation') is False, (held, r.out[-800:]))
finally:
    os.chdir(ROOT)
    shutil.rmtree(T, ignore_errors=True)

print(f"\nclassifier: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
