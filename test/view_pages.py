#!/usr/bin/env python3
"""A garden's handplace is its pages, one page bean for each entry of its navigation: several page beans in one
garden, each checked as the page it is, listed in the order the garden places them, and a table of a reading drawn with
no drawing module — its lines the reading's members, each opening its being's sheet, each sent only to a reader who may
read it.

A garden of the core is grown here (test/grow.py) taking the view profile: Sam keeps it, mends bicycles on a walk
(handed over, looked at, mended, collected), and holds two repairs on it; a reader kept under an opaque id may read one
of them. Four pages: what waits (a queue, placed first), the repairs (a table, second), the time (a timeline, third),
and an older page that says no place. Then:

  the pages   each passes the core's gate and `view check` as the page it is — another page's own terms are its own,
              not strays on this one; the garden's handplace lists them in the places their `be … as: order` gives, the
              page with none last
  the table   a page of a table of a reading names no drawing module, and `view check` agrees; its lines are the
              reading's members, one each, every cell the values at its column's path as they are (a step by its walk's
              words); the being of each line has its sheet; a reader is sent only the lines of the beings they may
              read, and no sheet of another
  a browser   the report of the table's page in `en` and `fa`: drawn at every lens but its story with no exception, its
              first column at the reader's line start, and a line's being opening its sheet

Run: python3 test/view_pages.py   (0 = green)
"""
import json, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'test'))
import grow  # noqa: E402

PY = sys.executable
FAILS, TRACES = [], []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-1500:]))
    if not cond:
        FAILS.append(name)


def run(*a, cwd=None):
    r = subprocess.run(list(a), capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=cwd or G, env=grow.ENV)
    out = r.stdout + r.stderr
    if 'Traceback' in out:
        TRACES.append(out[-1200:])
    return r.returncode, out


def put(rel, text):
    p = os.path.join(G, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)


def get(rel):
    with open(os.path.join(G, rel), encoding='utf-8') as fh:
        return fh.read()


T = tempfile.mkdtemp(prefix='view-pages-')
REL, G = os.path.join(T, 'release'), os.path.join(T, 'garden-sam')
READER = 'p-0a1b2c3d'

STORY = ('purpose: "{p}", outcome: "{o}", stages: [{{label: Read the garden, doer: the view}}, {{label: Draw what it says, '
         'doer: the reader}}, {{label: Open a being, doer: the reader}}], questions: [{{lens: orient, ask: "{q}"}}], '
         'blind: [{{what: "what nobody wrote down"}}]')


def page(bid, place, title, readings, drawings, fields):
    """A page bean: its place in the handplace (`be … at "ordinal:<n>" as: order`, none where `place` is None), its
    readings, its drawings, and the page that draws them."""
    st = ['say:    { by: sam, at: now }', 'own:    { by: sam, of: self }',
          'be:     { by: self, at: "uri:https://garden.example.org/", as: location, placed: { openness: here } }']
    if place is not None:
        st.append(f'be:     {{ by: self, at: "ordinal:{place}", as: order }}')
    st += [f'reckon: {{ id: {rid}, reading: {{ what: "{w}", steps: {steps} }} }}' for rid, w, steps in readings]
    st += [f'draw:   {{ id: {k}, by: self, of: [sam], drawing: {{ label: "{lab}", archetype: {a}, {STORY.format(p=lab, o=lab, q=lab)}{", " + x if x else ""} }} }}'
           for k, lab, a, x in drawings]
    st.append(f'draw:   {{ id: page, by: self, of: [{", ".join(k for k, *_ in drawings)}], page: {{ visibility: private, fields: {fields} }} }}')
    return (f'---\nbean: {bid}\nkind: service\ntitle: "{title}"\nsummary: "{title}, a page of Sam\'s handplace"\nstatements:\n'
            + ''.join(f'  - {s}\n' for s in st) + f'---\n{title}.\n')


CASES = [('cases', "Sam's repairs", '[ { id: c, op: select, kind: contract, where: [ { path: be.as, "=": order } ] } ]')]
FIELDS = ('[{kind: contract, fact: title, shown_from: understand}, {kind: contract, fact: agree, shown_from: understand}, '
          '{kind: contract, fact: move, shown_from: understand}]')
