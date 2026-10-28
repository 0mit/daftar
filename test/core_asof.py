#!/usr/bin/env python3
"""core_asof — a reading read over the garden as known at a moment (core 4.9): what was said, read, made or derived at
or before it, in a bean or a store, whatever moment its statements speak of — so a backtest never reads what was said
after its moment.

Grows a garden of the core from a release made of this tree (test/grow.py): two documents saved a moment apart, a
statement added to the first after that moment, a host that keeps a store holding a document read before it and one
read after, and a reading of every document, written last, that names its `known` input. Then:

  - asked as known at the moment between the saves, the reading reads the first document without the statement added
    later, not the second, and of the store's documents only the one read before — though the reading itself was
    written after;
  - asked now, it reads them all; a pin and `known` together read the commit as known at the moment, the clock that
    moment;
  - `known` given no moment, or a day where a moment is asked, is refused, saying what to give; a reading whose `known`
    names no input of it is refused by the gate.

Invented beings; nothing here is a fact.

Run: python3 test/core_asof.py   (0 = green)
"""
import datetime
import os
import shutil
import socket
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'bin'))
sys.path.append(os.path.join(ROOT, 'test'))
import machine  # noqa: E402
machine.ensure()
import grow  # noqa: E402

FAILS = []
PY = sys.executable
T = tempfile.mkdtemp(prefix='core-asof-')
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


def text(rel):
    with open(os.path.join(G, rel), encoding='utf-8') as fh:
        return fh.read()


def save(what, body):
    return grow.run(PY, 'bin/save.py', 'sam', what, '--body', body, cwd=G)


def doc(bid, *statements):
    return (f'---\nbean: {bid}\nkind: document\ntitle: "{bid}"\nstatements:\n'
            + ''.join(f'  - {s}\n' for s in statements) + '---\nA document.\n')


def ask(*a):
    r = grow.run(PY, 'bin/reckon.py', 'backtest:docs', *a, cwd=G)
    return r, [ln.strip() for ln in r.out.splitlines() if ln.startswith('  ') and not ln.startswith('  note')
               and not ln.startswith('  (') and not ln.startswith('  read at')]


def moment(t):
    return datetime.datetime.fromtimestamp(t).astimezone().isoformat(timespec='seconds')


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
    write('beans/report-a.md', doc('report-a', 'say: { by: sam, at: now }',
                                   'produce: { id: p, by: sam, of: self, at: "2026-09-01" }'))
    r = save('a host and the first report', '- action: wrote [[nas]], [[report-a]]')
    check("the first report is saved", r.returncode == 0, r.out[-800:])
    time.sleep(1.5)
    between = time.time()
    M = moment(between)
    time.sleep(1.5)
    write('beans/report-b.md', doc('report-b', 'say: { by: sam, at: now }',
                                   'produce: { id: p, by: sam, of: self, at: "2026-05-01" }'))
    write('beans/report-a.md', text('beans/report-a.md').replace('---\nA document.', '  - about: { id: ab, of: [nas] }\n'
                                                       '  - say: { by: sam, of: [ab], at: now }\n---\nA document.'))
    r = save('the second report, and what the first is about',
             '- action: wrote [[report-b]], [[report-a]]: what it is about, said after')
    check("the second report, and a statement added to the first, are saved after the moment", r.returncode == 0,
          r.out[-800:])

    sys.path.insert(0, G)
    os.chdir(G)
    import store as dmstore  # noqa: E402
    st = dmstore.open_store('t', root=G)
    for d, at in (('doc-before', moment(between - 86400)), ('doc-after', moment(between + 3600))):
        act = st.put('nas', 'read', {'id': f'read-{d}', 'by': 'nas', 'at': at})
        st.being(d, 'document', title=d)
        st.put(d, 'produce', {'by': 'sam', 'of': d, 'at': '2026-01-01'}, act=f'nas#{act}')
    st.put('doc-before', 'about', {'id': 'stored-ab', 'of': ['nas']},
           act=f"nas#{st.put('nas', 'read', {'id': 'read-early', 'by': 'nas', 'at': moment(between - 60)})}")
    st.db.commit()
    st.close()

    write('beans/backtest.md', '---\nbean: backtest\nkind: design\ntitle: "backtest"\nstatements:\n'
          '  - say: { by: sam, at: now }\n'
          '  - reckon: { id: docs, reading: { what: "every document, as known at the moment asked", inputs: '
          '[ { name: as-of, origin: { act: say }, type: position } ], known: as-of, steps: '
          '[ { id: d, op: select, kind: document, store: t } ] } }\n'
          '  - reckon: { id: about, reading: { what: "what is said to be about the host", inputs: '
          '[ { name: as-of, origin: { act: say }, type: position } ], known: as-of, steps: '
          '[ { id: a, op: select, kind: document, store: t, entries: about } ] } }\n---\nA reading.\n')
    r = save('a reading, as known at a moment', '- action: wrote [[backtest]]')
    check("a reading that names its `known` input passes the gate", r.returncode == 0, r.out[-800:])
    head = grow.run('git', 'rev-parse', 'HEAD', cwd=G).stdout.strip()

    r, got = ask('--input', f'as-of={M}')
    check("as known at the moment: the first report, and of the store's documents the one read before — not the second "
          "report, saved after, nor the document read after — though the reading itself was written after",
          r.returncode == 0 and sorted(got) == ['doc-before', 'report-a'], (got, r.out[-800:]))
    r2 = grow.run(PY, 'bin/reckon.py', 'backtest:about', '--input', f'as-of={M}', cwd=G)
    abouts = [ln.strip() for ln in r2.out.splitlines() if ln.startswith('  ') and '#' in ln]
    check("...a statement added to a bean after the moment is not read; one a store knew before it is",
          r2.returncode == 0 and not any(x.startswith('report-a#') for x in abouts) and 'doc-before#stored-ab' in abouts,
          (abouts, r2.out[-800:]))
    r, got = ask('--input', f'as-of={moment(time.time() + 7200)}')
    check("asked later, it reads them all", r.returncode == 0
          and sorted(got) == ['doc-after', 'doc-before', 'report-a', 'report-b'], (got, r.out[-800:]))
    r, got = ask('--input', f'as-of={M}', '--at', head, '--moment', moment(time.time()))
    check("a pin beside it: the commit read as known at the moment, the clock that moment",
          r.returncode == 0 and sorted(got) == ['doc-before', 'report-a'] and f'the clock {M}' in r.out, (got, r.out[-600:]))
    r, _got = ask()
    check("refused: `known` given no moment — it says which input to give", r.returncode != 0 and '--input as-of=' in r.out,
          r.out[-400:])
    r, _got = ask('--input', 'as-of=2026-10-01')
    check("refused: a day where a moment is asked", r.returncode != 0 and 'a moment' in r.out, r.out[-400:])
    write('beans/backtest.md', text('beans/backtest.md').replace('known: as-of, steps: [ { id: d,', 'known: when, steps: [ { id: d,'))
    r = save('a reading whose known names nothing', '- action: wrote [[backtest]]')
    check("the gate refuses a reading whose `known` names no input of it", r.returncode != 0
          and '`known: when` names no input' in r.out, r.out[-800:])
finally:
    os.chdir(ROOT)
    shutil.rmtree(T, ignore_errors=True)

print(f"\ncore_asof: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
