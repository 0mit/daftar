#!/usr/bin/env python3
"""What went between gardens, drawn with every garden called by a name, never its id: this garden as the one the page
is read in, a garden by its bean's title, and a garden whose bean says no more of it than its id as another garden —
numbered in the reader's digits where there are several — its id kept beside, in the node's title.

A garden of the core is grown here (test/grow.py) taking the view profile: Sam keeps it; a note was taken from Ali's
garden (its bean titled), the notes went to a second garden and a third garden's note was taken here (their beans say
only their ids). A page draws the gardens and what went between them (`flows`, `nodes: gardens`). Then:

  the page      this garden carries no id as its title (`here`); Ali's garden its title's words; the two others
                `unnamed`, numbered 1 and 2
  a browser     in Persian: «همین دفتر», Ali's garden by its title, «دفتری دیگر (۱)» and «دفتری دیگر (۲)»; no garden's
                id in what is read, each in its node's title; what went, each by how the page calls it

Run: python3 test/view_between_names.py   (0 = green; a NOTE, and no browser check, where no Chromium is on the machine)
"""
import html, json, os, re, shutil, subprocess, sys, tempfile

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


def last_json(out):
    try:
        return json.loads(out.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return {'error': out[-1500:]}


T = tempfile.mkdtemp(prefix='view-between-names-')
REL, G = os.path.join(T, 'release'), os.path.join(T, 'garden-sam')
STORY = ('purpose: "{p}", outcome: "{p}", stages: [{{label: Read, doer: the view}}, {{label: Draw, doer: the view}}, '
         '{{label: Open, doer: the reader}}], questions: [{{lens: orient, ask: "{p}"}}], blind: [{{what: "what nobody wrote down"}}]')
PAGE = """import json, os, sys; sys.path[:0] = [os.path.join('.', 'assets', 'view', 'lib'), 'bin']
import view_model as vm, view_engraved as ve
vm.init('.', 'page')
p = ve.page(lambda *a, **k: True, 'sam')
ve.localize(p, 'fa')
print(json.dumps(p, default=str, ensure_ascii=False))"""

try:
    grow.release(REL)
    rc, out = run(PY, os.path.join(REL, 'seed', 'germinate.py'), G, '--gardener', 'sam', '--gardener-name', 'Sam',
                  '--profile', 'view', cwd=T)
    check("a garden of the core grows taking the view profile, kept by Sam", rc == 0, out[-800:])
    run(PY, 'bin/install.py')
    put('beans/garden-ali.md', '''---
bean: garden-ali
kind: garden
title: "garden-ali — the garden Ali keeps"
summary: "Ali's own garden."
statements:
  - say:  { by: sam, at: now }
  - name: { by: garden-id, of: self, as: "123456789abc" }
  - own:  { by: theone, of: self }
---
Ali's garden.
''')
    for g, gid in (('garden-x7', '7777777777aa'), ('garden-x8', '8888888888bb')):
        put(f'beans/{g}.md', f'''---
bean: {g}
kind: garden
title: "{g}"
statements:
  - say:  {{ by: sam, at: now }}
  - name: {{ by: garden-id, of: self, as: "{gid}" }}
  - own:  {{ by: theone, of: self }}
---
A garden.
''')
    put('beans/note-ali.md', '''---
bean: note-ali
kind: document
title: "note-ali — a note from Ali's garden"
summary: "a note taken from Ali's garden"
statements:
  - say:  { by: sam, at: now }
  - own:  { by: sam, of: self }
  - take: { id: taken-1, by: sam, of: self, from: garden-ali }
---
A note.
''')
    put('beans/note-x8.md', '''---
bean: note-x8
kind: document
title: "note-x8 — a note from a garden"
summary: "a note taken from a garden"
statements:
  - say:  { by: sam, at: now }
  - own:  { by: sam, of: self }
  - take: { id: taken-1, by: sam, of: self, from: garden-x8 }
---
A note.
''')
    put('beans/notes.md', '''---
bean: notes
kind: document
title: "notes — Sam's notes"
summary: "notes Sam proposed to another garden"
statements:
  - say:     { by: sam, at: now }
  - own:     { by: sam, of: self }
  - propose: { id: offered, by: sam, of: [notes], to: garden-x7 }
---
Notes.
''')
    put('beans/page.md', f'''---
bean: page
kind: service
title: "Sam's page"
summary: "what went between gardens"
statements:
  - say:  {{ by: sam, at: now }}
  - own:  {{ by: sam, of: self }}
  - be:   {{ by: self, at: "uri:https://garden.example.org/", as: location }}
  - draw: {{ id: between, by: self, of: [sam], drawing: {{ label: Between, archetype: flows, nodes: gardens, {STORY.format(p='what went between gardens')} }} }}
  - draw: {{ id: page, by: self, of: [between], page: {{ visibility: private }} }}
---
A page.
''')
    rc, out = run(PY, 'bin/save.py', 'sam', 'three gardens, what went between them, and a page', '--body',
                  '- action: wrote [[garden-ali]], [[garden-x7]], [[garden-x8]], [[note-ali]], [[note-x8]], [[notes]] and [[page]]')
    check("the gardens, what went between them and the page are saved through the gate", rc == 0 and '0 error(s)' in out,
          out[-1500:])

    P = last_json(run(PY, '-c', PAGE)[1])
    nodes = {n['id']: n for n in ((P.get('drawings') or {}).get('between') or {}).get('nodes') or []}
    here = next((n for n in nodes.values() if n.get('here')), {})
    check("the page: this garden carries no id as its title, as the one the page is read in", here.get('here') is True
          and not here.get('title'), (here, P.get('error')))
    check("...Ali's garden its title's words; the two whose beans say only their ids `unnamed`, numbered 1 and 2",
          (nodes.get('garden-ali') or {}).get('title') == 'the garden Ali keeps'
          and (nodes.get('garden-x7') or {}).get('unnamed') is True and (nodes.get('garden-x8') or {}).get('unnamed') is True
          and sorted([(nodes.get('garden-x7') or {}).get('n'), (nodes.get('garden-x8') or {}).get('n')]) == [1, 2], nodes)

    browser = next((x for x in ('chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable') if shutil.which(x)), None)
    if not browser:
        print("NOTE  the page was not drawn in a browser: none on this machine")
    elif P.get('drawings'):
        sys.path.insert(0, os.path.join(ROOT, 'assets', 'view', 'lib'))
        import view_widgets
        LIB = os.path.join(ROOT, 'assets', 'view', 'lib')
        js = view_widgets.bundle() + ''.join(open(os.path.join(LIB, f), encoding='utf-8').read() for f in (
            os.path.join('widgets', 'direction.js'), 'view_engraved.js', 'view_flows.js'))
        page = """<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><style>%(css)s</style></head>
<body><div id="f" class="vw light" dir="rtl"></div><script>%(js)s</script><script>
const out = {errs: []}, E = %(payload)s;
window.addEventListener('error', e => out.errs.push(String(e.message)));
try {
  const t = window.daftarEngraved.tools({engraved: E});
  window.daftarArchetypes.flows(document.getElementById('f'), E.drawings.between, t, null);
  out.text = document.getElementById('f').innerText;
  out.titles = [...document.querySelectorAll('#f .eg-node')].map(x => x.getAttribute('title')).filter(Boolean);
} catch (e) { out.errs.push('driver: ' + e.message + ' ' + (e.stack || '').split('\\n')[1]); }
const pre = document.createElement('pre'); pre.id = '__out'; pre.textContent = JSON.stringify(out); document.body.appendChild(pre);
</script></body></html>"""
        path = os.path.join(T, 'between.html')
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(page % {'css': view_widgets.css() + open(os.path.join(LIB, 'view_engraved.css'), encoding='utf-8').read(),
                             'js': js, 'payload': json.dumps(P, ensure_ascii=False)})
        r = subprocess.run([browser, '--headless=new', '--disable-gpu', '--no-sandbox', '--virtual-time-budget=5000',
                            '--dump-dom', 'file://' + path], capture_output=True, text=True, encoding='utf-8', errors='replace',
                           timeout=180)
        m = re.search(r'<pre id="__out">(.*?)</pre>', r.stdout, re.S)
        B = json.loads(html.unescape(m.group(1))) if m else {'errs': ['no result: ' + r.stderr[-600:]]}
        txt = B.get('text') or ''
        check("in Persian: «همین دفتر», Ali's garden by its title, «دفتری دیگر (۱)» and «دفتری دیگر (۲)»",
              not B['errs'] and 'همین دفتر' in txt and 'the garden Ali keeps' in txt and 'دفتری دیگر (۱)' in txt
              and 'دفتری دیگر (۲)' in txt, B)
        check("...no garden's id in what is read; each beside its node, in its title", not re.search(r'garden-x[78]', txt)
              and 'garden-sam' not in txt and {'garden-x7', 'garden-x8'} <= set(B.get('titles') or []), B)
        check("...and what went, each by how the page calls it, never its id", "a note from Ali's garden" in txt
              and "Sam's notes" in txt and not re.search(r'note-ali|note-x8|^notes$', txt, re.M), B)
finally:
    if TRACES:
        print("TRACEBACKS:\n" + "\n---\n".join(TRACES[:3]))
    shutil.rmtree(T, ignore_errors=True)

print(f"\nview_between_names: {len(FAILS)} failed" + (": " + ", ".join(FAILS) if FAILS else ""))
sys.exit(1 if FAILS or TRACES else 0)