PAGES = {
    'page-now': page('page-now', 1, 'Now', [], [('waits', 'What waits', 'queue', '')], FIELDS),
    'page-repairs': page('page-repairs', 2, 'Repairs', CASES,
                         [('repairs', 'Repairs', 'table', 'selection: cases, columns: [ { label: Repair, path: title }, '
                                                          '{ label: Where it stands, path: move.at } ]')], FIELDS),
    'page-time': page('page-time', 3, 'Time', CASES, [('time', 'Time', 'timeline', 'selection: cases')], FIELDS),
    'page-older': page('page-older', None, 'Older', [], [('older', 'Older', 'queue', '')], FIELDS),
}


WALK = ['handed-over', 'looked-at', 'mended', 'collected']


def repair(bid, title, step):
    moves = ''.join(f'  - move:   {{ by: sam, of: self, through: course, at: [now, "walk-repair#{s}"] }}\n'
                    for s in WALK[:WALK.index(step) + 1])
    return f'''---
bean: {bid}
kind: contract
title: "{title}"
summary: "Sam mends a bicycle"
statements:
  - say:    {{ by: sam, at: now }}
  - own:    {{ by: theone, of: self }}
  - agree:  {{ by: sam, of: "a bicycle", through: spoken, as: repairer }}
  - be:     {{ id: course, by: self, at: walk-repair, as: order }}
{moves}---
{title}.
'''


