#!/usr/bin/env python3
"""Each reader's own way of reading (assets/view/lib/view_prefs.py, widgets/prefs.js): their language as one BCP 47 tag
whose Unicode keys (UTS #35) say their calendar, digits, hour cycle, first day of the week and the zone moments are shown
in, and beside it how a day is written and a currency named — kept with their account on the host, never in the garden.

A garden of the core is grown here (test/grow.py) taking the view profile: Sam keeps it, and a repair's deposit was paid
on a day; a page draws its sheet. The view's own host serves it to Sam and to a reader. Then:

  the tag       read by the grammar of RFC 5646 and CLDR's own types (seed/knowledge/cldr-bcp47.tsv): a good tag kept
                in its canonical order; a bad one — a key CLDR has no such type of, a key no reader sets, an empty part —
                refused with a sentence
  the host      Sam chooses English, the Persian calendar, Latin digits, twelve hours, New York's zone, a full date and
                currencies by name; their page carries them and the reader's does not; they hold after Sam signs out and
                in again, and in a second browser; the garden gains no commit and no change, and the host's own file
                keeps them
  a browser     Sam's sheet in their choice — the day in the Persian calendar in English with its weekday, Latin digits,
                the moment it was said in New York's time on a twelve-hour clock, the euro by its name, left to right;
                the reader's in their language's own, unset — Persian, the Persian calendar, Persian digits, right to
                left; a day Sam types in their calendar is saved as the same day; the panel draws its sample in either
                direction

Run: python3 test/view_reader_prefs.py   (0 = green; a NOTE, and no browser check, where no Chromium is on the machine)
"""
import html, http.cookiejar, json, os, re, shutil, socket, subprocess, sys, tempfile, time, urllib.error, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'assets', 'view', 'lib'), os.path.join(ROOT, 'test')]
import grow  # noqa: E402
try:
    import view_prefs  # noqa: E402
except ImportError:                       # a release whose view keeps no reader's preferences: every check below fails
    view_prefs = None

PY = sys.executable
FAILS, TRACES = [], []
READER = 'p-0a1b2c3d'


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


# ------------------------------------------------------------------ the tag
if view_prefs is None:
    class view_prefs:                     # noqa: N801 — what a release without it answers: nothing kept, nothing refused
        check = staticmethod(lambda p: ({}, []))
kept, bad = view_prefs.check({'locale': 'fa-u-nu-arabext-ca-persian-hc-h23-fw-sat', 'date': 'long'})
check("a good tag is kept in its canonical order, beside how a day is written",
      kept == {'locale': 'fa-u-ca-persian-fw-sat-hc-h23-nu-arabext', 'date': 'long'} and not bad, (kept, bad))
refused = {t: view_prefs.check({'locale': t})[1] for t in ('fa-u-ca-nonsense', 'fa-u-co-phonebk', 'fa--u', 'fa-u-tz-nowhere')}
check("a bad tag is refused with a sentence: a type CLDR has not, a key no reader sets, an empty part, a zone CLDR names not",
      all(refused.values()) and 'ca' in refused['fa-u-ca-nonsense'][0] and 'co' in refused['fa-u-co-phonebk'][0], refused)
check("...and a date's style and a currency's naming only Intl's", view_prefs.check({'date': 'longest'})[1]
      and view_prefs.check({'currency': 'emoji'})[1], (view_prefs.check({'date': 'longest'}), view_prefs.check({'currency': 'emoji'})))

T = tempfile.mkdtemp(prefix='view-prefs-')
REL, G = os.path.join(T, 'release'), os.path.join(T, 'garden-sam')
STORY = ('purpose: "{p}", outcome: "{p}", stages: [{{label: Read, doer: the view}}, {{label: Draw, doer: the view}}, '
         '{{label: Open, doer: the reader}}], questions: [{{lens: orient, ask: "{p}"}}], blind: [{{what: "what nobody wrote down"}}]')
