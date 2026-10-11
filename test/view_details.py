#!/usr/bin/env python3
"""What a page names of a being's `details` (its `fields`), drawn on the sheet: what fits no verb yet, kept whole until
one is proposed — key by key as it is held, each value by the widget of what it looks like (a day in the reader's
calendar, an amount at its currency's places, words), a map's keys beneath its own, and never edited there.

A garden of the core is grown here (test/grow.py) taking the view profile: Sam keeps it, and a repair of a bicycle keeps
in `details` the day it was brought in, a deposit, and how the owner was found; a page names those three for a
contract and draws its sheet. Then:

  the reading   the sheet carries the three, as written, and nothing of `details` the page does not name
  a browser     in Persian, right to left: the sheet draws them under «نگه‌داشته‌شده به همان شکل», the day in the Persian
                calendar and digits, the deposit at its currency's places in Persian digits, the map's keys beneath its
                own; in English the same day in the Gregorian calendar; Edit still shows them and offers no field for
                them, and Save with nothing changed sends nothing

Run: python3 test/view_details.py   (0 = green; a NOTE, and no browser check, where no Chromium is on the machine)
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


T = tempfile.mkdtemp(prefix='view-details-')
REL, G = os.path.join(T, 'release'), os.path.join(T, 'garden-sam')
STORY = ('purpose: "{p}", outcome: "{p}", stages: [{{label: Read, doer: the view}}, {{label: Draw, doer: the view}}, '
         '{{label: Open, doer: the reader}}], questions: [{{lens: orient, ask: "{p}"}}], blind: [{{what: "what nobody wrote down"}}]')

try:
    grow.release(REL)
    rc, out = run(PY, os.path.join(REL, 'seed', 'germinate.py'), G, '--gardener', 'sam', '--gardener-name', 'Sam',
                  '--profile', 'view', cwd=T)
    check("a garden of the core grows taking the view profile, kept by Sam", rc == 0, out[-800:])
    run(PY, 'bin/install.py')
    put('beans/repair-1.md', '''---
bean: repair-1
kind: contract
title: "repair-1"
summary: "Sam mends a bicycle"
details:
  brought_in: "2026-09-24"
  deposit: { count: "25.00", unit: XTS }
  found_through: { channel: "a neighbour", said: "the blue one" }
  workbench: "the second"
statements:
  - say: { by: sam, at: now }
  - own: { by: theone, of: self }
---
A repair.
''')
    put('beans/page.md', f'''---
bean: page
kind: service
title: "Sam's page"
summary: "a repair"
statements:
  - say:  {{ by: sam, at: now }}
  - own:  {{ by: sam, of: self }}
  - be:   {{ by: self, at: "uri:https://garden.example.org/", as: location }}
  - draw: {{ id: repair, by: self, of: [repair-1], drawing: {{ label: Repair, archetype: sheet, {STORY.format(p='the repair')} }} }}
  - draw: {{ id: page, by: self, of: [repair], page: {{ fields: [ {{ kind: contract, fact: brought_in, shown_from: understand }}, {{ kind: contract, fact: deposit, shown_from: understand }}, {{ kind: contract, fact: found_through, shown_from: understand }} ] }} }}
---
A page.
''')
    rc, out = run(PY, 'bin/save.py', 'sam', 'a repair and a page of its sheet', '--body', '- action: wrote [[repair-1]] and [[page]]')
    check("the repair and the page are saved through the core's gate", rc == 0 and '0 error(s)' in out, out[-1500:])

    rc, out = run(PY, '-c', "import json, os, sys; sys.path[:0] = [os.path.join('.', 'assets', 'view', 'lib'), 'bin']; "
                  "import view_model as vm, view_engraved as ve; vm.init('.', 'page'); "
                  "print(json.dumps({'sheet': ve.sheet('repair-1', lambda *a, **k: True), 'settings': ve.settings()}, default=str))")
    try:
        R = json.loads(out.strip().splitlines()[-1])
    except (ValueError, IndexError):
        R = {'error': out[-1500:]}
    D = (R.get('sheet') or {}).get('details')
    check("the sheet carries the three `details` keys the page names, as written, and not the one it does not name",
          D == {'brought_in': '2026-09-24', 'deposit': {'count': '25.00', 'unit': 'XTS'},
                'found_through': {'channel': 'a neighbour', 'said': 'the blue one'}}, D or R.get('error'))

    browser = next((b for b in ('chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable') if shutil.which(b)), None)
    if not browser:
        print("NOTE  the sheet was not drawn in a browser: none on this machine")
    else:
        sys.path.insert(0, os.path.join(ROOT, 'assets', 'view', 'lib'))
        import view_widgets
        LIB = os.path.join(ROOT, 'assets', 'view', 'lib')
        js = view_widgets.bundle() + ''.join(open(os.path.join(LIB, f), encoding='utf-8').read() for f in (
            os.path.join('widgets', 'direction.js'), 'view_engraved.js', 'view_sheet.js'))
        page = """<!doctype html><html lang="%(lang)s" dir="%(dir)s"><head><meta charset="utf-8"><style>%(css)s</style></head>