try:
    grow.release(REL)
    rc, out = run(PY, os.path.join(REL, 'seed', 'germinate.py'), G, '--gardener', 'sam', '--gardener-name', 'Sam',
                  '--profile', 'view', cwd=T)
    check("a garden of the core grows taking the view profile, kept by Sam", rc == 0, out[-800:])
    run(PY, 'bin/install.py')
    put('VOCAB.md', get('VOCAB.md').replace('kinds: []\n', 'kinds:\n  - { kind: procedure, nature: sayable, meaning: "a way a thing is done, step by step: a walk" }\n', 1)
        if 'kinds: []\n' in get('VOCAB.md') else get('VOCAB.md').replace(
            '---\n', '---\nkinds:\n  - { kind: procedure, nature: sayable, meaning: "a way a thing is done, step by step: a walk" }\n', 1))
    put('mappings/walk-repair.md', '''---
bean: walk-repair
kind: procedure
title: "walk-repair — how a bicycle repair goes"
summary: "handed over, looked at, mended, collected"
statements:
  - say:  { by: sam, at: now }
  - step: { id: handed-over, as: "the owner brings the bicycle", to: [looked-at] }
  - step: { id: looked-at, as: "what is wrong is found", to: [mended] }
  - step: { id: mended, as: "it is mended", to: [collected] }
  - step: { id: collected, as: "the owner takes it home", walk: { final: "true" } }
---
The steps of a repair.
''')
    put('beans/repair-1.md', repair('repair-1', 'repair-1 — the red bicycle', 'looked-at'))
    put('beans/repair-2.md', repair('repair-2', 'repair-2 — the blue bicycle', 'mended'))
    put(f'beans/{READER}.md', f'---\nbean: {READER}\nkind: person\ntitle: "{READER}"\nsummary: "a reader"\nstatements:\n'
                              '  - say: { by: sam, at: now }\n  - own: { by: theone, of: self }\n---\nA reader.\n')
    rc, out = run(PY, 'bin/save.py', 'sam', "RULE-CHANGE: Sam's repairs on a walk, and a reader",
                  '--body', '- ratified_by: sam', '- action: the walk [[walk-repair]], [[repair-1]] and [[repair-2]] on it, '
                  f'and [[{READER}]]; VOCAB.md holds the kind of a walk')
    check("the repairs, the walk and the reader are saved through the core's gate", rc == 0 and "0 error(s)" in out, (rc, out[-2500:]))
    for bid, text in PAGES.items():
        put(f'beans/{bid}.md', text)
    put('beans/sam.md', get('beans/sam.md').replace('\n---\n', f'\n  - grant: {{ id: reader-reads, by: self, to: [{READER}], of: [page-repairs, repair-1], as: read }}\n'
                                                   '  - say: { by: sam, of: [reader-reads], at: now }\n---\n', 1))
    rc, out = run(PY, 'bin/save.py', 'sam', "Sam's handplace: four pages, and the reader may read one repair on one",
                  '--body', '- action: wrote ' + ', '.join(f'[[{b}]]' for b in PAGES) + ', each a page of its own; '
                  f'[[sam]] lets [[{READER}]] read [[page-repairs]] and [[repair-1]]')
    check("four page beans — a queue, a table, a timeline, an older page — pass the core's gate", rc == 0 and '0 error(s)' in out,
          out[-1500:])

    # ------------------------------------------------------------------ the pages, each as the page it is
    for bid in PAGES:
        rc, out = run(PY, 'assets/view/bin/view.py', 'check', '--page', bid)
        check(f"view check --page {bid}: it agrees — the other pages' own terms are their own, no strays on it",
              rc == 0 and 'agree' in out and 'sit on the page' not in out, out[-900:])
    code = ("import json, os, sys; sys.path.insert(0, os.path.join(%r, 'assets', 'view', 'lib')); import view_model as vm; "
            "vm.init(%r); print(json.dumps(vm.handplace()))" % (G, G))
    rc, out = run(PY, '-c', code)
    try:
        hp = json.loads(out.strip().splitlines()[-1])
    except (ValueError, IndexError):
        hp = out[-600:]
    check("the handplace lists its pages in the places their `be … as: order` gives — now, repairs, time — and the page "
          "that says none after them", isinstance(hp, list) and [(x['bean'], x['place']) for x in hp]
          == [('page-now', 1), ('page-repairs', 2), ('page-time', 3), ('page-older', None)], hp)

    # ------------------------------------------------------------------ the table, with no module
    rc, out = run(PY, 'assets/view/bin/view.py', 'check', '--page', 'page-repairs')
    check("a page of a table of a reading names no drawing module, and view check agrees", rc == 0
          and 'drawing module' not in out, out[-600:])
    code = ("import json, os, sys, importlib; sys.path[:0] = [os.path.join(%r, 'assets', 'view', 'lib'), os.path.join(%r, 'bin')]; "
            "import view_model as vm, view_engraved as ve; vm.init(%r, 'page-repairs'); dmpass = importlib.import_module('pass'); "
            "may = lambda who: (lambda act, b, positions=None: dmpass.may(who, act, b, positions=positions, root=%r).granted); "
            "print(json.dumps({w: ve.page(may(w), w) for w in ('sam', %r)}, default=str))" % (G, G, G, G, READER))
    rc, out = run(PY, '-c', code)
    try:
        P = json.loads(out.strip().splitlines()[-1])
    except (ValueError, IndexError):
        P = {'sam': {}, READER: {}, 'error': out[-1500:]}
    t_sam = ((P.get('sam') or {}).get('drawings') or {}).get('repairs') or {}
    rows = [(r.get('bean'), r.get('cells')) for r in t_sam.get('rows') or []]
    check("its lines are the reading's members, one each, every cell the values at its column's path as they are — the "
          "title, and where each stands, the moment and the step its moves reached, said by the walk's own words",
          [b for b, _c in rows] == ['repair-1', 'repair-2'] and rows[0][1][0] == ['repair-1 — the red bicycle']
          and [x[1] for x in rows[0][1][1]] == ['the owner brings the bicycle', 'what is wrong is found']
          and [c['label'] for c in t_sam.get('columns') or []] == ['Repair', 'Where it stands'], (t_sam, P.get('error')))
    check("...and the being of each line has its sheet in the page", {'repair-1', 'repair-2'}
          <= set(((P.get('sam') or {}).get('sheets') or {})), sorted(((P.get('sam') or {}).get('sheets') or {})))
    t_rdr = ((P.get(READER) or {}).get('drawings') or {}).get('repairs') or {}
    check("a reader is sent only the lines of the beings they may read, and no sheet of another",
          [r.get('bean') for r in t_rdr.get('rows') or []] == ['repair-1']
          and 'repair-2' not in ((P.get(READER) or {}).get('sheets') or {}) and 'repair-2' not in json.dumps(P.get(READER)),
          (t_rdr, sorted(((P.get(READER) or {}).get('sheets') or {}))))

    # ------------------------------------------------------------------ in a browser
    browser = next((b for b in ('chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable') if shutil.which(b)), None)
    DRIVE = """<script>
window.__errs = []; window.addEventListener('error', e => window.__errs.push(String(e.message)));
window.addEventListener('load', () => { const out = {}; let sheet = '';
 try { document.querySelector('.tab[data-t="repairs"]').click();
  for (const l of [...document.querySelectorAll('#lens button')].map(b => b.dataset.l)) {
   document.querySelector('#lens button[data-l="' + l + '"]').click(); out[l] = document.querySelectorAll('#view table.eg-table tbody tr').length; }
  document.querySelector('#lens button[data-l="understand"]').click();
  const th = document.querySelector('#view table.eg-table thead th:nth-child(2)'), td = document.querySelector('#view table.eg-table tbody tr th');
  out.firstAtStart = th && td ? (document.documentElement.dir === 'rtl' ? td.getBoundingClientRect().right > th.getBoundingClientRect().right
                                                                         : td.getBoundingClientRect().left < th.getBoundingClientRect().left) : null;
  const o = document.querySelector('#view table.eg-table [data-action="open"]'); if (o) o.click();
  const d = document.querySelector('dialog.eg-dialog'); sheet = d ? d.innerText : '';
  out.dir = document.documentElement.dir;
 } catch (e) { window.__errs.push('driver: ' + e.message); }
 const pre = document.createElement('pre'); pre.id = '__result'; pre.textContent = JSON.stringify({errs: window.__errs, out, sheet}); document.body.appendChild(pre); });
</script>"""
    for lang, want in (('en', 'ltr'), ('fa', 'rtl')):
        src = os.path.join(T, f'repairs-{lang}.html')
        rc, out = run(PY, 'assets/view/bin/view.py', 'report', '--page', 'page-repairs', '--out', src, '--lang', lang)
        check(f"view report --page page-repairs --lang {lang}: written", rc == 0, out[-600:])
        if not browser or rc != 0:
            continue
        dr = os.path.join(T, f'drive-{lang}.html')
        with open(dr, 'w', encoding='utf-8') as fh:
            fh.write(open(src, encoding='utf-8').read().replace('<head>', '<head>' + DRIVE, 1))
        r = subprocess.run([browser, '--headless=new', '--disable-gpu', '--no-sandbox', '--virtual-time-budget=6000',
                            '--dump-dom', 'file://' + dr], capture_output=True, text=True, encoding='utf-8', errors='replace',
                           timeout=120)
        import html as _html
        m = re.search(r'<pre id="__result">(.*?)</pre>', r.stdout, re.S)
        res = json.loads(_html.unescape(m.group(1))) if m else {'errs': ['no result: ' + r.stderr[-300:]], 'out': {}}
        o = res.get('out') or {}
        check(f"browser, {lang}: the table drawn with no module at every lens but its story, two lines, its first column at "
              f"the reader's line start ({want}), and a line's being opening its sheet, with no exception",
              not res['errs'] and o.get('dir') == want and o.get('orient') == 0
              and all(o.get(l) == 2 for l in ('understand', 'operate', 'inspect')) and o.get('firstAtStart') is True
              and 'repair-1' in (res.get('sheet') or ''), res)
    if not browser:
        print("NOTE  the pages were not drawn in a browser: none on this machine")
finally:
    if TRACES:
        print("TRACEBACKS:\n" + "\n---\n".join(TRACES[:3]))
    shutil.rmtree(T, ignore_errors=True)

print(f"\nview_pages: {len(FAILS)} failed" + (": " + ", ".join(FAILS) if FAILS else ""))
sys.exit(1 if FAILS or TRACES else 0)
