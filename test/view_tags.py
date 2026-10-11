#!/usr/bin/env python3
"""A being's tags, where its page names them among its facts (`fields`): drawn on its sheet, each a word of its own, and
changed in the one Edit — written through the view's one write path (assets/view/lib/view_write.py) as a set of words,
and judged by the core's gate.

A garden of the core is grown here (test/grow.py) taking the view profile: Sam keeps it, and a repair of a bicycle is
tagged `bicycle` and «فوری»; a second repair has no tags; a page names a contract's tags and draws both sheets. Then:

  a browser     in Persian, right to left: the first sheet shows its two tags, each a word of its own; Edit offers them as
                one field, the words parted by the reader's own comma («،»); a third word added, Save sends one change of
                the tags, the three words in order
  the write     that change, through the one write path, passes the gate and the bean holds the three; on the second
                repair, tags written where there were none; then all taken out, and the key goes; a list with a word twice,
                an empty word, or a word of two lines is refused at the tags and nothing is written

Run: python3 test/view_tags.py   (0 = green; a NOTE, and no browser check, where no Chromium is on the machine)
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


def write(bean, ops):
    """The one write path, as a served page's Save calls it, for Sam; then the bean's tags as they stand."""
    rc, out = run(PY, '-c', "import json, os, sys; sys.path[:0] = [os.path.join('.', 'assets', 'view', 'lib'), 'bin']; "
                  "import view_write; print(json.dumps(view_write.write('.', 'sam', %r, %r), default=str))" % (bean, ops))
    try:
        res = json.loads(out.strip().splitlines()[-1])
    except (ValueError, IndexError):
        res = {'ok': False, 'output': out[-1500:]}
    with open(os.path.join(G, 'beans', f'{bean}.md'), encoding='utf-8') as fh:
        head = fh.read().split('\n---\n', 1)[0]
    import yaml
    return res, yaml.safe_load(head.lstrip('-\n')).get('tags', 'absent')


T = tempfile.mkdtemp(prefix='view-tags-')
REL, G = os.path.join(T, 'release'), os.path.join(T, 'garden-sam')
STORY = ('purpose: "{p}", outcome: "{p}", stages: [{{label: Read, doer: the view}}, {{label: Draw, doer: the view}}, '
         '{{label: Open, doer: the reader}}], questions: [{{lens: orient, ask: "{p}"}}], blind: [{{what: "what nobody wrote down"}}]')

try:
    grow.release(REL)
    rc, out = run(PY, os.path.join(REL, 'seed', 'germinate.py'), G, '--gardener', 'sam', '--gardener-name', 'Sam',
                  '--profile', 'view', cwd=T)
    check("a garden of the core grows taking the view profile, kept by Sam", rc == 0, out[-800:])
    run(PY, 'bin/install.py')
    for bid, tags in (('repair-1', 'tags: [bicycle, فوری]\n'), ('repair-2', '')):
        put(f'beans/{bid}.md', f'''---
bean: {bid}
kind: contract
title: "{bid}"
summary: "Sam mends a bicycle"
{tags}statements:
  - say: {{ by: sam, at: now }}
  - own: {{ by: theone, of: self }}
---
A repair.
''')
    put('beans/page.md', f'''---
bean: page
kind: service
title: "Sam's page"
summary: "the repairs"
statements:
  - say:  {{ by: sam, at: now }}
  - own:  {{ by: sam, of: self }}
  - be:   {{ by: self, at: "uri:https://garden.example.org/", as: location }}
  - draw: {{ id: one, by: self, of: [repair-1], drawing: {{ label: One, archetype: sheet, {STORY.format(p='a repair')} }} }}
  - draw: {{ id: two, by: self, of: [repair-2], drawing: {{ label: Two, archetype: sheet, {STORY.format(p='a repair')} }} }}
  - draw: {{ id: page, by: self, of: [one, two], page: {{ fields: [ {{ kind: contract, fact: tags, shown_from: understand }} ] }} }}
---
A page.
''')
    rc, out = run(PY, 'bin/save.py', 'sam', 'two repairs and a page of their sheets', '--body',
                  '- action: wrote [[repair-1]], [[repair-2]] and [[page]]')
    check("the repairs and the page are saved through the core's gate", rc == 0 and '0 error(s)' in out, out[-1500:])
    rc, out = run(PY, '-c', "import json, os, sys; sys.path[:0] = [os.path.join('.', 'assets', 'view', 'lib'), 'bin']; "
                  "import view_model as vm, view_engraved as ve; vm.init('.', 'page'); "
                  "print(json.dumps({'sheet': ve.sheet('repair-1', lambda *a, **k: True), 'settings': ve.settings()}, default=str))")
    try:
        R = json.loads(out.strip().splitlines()[-1])
    except (ValueError, IndexError):
        R = {'error': out[-1500:]}

    browser = next((b for b in ('chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable') if shutil.which(b)), None)
    body = {'bean': 'repair-1', 'ops': [{'op': 'change', 'header': 'tags', 'value': ['bicycle', 'فوری', 'رنگ']}]}
    if not browser:
        print("NOTE  the sheet was not drawn in a browser: none on this machine; the write is checked with the change it sends")
    else:
        sys.path.insert(0, os.path.join(ROOT, 'assets', 'view', 'lib'))
        import view_widgets
        LIB = os.path.join(ROOT, 'assets', 'view', 'lib')
        js = view_widgets.bundle() + ''.join(open(os.path.join(LIB, f), encoding='utf-8').read() for f in (
            os.path.join('widgets', 'direction.js'), 'view_engraved.js', 'view_sheet.js'))
        page = """<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><style>%(css)s</style></head>
