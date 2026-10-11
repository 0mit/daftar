#!/usr/bin/env python3
"""A person kept off git by name (`bin/held.py person`: an opaque id in git, their name and contacts held on a machine's
store), as a page shows them: by their name, to a reader who may read them, on the host whose store keeps it — and by
their opaque id to every other reader, on every other host, and in a page of one file.

A garden of the core is grown here (test/grow.py) taking the view profile: Sam keeps it on a machine whose store keeps
what is held; a person is minted by bin/held.py, their name and phone held there; Sam and they agree on lessons; a page
draws the lessons' sheet. A host is asked for the page of two readers — Sam, who may read the person, and a guest who
may read the lessons alone. Then:

  the host      to Sam the page calls the person by their held name — their sheet's title, their contact on it, the name
                every role that names them is shown by — and marks the name as held; to the guest nothing of the name or
                the phone, anywhere in the page, and no sheet of the person
  one file      the report, a page of one file, carries the opaque id and never the name or the phone
  a browser     Sam's page in Persian: the lessons' `agree` shows the person by their name; their sheet shows how to reach
                them under «نشانی و تماس», the phone left to right as it is written, and says it is held on this machine
  erased        once the person is erased from the store, the page calls them by their id again

Run: python3 test/view_held_names.py   (0 = green; a NOTE, and no browser check, where no Chromium is on the machine)
"""
import html, json, os, re, shutil, socket, subprocess, sys, tempfile, types

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


T = tempfile.mkdtemp(prefix='view-held-names-')
REL, G, STORE = os.path.join(T, 'release'), os.path.join(T, 'garden-sam'), os.path.join(T, 'vault')
HOST = socket.gethostname().lower()
NAME, PHONE = 'Ali Demir', '+15555550100'
STORY = ('purpose: "{p}", outcome: "{p}", stages: [{{label: Read, doer: the view}}, {{label: Draw, doer: the view}}, '
         '{{label: Open, doer: the reader}}], questions: [{{lens: orient, ask: "{p}"}}], blind: [{{what: "what nobody wrote down"}}]')
# the page as a host gives it to a reader (view_engraved.scoped), `may` the host's one answer: Sam reads every being,
# the guest the lessons and the page alone
SCOPED = ("import json, os, sys, types; sys.path[:0] = [os.path.join('.', 'assets', 'view', 'lib'), 'bin']; "
          "import view_model as vm, view_engraved as ve; vm.init('.', 'page'); "
          "may = lambda user, bean, positions=None, write=False: (user == 'sam' or bean in ('lessons', 'page'), ''); "
          "host = types.SimpleNamespace(cfg={'users': {'sam': {'bean': 'sam', 'lang': 'fa'}, 'guest': {'bean': 'guest'}}}, "
          "head='h', may=may); print(json.dumps({u: ve.scoped(host, u) for u in ('sam', 'guest')}, default=str, ensure_ascii=False))")