<body><div id="s" class="vw" dir="%(dir)s"></div><script>%(js)s</script><script>
const out = {errs: []}, E = {settings: Object.assign({}, %(settings)s, {garden: {lang: '%(lang)s'}}), names: {}};
window.addEventListener('error', e => out.errs.push(String(e.message)));
try {
  const el = document.getElementById('s');
  window.daftarArchetypes.sheet(el, %(sheet)s, window.daftarEngraved.tools({engraved: E, write: b => { out.body = b; return new Promise(() => {}); }}), null);
  const d = el.querySelector('[data-fact="details"]');
  out.text = d ? d.innerText : null;
  out.keys = d ? [...d.querySelectorAll('[data-detail]')].map(x => x.dataset.detail) : [];
  out.map = d ? [...d.querySelectorAll('.eg-details-map dt')].map(x => x.textContent) : [];
  el.querySelector('[data-do="edit"]').click();
  const e = el.querySelector('[data-fact="details"]');
  out.editFields = e ? e.querySelectorAll('input, textarea, select').length : -1;
  el.querySelector('[data-do="save"]').click();
} catch (e) { out.errs.push('driver: ' + e.message + ' ' + (e.stack || '').split('\\n')[1]); }
const pre = document.createElement('pre'); pre.id = '__out'; pre.textContent = JSON.stringify(out); document.body.appendChild(pre);
</script></body></html>"""
        B = {}
        for lang, d in (('fa', 'rtl'), ('en', 'ltr')):
            path = os.path.join(T, f'details-{lang}.html')
            with open(path, 'w', encoding='utf-8') as fh:
                fh.write(page % {'css': view_widgets.css() + open(os.path.join(LIB, 'view_engraved.css'), encoding='utf-8').read(),
                                 'js': js, 'lang': lang, 'dir': d, 'settings': json.dumps(R.get('settings') or {}),
                                 'sheet': json.dumps(R.get('sheet') or {}, ensure_ascii=False)})
            r = subprocess.run([browser, '--headless=new', '--disable-gpu', '--no-sandbox', '--virtual-time-budget=5000',
                                '--dump-dom', 'file://' + path], capture_output=True, text=True, encoding='utf-8',
                               errors='replace', timeout=180)
            m = re.search(r'<pre id="__out">(.*?)</pre>', r.stdout, re.S)
            B[lang] = json.loads(html.unescape(m.group(1))) if m else {'errs': ['no result: ' + r.stderr[-600:]]}
        fa, en = B['fa'], B['en']
        check("in Persian the sheet draws the three under «نگه‌داشته‌شده به همان شکل», in the order the bean holds them, "
              "the map's keys beneath its own", not fa['errs'] and 'نگه‌داشته‌شده به همان شکل' in (fa.get('text') or '')
              and fa.get('keys') == ['brought_in', 'deposit', 'found_through'] and fa.get('map') == ['channel', 'said'], fa)
        check("...the day in the Persian calendar and digits (۲ مهر ۱۴۰۵), the deposit at its places in Persian digits (۲۵٫۰۰)",
              '۱۴۰۵' in (fa.get('text') or '') and 'مهر' in (fa.get('text') or '') and '۲۵٫۰۰' in (fa.get('text') or '')
              and '2026' not in (fa.get('text') or ''), fa.get('text'))
        check("in English the same day in the Gregorian calendar, the deposit 25.00", not en['errs']
              and '2026' in (en.get('text') or '') and '25.00' in (en.get('text') or '') and 'Kept whole' in (en.get('text') or ''),
              en.get('text'))
        check("Edit still shows what `details` keeps and offers no field for it, and Save with nothing changed sends nothing",
              fa.get('editFields') == 0 and en.get('editFields') == 0 and 'body' not in fa and 'body' not in en, (fa, en))
finally:
    if TRACES:
        print("TRACEBACKS:\n" + "\n---\n".join(TRACES[:3]))
    shutil.rmtree(T, ignore_errors=True)

print(f"\nview_details: {len(FAILS)} failed" + (": " + ", ".join(FAILS) if FAILS else ""))
sys.exit(1 if FAILS or TRACES else 0)