<body><div id="s" class="vw" dir="rtl"></div><script>%(js)s</script><script>
const out = {errs: []}, E = {settings: Object.assign({}, %(settings)s, {garden: {lang: 'fa'}}), names: {}};
window.addEventListener('error', e => out.errs.push(String(e.message)));
try {
  const el = document.getElementById('s');
  window.daftarArchetypes.sheet(el, %(sheet)s, window.daftarEngraved.tools({engraved: E, write: b => { out.body = b; return new Promise(() => {}); }}), null);
  out.tags = [...el.querySelectorAll('[data-fact="header:tags"] .eg-tag')].map(x => x.textContent.replace(/[\\u2066-\\u2069]/g, ''));
  el.querySelector('[data-do="edit"]').click();
  const f = el.querySelector('[name="header.tags"]');
  out.field = f ? f.value : null;
  if (f) f.value = f.value + '، رنگ';
  el.querySelector('[data-do="save"]').click();
} catch (e) { out.errs.push('driver: ' + e.message + ' ' + (e.stack || '').split('\\n')[1]); }
const pre = document.createElement('pre'); pre.id = '__out'; pre.textContent = JSON.stringify(out); document.body.appendChild(pre);
</script></body></html>"""
        path = os.path.join(T, 'tags.html')
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(page % {'css': view_widgets.css() + open(os.path.join(LIB, 'view_engraved.css'), encoding='utf-8').read(),
                             'js': js, 'settings': json.dumps(R.get('settings') or {}),
                             'sheet': json.dumps(R.get('sheet') or {}, ensure_ascii=False)})
        r = subprocess.run([browser, '--headless=new', '--disable-gpu', '--no-sandbox', '--virtual-time-budget=5000',
                            '--dump-dom', 'file://' + path], capture_output=True, text=True, encoding='utf-8', errors='replace',
                           timeout=180)
        m = re.search(r'<pre id="__out">(.*?)</pre>', r.stdout, re.S)
        B = json.loads(html.unescape(m.group(1))) if m else {'errs': ['no result: ' + r.stderr[-600:]]}
        check("in Persian the sheet shows its two tags, each a word of its own", not B['errs'] and B.get('tags') == ['bicycle', 'فوری'], B)
        check("Edit offers them as one field, parted by the reader's comma («،»); a third word added, Save sends one change "
              "of the tags, the three in order", B.get('field') == 'bicycle، فوری' and B.get('body') == body, B)
        body = B.get('body') or body

    res, tags = write(body['bean'], body['ops'])
    check("that change, through the one write path, passes the gate, and the bean holds the three",
          res.get('ok') is True and tags == ['bicycle', 'فوری', 'رنگ'], (res, tags))
    res, tags = write('repair-2', [{'op': 'change', 'header': 'tags', 'value': ['bicycle']}])
    check("...tags written on a bean that had none", res.get('ok') is True and tags == ['bicycle'], (res, tags))
    res, tags = write('repair-2', [{'op': 'change', 'header': 'tags', 'value': []}])
    check("...and all taken out: the key goes", res.get('ok') is True and tags == 'absent', (res, tags))
    for bad, why in ((['bicycle', 'bicycle'], 'a word twice'), (['bicycle', ' '], 'an empty word'),
                     (['two\nlines'], 'a word of two lines'), ('bicycle', 'a word, not a list')):
        res, tags = write('repair-1', [{'op': 'change', 'header': 'tags', 'value': bad}])
        check(f"{why} is refused at the tags, and nothing is written", res.get('ok') is False
              and any(x.get('fact') == 'header:tags' for x in res.get('refusals') or []) and tags == ['bicycle', 'فوری', 'رنگ'],
              (res, tags))
finally:
    if TRACES:
        print("TRACEBACKS:\n" + "\n---\n".join(TRACES[:3]))
    shutil.rmtree(T, ignore_errors=True)

print(f"\nview_tags: {len(FAILS)} failed" + (": " + ", ".join(FAILS) if FAILS else ""))
sys.exit(1 if FAILS or TRACES else 0)