def scoped():
    rc, out = run(PY, '-c', SCOPED)
    try:
        return json.loads(out.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return {'error': out[-1500:]}


try:
    grow.release(REL)
    rc, out = run(PY, os.path.join(REL, 'seed', 'germinate.py'), G, '--gardener', 'sam', '--gardener-name', 'Sam',
                  '--profile', 'view', cwd=T)
    check("a garden of the core grows taking the view profile, kept by Sam", rc == 0, out[-800:])
    run(PY, 'bin/install.py')
    os.makedirs(STORE, exist_ok=True)
    put('VOCAB.md', get('VOCAB.md').replace(
        "namespaces: []\n",
        "namespaces:\n  - { namespace: anchor-hostname, once: \"false\", meaning: \"a machine's own name for itself\" }\n", 1))
    put('beans/laptop.md', f'''---
bean: laptop
kind: host
title: "laptop"
summary: "Sam's laptop: the garden, and the store its held values are kept in."
statements:
  - read: {{ by: sam, at: now }}
  - own:  {{ by: sam, of: self }}
  - name: {{ by: anchor-hostname, of: self, as: {HOST} }}
details:
  roots:
    vault: {{ system: unix-filesystem, at: "{HOST}:{STORE}", keeps: special-category, readable_from: this-host }}
---
The laptop.
''')
    rc, out = run(PY, 'bin/save.py', 'sam', 'the laptop and its store', '--body',
                  '- action: recorded [[laptop]]. RULE-CHANGE: VOCAB.md names the namespace a machine names itself in.')
    check("the machine and its store are saved", rc == 0, out[-800:])
    rc, out = run(PY, 'bin/held.py', 'person', f'name={NAME}', f'phone={PHONE}')
    m = re.search(r'(p-[0-9a-f]{8}): written', out)
    PID = m.group(1) if m else 'p-none'
    put('beans/lessons.md', f'''---
bean: lessons
kind: contract
title: "lessons"
summary: "Sam teaches the guitar"
statements:
  - say:   {{ by: sam, at: now }}
  - own:   {{ by: theone, of: self }}
  - agree: {{ id: a, by: [sam, {PID}], of: self, through: spoken, at: "2026-09-01" }}
---
Lessons.
''')
    put('beans/page.md', f'''---
bean: page
kind: service
title: "Sam's page"
summary: "the lessons"
statements:
  - say:  {{ by: sam, at: now }}
  - own:  {{ by: sam, of: self }}
  - be:   {{ by: self, at: "uri:https://garden.example.org/", as: location }}
  - draw: {{ id: lessons, by: self, of: [lessons], drawing: {{ label: Lessons, archetype: sheet, {STORY.format(p='the lessons')} }} }}
  - draw: {{ id: page, by: self, of: [lessons], page: {{ fields: [ {{ kind: contract, fact: agree, shown_from: understand }} ] }} }}
---
A page.
''')
    rc, out = run(PY, 'bin/save.py', 'sam', 'a person held off git, the lessons and a page', '--body',
                  f'- action: wrote [[{PID}]], [[lessons]] and [[page]]')
    check("a person is minted with their name and phone held off git, and saved with the lessons and the page — git holds "
          "neither", rc == 0 and NAME not in get(f'beans/{PID}.md') and PHONE not in get(f'beans/{PID}.md'), out[-1500:])

    P = scoped()
    sam, guest = P.get('sam') or {}, P.get('guest') or {}
    ps = (sam.get('sheets') or {}).get(PID) or {}
    being = next((b for b in sam.get('beings') or [] if b.get('id') == PID), {})
    check("to Sam the host calls the person by their held name: their sheet's title, their contact on it, and the being a "
          "role names, marked as a held name", ps.get('title') == NAME and (ps.get('contact') or {}).get('phone') == PHONE
          and being.get('title') == NAME and being.get('held_name') is True, (ps, being, P.get('error')))
    g = json.dumps(guest, ensure_ascii=False)
    check("to the guest, who may read the lessons alone, nothing of the name or the phone anywhere in the page, and no "
          "sheet of the person", guest and NAME not in g and PHONE not in g and PID not in (guest.get('sheets') or {})
          and 'lessons' in (guest.get('sheets') or {}), g[-600:])

    rc, out = run(PY, 'assets/view/bin/view.py', 'report', '--out', os.path.join(T, 'report.html'), '--lang', 'fa')
    rep = open(os.path.join(T, 'report.html'), encoding='utf-8').read() if rc == 0 else out
    check("the report, a page of one file, carries the opaque id and never the name or the phone",
          rc == 0 and PID in rep and NAME not in rep and PHONE not in rep, out[-600:])

    browser = next((b for b in ('chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable') if shutil.which(b)), None)
    if not browser:
        print("NOTE  the page was not drawn in a browser: none on this machine")
    elif sam:
        sys.path.insert(0, os.path.join(ROOT, 'assets', 'view', 'lib'))
        import view_widgets
        LIB = os.path.join(ROOT, 'assets', 'view', 'lib')
        js = view_widgets.bundle() + ''.join(open(os.path.join(LIB, f), encoding='utf-8').read() for f in (
            os.path.join('widgets', 'direction.js'), 'view_engraved.js', 'view_sheet.js'))
        page = """<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><style>%(css)s</style></head>
<body><div id="l" class="vw" dir="rtl"></div><div id="p" class="vw" dir="rtl"></div><script>%(js)s</script><script>
const out = {errs: []}, E = %(payload)s;
window.addEventListener('error', e => out.errs.push(String(e.message)));
try {
  const t = window.daftarEngraved.tools({engraved: E}), A = window.daftarArchetypes;
  A.sheet(document.getElementById('l'), E.sheets.lessons, t, null);
  out.agree = document.querySelector('#l [data-fact="agree#a"] [data-role="by"]').innerText;
  A.sheet(document.getElementById('p'), E.sheets['%(pid)s'], t, null);
  const c = document.querySelector('#p [data-fact="contact"]');
  out.contact = c ? c.innerText : null;
  const ph = c && [...c.querySelectorAll('.eg-detail')].find(x => x.innerText.includes('phone'));
  const v = ph && ph.lastElementChild;
  out.phoneDir = v ? getComputedStyle(v).direction : null;
} catch (e) { out.errs.push('driver: ' + e.message + ' ' + (e.stack || '').split('\\n')[1]); }
const pre = document.createElement('pre'); pre.id = '__out'; pre.textContent = JSON.stringify(out); document.body.appendChild(pre);
</script></body></html>"""
        path = os.path.join(T, 'held.html')
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(page % {'css': view_widgets.css() + open(os.path.join(LIB, 'view_engraved.css'), encoding='utf-8').read(),
                             'js': js, 'payload': json.dumps(sam, ensure_ascii=False), 'pid': PID})
        r = subprocess.run([browser, '--headless=new', '--disable-gpu', '--no-sandbox', '--virtual-time-budget=5000',
                            '--dump-dom', 'file://' + path], capture_output=True, text=True, encoding='utf-8', errors='replace',
                           timeout=180)
        m = re.search(r'<pre id="__out">(.*?)</pre>', r.stdout, re.S)
        B = json.loads(html.unescape(m.group(1))) if m else {'errs': ['no result: ' + r.stderr[-600:]]}
        check("in Persian the lessons' `agree` shows the person by their name", not B['errs'] and NAME in (B.get('agree') or '')
              and PID not in (B.get('agree') or ''), B)
        check("...their sheet shows how to reach them under «نشانی و تماس», the phone left to right as it is written, and "
              "says it is held on this machine only", 'نشانی و تماس' in (B.get('contact') or '') and PHONE in (B.get('contact') or '')
              and B.get('phoneDir') == 'ltr' and 'فقط روی همین دستگاه' in (B.get('contact') or ''), B)

    rc, out = run(PY, 'bin/held.py', 'erase', PID)
    P = scoped()
    ps = ((P.get('sam') or {}).get('sheets') or {}).get(PID) or {}
    s = json.dumps(P, ensure_ascii=False)
    check("once the person is erased from the store, the page calls them by their id again, and holds nothing of them",
          rc == 0 and NAME not in s and PHONE not in s and all(b.get('title') == PID for b in (P.get('sam') or {}).get('beings') or []
                                                              if b.get('id') == PID), (out[-400:], ps))
finally:
    if TRACES:
        print("TRACEBACKS:\n" + "\n---\n".join(TRACES[:3]))
    shutil.rmtree(T, ignore_errors=True)

print(f"\nview_held_names: {len(FAILS)} failed" + (": " + ", ".join(FAILS) if FAILS else ""))
sys.exit(1 if FAILS or TRACES else 0)