srv = None
try:
    grow.release(REL)
    rc, out = run(PY, os.path.join(REL, 'seed', 'germinate.py'), G, '--gardener', 'sam', '--gardener-name', 'Sam',
                  '--profile', 'view', cwd=T)
    check("a garden of the core grows taking the view profile, kept by Sam", rc == 0, out[-800:])
    run(PY, 'bin/install.py')
    put(f'beans/{READER}.md', f'---\nbean: {READER}\nkind: person\ntitle: "{READER}"\nsummary: "a reader of the page"\nstatements:\n'
        '  - say: { by: sam, at: now }\n  - own: { by: theone, of: self }\n---\nA reader.\n')
    put('beans/repair-1.md', '''---
bean: repair-1
kind: contract
title: "repair-1 — a bicycle"
summary: "Sam mends a bicycle"
statements:
  - say: { by: sam, at: now }
  - own: { by: theone, of: self }
  - pay: { id: deposit, by: sam, of: { count: "25.00", unit: EUR }, at: "2026-09-24" }
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
  - draw: {{ id: page, by: self, of: [repair], page: {{ visibility: private, fields: [ {{ kind: contract, fact: pay, shown_from: understand }} ] }} }}
---
A page.
''')
    sam = open(os.path.join(G, 'beans', 'sam.md'), encoding='utf-8').read()
    put('beans/sam.md', sam.replace('\n---\n', f'\n  - grant: {{ id: reader-reads, by: self, to: [{READER}], of: [page, repair-1], as: read }}\n'
                                    '  - say: { by: sam, of: [reader-reads], at: now }\n---\n', 1))
    rc, out = run(PY, 'bin/save.py', 'sam', 'a repair, a reader, and a page of its sheet', '--body',
                  f'- action: wrote [[{READER}]], [[repair-1]] and [[page]]; [[sam]] opens the page and the repair to the reader')
    check("the repair, the reader and the page are saved through the gate", rc == 0 and '0 error(s)' in out, out[-1200:])
    head = lambda: subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=G, capture_output=True, text=True, encoding='utf-8').stdout.strip()
    before = head()

    CFG = os.path.join(T, 'host', 'serve.json')
    for user, bean in (('sam', 'sam'), ('reader', READER)):
        run(PY, 'assets/view/bin/view.py', 'serve-init', '--config', CFG, '--user', user, '--bean', bean)
    s_ = socket.socket(); s_.bind(('127.0.0.1', 0)); PORT = s_.getsockname()[1]; s_.close()
    C = json.load(open(CFG)); C.update(listen='127.0.0.1:%d' % PORT, recheck_seconds=1, request_seconds=5)
    C['users']['sam']['lang'] = 'fa'; C['users']['reader']['lang'] = 'fa'
    json.dump(C, open(CFG, 'w'))
    srv = subprocess.Popen([PY, 'assets/view/bin/view.py', 'serve', '--config', CFG], cwd=G, stderr=subprocess.PIPE,
                           text=True, encoding='utf-8', env=grow.ENV)
    BASE = 'http://127.0.0.1:%d' % PORT
    for _ in range(100):
        try:
            urllib.request.urlopen(BASE + '/healthz', timeout=1); break
        except Exception:
            time.sleep(0.2)

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None

    def session(user):
        op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()), NoRedirect)
        pw = open(os.path.join(T, 'host', user + '.password')).read().strip()
        try:
            op.open(BASE + '/login', urllib.parse.urlencode({'user': user, 'password': pw}).encode())
        except urllib.error.HTTPError:
            pass
        return op

    def page_of(op):
        try:
            r = op.open(BASE + '/'); text = r.read().decode()
        except urllib.error.HTTPError as e:
            return e.code, {}
        m = re.search(r'<script type="application/json" id="viewdata">(.*?)</script>', text, re.S)
        return 200, (json.loads(m.group(1).replace('<\\/', '</')) if m else {})

    def post(op, path, obj, csrf):
        req = urllib.request.Request(BASE + path, json.dumps(obj).encode(), {'Content-Type': 'application/json', 'X-View-CSRF': csrf})
        try:
            r = op.open(req, timeout=60); return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b'{}')

    reader_of = lambda P: ((P.get('engraved') or {}).get('settings') or {}).get('reader')
    SAM, RDR = session('sam'), session('reader')
    st, PS = page_of(SAM)
    st2, PR = page_of(RDR)
    check("unset, a reader's page carries nothing of their own: their language's own stands", st == 200 and st2 == 200
          and reader_of(PS) == {} and reader_of(PR) == {}, (st, st2, reader_of(PS), reader_of(PR)))
    csrf = (PS.get('live') or {}).get('csrf', '')
    code, ans = post(SAM, '/api/prefs', {'locale': 'en-u-ca-persian-nu-latn-hc-h12-tz-usnyc'.replace('-tz-usnyc', '-tz-usnyc'), 'date': 'full'}, '')
    check("a preference is a write: without the page's CSRF token it is refused", code == 403, (code, ans))
    code, ans = post(SAM, '/api/prefs', {'locale': 'en-u-ca-persian-co-phonebk'}, csrf)
    check("a bad tag is refused by the host with a sentence, and nothing is kept", code == 400 and 'co' in ans.get('error', '')
          and reader_of(page_of(SAM)[1]) == {}, (code, ans))
    WANT = {'locale': 'en-u-ca-persian-hc-h12-nu-latn-tz-usnyc', 'zone': 'America/New_York', 'date': 'full', 'currency': 'name'}
    code, ans = post(SAM, '/api/prefs', {'locale': 'en-u-nu-latn-ca-persian-hc-h12-tz-usnyc', 'date': 'full', 'currency': 'name'}, csrf)
    st, PS = page_of(SAM)
    st2, PR = page_of(RDR)
    check("Sam's choice is kept and their page carries it — their tag in its canonical order, the zone its `tz` stands for — "
          "and the reader's page does not", code == 200 and reader_of(PS) == WANT and reader_of(PR) == {}, (code, ans, reader_of(PS), reader_of(PR)))
    out_ = post(SAM, '/logout', {}, (PS.get('live') or {}).get('csrf', ''))
    again, other = session('sam'), session('sam')
    PA, PO = page_of(again), page_of(other)
    check("...and it holds after they sign out and in again, and in a second browser", reader_of(PA[1]) == WANT
          and reader_of(PO[1]) == WANT, (out_, PA[0], PO[0], reader_of(PA[1]), reader_of(PO[1])))
    gs = subprocess.run(['git', 'status', '--porcelain'], cwd=G, capture_output=True, text=True, encoding='utf-8').stdout.strip()
    check("no commit is made to the garden by a preference, and nothing in it changed; the host's own file keeps it",
          head() == before and gs == '' and json.load(open(CFG))['users']['sam'].get('locale') == WANT['locale'], (head(), before, gs))

    browser = next((b for b in ('chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable') if shutil.which(b)), None)
    if not browser:
        print("NOTE  the pages were not drawn in a browser: none on this machine")
    else:
        import view_widgets
        LIB = os.path.join(ROOT, 'assets', 'view', 'lib')
        js = view_widgets.bundle() + ''.join(open(os.path.join(LIB, f), encoding='utf-8').read() for f in (
            os.path.join('widgets', 'direction.js'), 'view_engraved.js', 'view_sheet.js'))
        page = """<!doctype html><html><head><meta charset="utf-8"><style>%(css)s</style></head>
<body><div id="s" class="vw light"></div><div id="p"></div><script>%(js)s</script><script>
const out = {errs: []}, E = %(engraved)s, W = window.daftarWidgets;
window.addEventListener('error', e => out.errs.push(String(e.message)));
try {
  W.settings.configure(E.settings);
  const lang = W.locale.langOf({}); document.documentElement.lang = lang; document.documentElement.dir = W.locale.dirOf(lang);
  const el = document.getElementById('s');
  window.daftarArchetypes.sheet(el, E.sheets['repair-1'], window.daftarEngraved.tools({engraved: E, write: b => { out.body = b; return new Promise(() => {}); }}), null);
  out.dir = document.documentElement.dir; out.text = el.innerText;
  const edit = el.querySelector('[data-do="edit"]');
  if (edit) {
    edit.click();
    const day = el.querySelector('[data-fact="pay#deposit"] .w-moment-input');
    out.field = day ? day.value : null;
    out.back = W.moment.take(out.field || '').value;
    if (day) day.value = %(typed)s;
    el.querySelector('[data-do="save"]').click();
  }
  W.prefs.open(document.getElementById('p'), (E.settings.reader || {}), {languages: ['fa', 'en'], zones: [['usnyc', 'America/New_York']], currency: 'EUR'}, () => ({ok: true}));
  out.sample = document.querySelector('#p .w-prefs-sample').innerText;
} catch (e) { out.errs.push('driver: ' + e.message + ' ' + (e.stack || '').split('\\n')[1]); }
const pre = document.createElement('pre'); pre.id = '__out'; pre.textContent = JSON.stringify(out); document.body.appendChild(pre);
</script></body></html>"""
        res = {}
        for who, P_, typed in (('sam', PA[1], '7/9/1405'), ('reader', PR, '')):
            path = os.path.join(T, f'prefs-{who}.html')
            with open(path, 'w', encoding='utf-8') as fh:
                fh.write(page % {'css': view_widgets.css() + open(os.path.join(LIB, 'view_engraved.css'), encoding='utf-8').read(),
                                 'js': js, 'engraved': json.dumps(P_.get('engraved') or {}, ensure_ascii=False), 'typed': json.dumps(typed)})
            r = subprocess.run([browser, '--headless=new', '--disable-gpu', '--no-sandbox', '--virtual-time-budget=5000',
                                '--dump-dom', 'file://' + path], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=180)
            m = re.search(r'<pre id="__out">(.*?)</pre>', r.stdout, re.S)
            res[who] = json.loads(html.unescape(m.group(1))) if m else {'errs': ['no result: ' + r.stderr[-600:]]}
        S, R = res['sam'], res['reader']
        st_ = S.get('text') or ''
        check("Sam's sheet in their choice: the day in the Persian calendar, in English with its weekday, Latin digits, the "
              "euro by its name, left to right", not S['errs'] and S.get('dir') == 'ltr' and 'Mehr' in st_ and '1405' in st_
              and re.search(r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)', st_) and 'euro' in st_.lower()
              and not re.search('[۰-۹]', st_), S)
        check("...the moment it was said, in New York's time on a twelve-hour clock", re.search(r'\d{1,2}:\d{2}\s?(AM|PM)', st_), st_)
        rt = R.get('text') or ''
        check("the reader's sheet in their language's own: Persian, the Persian calendar, Persian digits, right to left",
              not R['errs'] and R.get('dir') == 'rtl' and 'مهر' in rt and re.search('[۰-۹]', rt) and 'Mehr' not in rt, R)
        ops = ((S.get('body') or {}).get('ops') or [])
        check("a day Sam types in their calendar (7/9/1405, as English writes a day) is saved as the same day, 2026-10-01; the "
          "day shown in their field reads back as the day it is",
              re.fullmatch(r'0?7/0?2/1405( AP)?', S.get('field') or '') and S.get('back') == '2026-09-24' and len(ops) == 1
              and (ops[0].get('roles') or {}).get('at') == '2026-10-01', (S.get('field'), S.get('back'), ops))
        check("the panel draws its sample in either direction: Latin digits for Sam, Persian for the reader",
              S.get('sample') and R.get('sample') and not re.search('[۰-۹]', S['sample']) and re.search('[۰-۹]', R['sample']),
              (S.get('sample'), R.get('sample')))
finally:
    if srv:
        srv.terminate()
        try:
            srv.wait(timeout=10)
        except subprocess.TimeoutExpired:
            srv.kill()
    if TRACES:
        print("TRACEBACKS:\n" + "\n---\n".join(TRACES[:3]))
    shutil.rmtree(T, ignore_errors=True)

print(f"\nview_reader_prefs: {len(FAILS)} failed" + (": " + ", ".join(FAILS) if FAILS else ""))
sys.exit(1 if FAILS or TRACES else 0)
