#!/usr/bin/env python3
"""A place on a sheet (assets/view/lib/widgets/place.js; the design's §12): what a person types into where a being is,
answered while they type — the garden's own places first, then what the machine's host finds, then a place service
beyond it — and what lands: a place of the garden as the being it is, any other as a coordinate in its reference system
with the identifier it was read from beside it and a `read` of its source; never a name, since a map's element says
which object was meant and never which being; and nothing about where a person will be asked beyond the machine.

A garden of the core is grown here (test/grow.py) taking the view profile: Sam keeps it; a bookshop says where it is (a
coordinate and the map's element); a café says nowhere yet; another café stands at a street's element; a meeting ahead,
which Sam attends, says when; a page draws a sheet of the café and of the meeting. Then:

  the reading   the page carries the garden's own places a reader may read, each by its title with its coordinate and
                its element, none of another reader's closed beans; and the law's reference systems, WGS 84 accurate to
                2 m, its unit as CLDR names it
  a browser     drawn in Persian, right to left, with a host's lookup standing in for one (it counts what it is asked):
                on the café's sheet, a `be` added and «فلسطین» typed, the machine's street offered with its main and
                secondary line, picked; Save sends the place as a coordinate, latitude first, with its element and the
                source it was read from; the coordinate shown in the reader's digits, left to right in its isolate; on the
                meeting's sheet, its place looked up here alone — the place service beyond the machine never asked
  the write     that add, through the view's one write path (view_write), lands as the law writes a place: the
                coordinate and the element in one `be`, known by Sam's `read` from the map, through its words; the gate
                passes it
  identity      an OpenStreetMap element never establishes an identity: the two cafés at one element both stand, and are
                two; neither is known beyond the garden by it (a proposal's stub carries only names a namespace gives once,
                and a hub compares only those); and a `name` by `osm` is refused, for `osm` is no namespace

Run: python3 test/view_places.py   (0 = green; a NOTE, and no browser check, where no Chromium is on the machine)
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


def py(code):
    """What the view reads in the garden, as JSON: `code` an expression over view_model (vm) and view_engraved (ve)."""
    rc, out = run(PY, '-c', "import json, os, sys; sys.path[:0] = [os.path.join('.', 'assets', 'view', 'lib'), 'bin']; "
                  "import view_model as vm, view_engraved as ve; vm.init('.', 'page'); may = lambda *a, **k: True; "
                  "print(json.dumps(%s, default=str, ensure_ascii=False))" % code)
    try:
        return json.loads(out.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return {'error': out[-1500:]}


T = tempfile.mkdtemp(prefix='view-places-')
REL, G = os.path.join(T, 'release'), os.path.join(T, 'garden-sam')
STORY = ('purpose: "{p}", outcome: "{p}", stages: [{{label: Read, doer: the view}}, {{label: Draw, doer: the view}}, '
         '{{label: Open, doer: the reader}}], questions: [{{lens: orient, ask: "{p}"}}], blind: [{{what: "what nobody wrote down"}}]')
ORG = '''---
bean: {id}
kind: org
title: "{title}"
statements:
  - say:  {{ by: sam, at: now }}
  - own:  {{ by: sam, of: self }}
{more}---
{title}.
'''

try:
    grow.release(REL)
    rc, out = run(PY, os.path.join(REL, 'seed', 'germinate.py'), G, '--gardener', 'sam', '--gardener-name', 'Sam',
                  '--profile', 'view', cwd=T)
    check("a garden of the core grows taking the view profile, kept by Sam", rc == 0, out[-800:])
    run(PY, 'bin/install.py')
    put('beans/bookshop.md', ORG.format(id='bookshop', title='کاخ کتاب', more='  - be:   { id: where, by: self, at: '
        '["EPSG:4326;35.7001,51.4012", "osm:way/9001"], as: location }\n'))
    put('beans/cafe-a.md', ORG.format(id='cafe-a', title='Cafe A', more=''))
    put('beans/cafe-b.md', ORG.format(id='cafe-b', title='Cafe B', more='  - be:   { id: where, by: self, at: '
        '["EPSG:4326;35.6976,51.4023", "osm:way/42"], as: location }\n'))
    put('beans/meeting.md', '''---
bean: meeting
kind: event
title: "meeting"
summary: "a meeting ahead"
statements:
  - say:    { by: sam, at: now }
  - own:    { by: sam, of: self }
  - be:     { id: when, by: self, at: "2099-03-01T10:00+03:30" }
  - attend: { id: goes, by: sam, of: self }
---
A meeting.
''')
    put('beans/page.md', f'''---
bean: page
kind: service
title: "Sam's page"
summary: "the café and the meeting"
statements:
  - say:    {{ by: sam, at: now }}
  - own:    {{ by: sam, of: self }}
  - be:     {{ by: self, at: "uri:https://garden.example.org/", as: location }}
  - draw:   {{ id: cafe, by: self, of: [cafe-a], drawing: {{ label: Cafe, archetype: sheet, {STORY.format(p='the café')} }} }}
  - draw:   {{ id: meet, by: self, of: [meeting], drawing: {{ label: Meeting, archetype: sheet, {STORY.format(p='the meeting')} }} }}
  - draw:   {{ id: page, by: self, of: [cafe, meet], page: {{ fields: [ {{ kind: org, fact: be, shown_from: understand }}, {{ kind: event, fact: be, shown_from: understand }} ] }} }}
---
A page.
''')
    rc, out = run(PY, 'bin/save.py', 'sam', 'a bookshop, two cafés, a meeting and a page', '--body',
                  '- action: wrote [[bookshop]], [[cafe-a]], [[cafe-b]], [[meeting]] and [[page]]')
    check("the bookshop, the cafés, the meeting and the page are saved through the core's gate — the two cafés' places at "
          "one element both standing", rc == 0 and '0 error(s)' in out, out[-1500:])

    # ------------------------------------------------------------------ the reading
    R = py("{'cafe': ve.sheet('cafe-a', may), 'meeting': ve.sheet('meeting', may), 'settings': ve.settings(), "
           "'places': ve.places(may), 'closed': ve.places(lambda act, bean, positions=None: bean == 'cafe-b')}")
    own = {p.get('id'): p for p in R.get('places') or []}
    check("the page carries the garden's own places, each by its title with its coordinate and its element; a being that "
          "says nowhere, or only when, carries none",
          sorted(own) == ['bookshop', 'cafe-b'] and own['bookshop'].get('title') == 'کاخ کتاب'
          and own['bookshop'].get('point') == [35.7001, 51.4012] and own['bookshop'].get('osm') == 'way/9001', R)
    check("...only those the reader may read", [p.get('id') for p in R.get('closed') or []] == ['cafe-b'], R.get('closed'))
    crs = {r.get('crs'): r for r in (R.get('settings') or {}).get('crs') or []}
    check("the page's settings carry the law's reference systems: WGS 84 (EPSG:4326) accurate to 2 m, its unit as CLDR "
          "names it", (crs.get('EPSG:4326') or {}).get('accuracy') == {'count': '2', 'unit': 'length-meter'}, crs)

    # ------------------------------------------------------------------ a browser
    browser = next((b for b in ('chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable') if shutil.which(b)), None)
    body = None
    if not browser:
        print("NOTE  the sheets were not drawn in a browser: none on this machine")
    else:
        sys.path.insert(0, os.path.join(ROOT, 'assets', 'view', 'lib'))
        import view_widgets
        LIB = os.path.join(ROOT, 'assets', 'view', 'lib')
        js = view_widgets.bundle() + ''.join(open(os.path.join(LIB, f), encoding='utf-8').read() for f in (
            os.path.join('widgets', 'direction.js'), 'view_engraved.js', 'view_sheet.js'))
        here = {'places': [{'code': 'zz-tehran-palestine', 'label': 'فلسطین', 'detail': 'تهران', 'kind': 'street',
                            'point': [35.6976, 51.4023], 'osm': 'way/42'}],
                'sources': [{'name': 'OpenStreetMap', 'licence': 'ODbL-1.0', 'attribution': '© OpenStreetMap contributors',
                             'url': 'https://www.openstreetmap.org/copyright'}]}
        page = """<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><style>%(css)s
body{font:18px system-ui,'Noto Sans Arabic',sans-serif}</style></head><body><div id="cafe" class="vw" dir="rtl"></div>
<div id="meeting" class="vw" dir="rtl"></div><div id="shown" dir="rtl"></div><script>%(js)s</script><script>
const SKIP = /[\\u200e\\u200f\\u061c\\u2066-\\u2069\\u202a-\\u202e]/;
function visual(el) {
  const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT), glyphs = [];
  for (let n = w.nextNode(); n; n = w.nextNode()) for (let i = 0; i < n.data.length; i++) {
    const ch = n.data[i]; if (SKIP.test(ch)) continue;
    const r = document.createRange(); r.setStart(n, i); r.setEnd(n, i + 1); const b = r.getBoundingClientRect();
    if (b.width > 0 || ch.trim()) glyphs.push([b.left + b.width / 2, ch]); }
  glyphs.sort((a, b) => a[0] - b[0]);
  return glyphs.map(g => g[1]).join('').replace(/\\s+/g, ' ').trim();
}
const sleep = ms => new Promise(r => setTimeout(r, ms));
const out = {errs: [], asked: {here: [], far: []}};
const E = {settings: Object.assign({}, %(settings)s, {garden: {lang: 'fa'}}), names: {}, places: %(places)s,
           beings: [{id: 'self', title: 'self'}]};
const places = {here: (q, o) => { out.asked.here.push([q, o]); return Promise.resolve(%(here)s); },
                far: (q, o) => { out.asked.far.push([q, o]); return Promise.resolve({places: [], sources: [], sent: true}); }};
window.addEventListener('error', e => out.errs.push(String(e.message)));
(async () => {
  try {
    const A = window.daftarArchetypes, t = state => window.daftarEngraved.tools(Object.assign({engraved: E, places}, state || {}));
    const cafe = document.getElementById('cafe'), meeting = document.getElementById('meeting');
    A.sheet(cafe, %(cafe)s, t({write: body => { out.body = body; return new Promise(() => {}); }}), null);
    cafe.querySelector('[data-do="edit"]').click();
    cafe.querySelector('[data-add="be"]').click();
    const li = cafe.querySelector('li.eg-added[data-verb="be"]');
    const by = li.querySelector('select[name$=".by"]'); by.value = 'self';
    const as = li.querySelector('select[name$=".as"]'); if (as) as.value = 'location';
    const input = li.querySelector('.w-place-input');
    input.value = 'فلسطین'; input.dispatchEvent(new Event('input'));
    await sleep(400);
    const list = li.querySelector('.w-place-list');
    out.options = [...list.querySelectorAll('[role="option"]')].map(o => ({main: o.querySelector('.w-place-main').textContent,
      sub: o.querySelector('.w-place-sub').textContent, visual: visual(o)}));
    out.credit = (list.querySelector('.w-place-credit') || {}).textContent || '';
    out.expanded = input.getAttribute('aria-expanded');
    list.querySelector('[role="option"]').click();
    cafe.querySelector('[data-do="save"]').click();
    const shown = document.getElementById('shown');
    window.daftarWidgets.safe.mount(shown, window.daftarWidgets.safe.h`<p id="p1">جا: ${window.daftarWidgets.place.show(['EPSG:4326;35.6976,51.4023', 'osm:way/42'])}</p>`);
    out.shown = visual(shown.querySelector('#p1 .w-place-coord'));
    out.shownLogical = shown.querySelector('#p1 .w-place-coord').textContent;
    out.shownLine = visual(shown.querySelector('#p1'));
    A.sheet(meeting, %(meeting)s, t({write: () => new Promise(() => {})}), null);
    meeting.querySelector('[data-do="edit"]').click();
    out.whenIsNoPlace = !meeting.querySelector('[data-fact="be#when"] [data-place]');   // its time is no place
    meeting.querySelector('[data-add="be"]').click();
    const mi = meeting.querySelector('li.eg-added .w-place-input');
    out.sealedField = !!meeting.querySelector('.w-place-sealed');
    out.farBefore = out.asked.far.length;
    if (mi) { mi.value = 'فلسطین'; mi.dispatchEvent(new Event('input')); }
    await sleep(400);
    out.farAfter = out.asked.far.length;
  } catch (e) { out.errs.push('driver: ' + e.message + ' ' + (e.stack || '').split('\\n')[1]); }
  const pre = document.createElement('pre'); pre.id = '__out'; pre.textContent = JSON.stringify(out); document.body.appendChild(pre);
})();
</script></body></html>"""
        path = os.path.join(T, 'places.html')
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(page % {'css': view_widgets.css() + open(os.path.join(LIB, 'view_engraved.css'), encoding='utf-8').read(),
                             'js': js, 'settings': json.dumps(R.get('settings') or {}, ensure_ascii=False),
                             'places': json.dumps(R.get('places') or [], ensure_ascii=False),
                             'here': json.dumps(here, ensure_ascii=False),
                             'cafe': json.dumps(R.get('cafe') or {}, ensure_ascii=False),
                             'meeting': json.dumps(R.get('meeting') or {}, ensure_ascii=False)})
        r = subprocess.run([browser, '--headless=new', '--disable-gpu', '--no-sandbox', '--virtual-time-budget=10000',
                            '--dump-dom', 'file://' + path], capture_output=True, text=True, encoding='utf-8', errors='replace',
                           timeout=180)
        m = re.search(r'<pre id="__out">(.*?)</pre>', r.stdout, re.S)
        B = json.loads(html.unescape(m.group(1))) if m else {'errs': ['no result: ' + r.stderr[-600:]]}
        opts = B.get('options') or []
        check("on the café's sheet, «فلسطین» typed into a `be` added: the machine's street offered — its own words on the "
              "main line, where it is and whence it came on the secondary — the map's contributors credited, the list open",
              not B['errs'] and len(opts) == 1 and opts[0].get('main') == 'فلسطین' and 'تهران' in opts[0].get('sub', '')
              and 'روی همین دستگاه' in opts[0].get('sub', '') and 'OpenStreetMap' in B.get('credit', '')
              and B.get('expanded') == 'true', B)
        check("...the host asked with what was typed, and no position: none was asked for",
              (B.get('asked') or {}).get('here', [[None]])[0] == ['فلسطین', {}], B.get('asked'))
        body = B.get('body') or {}
        ops = body.get('ops') or []
        check("Save sends the place picked: a coordinate in WGS 84, latitude first, with the map's element beside it, and "
              "the source it was read from — never a name",
              body.get('bean') == 'cafe-a' and len(ops) == 1 and ops[0].get('op') == 'add' and ops[0].get('verb') == 'be'
              and (ops[0].get('roles') or {}).get('at') == ['EPSG:4326;35.6976,51.4023', 'osm:way/42']
              and (ops[0].get('roles') or {}).get('by') == 'self'
              and (ops[0].get('read') or {}).get('from') == {'someone': 'org', 'at': 'uri:https://www.openstreetmap.org/copyright'}
              and (ops[0].get('read') or {}).get('through', '').startswith('OpenStreetMap way/42'), body)
        check("bidi: the coordinate shown in the reader's digits reads left to right as written, in a right-to-left line; "
              "the line read from its start: «جا:», the coordinate, its system, the accuracy the law states in the reader's "
              "words («±۲متر» as CLDR writes it, the sign going with the Persian digits), then the map's element",
              B.get('shown') == '۳۵٫۶۹۷۶, ۵۱٫۴۰۲۳'
              and re.sub('[\\u2066-\\u2069]', '', B.get('shownLogical') or '') == '۳۵٫۶۹۷۶, ۵۱٫۴۰۲۳'
              and B.get('shownLine') == 'OpenStreetMap way/42 · رتم±۲ EPSG:4326 ۳۵٫۶۹۷۶, ۵۱٫۴۰۲۳ :اج',
              (B.get('shown'), B.get('shownLogical'), B.get('shownLine')))
        check("on the meeting's sheet — a happening, attended — its time stays a time, and a place added to it is looked "
              "up on the machine alone: the field is sealed, and the place service beyond it is never asked",
              B.get('whenIsNoPlace') is True and B.get('sealedField') is True and B.get('farBefore') == B.get('farAfter') == 1, B)
        if ops and (ops[0].get("roles") or {}).get("as") != "location":
            ops[0].setdefault('roles', {})['as'] = 'location'

    # ------------------------------------------------------------------ the write
    if body:
        code = ("import json, os, sys; sys.path[:0] = [os.path.join('.', 'assets', 'view', 'lib'), 'bin']; import view_write; "
                "print(json.dumps(view_write.write('.', 'sam', %r, %r), default=str))" % (body.get('bean'), body.get('ops')))
        rc, out = run(PY, '-c', code)
        try:
            W = json.loads(out.strip().splitlines()[-1])
        except (ValueError, IndexError):
            W = {'ok': False, 'output': out[-1500:]}
        st = py("[{v: r} for _i, v, r in vm.CORE.G.beans['cafe-a'].items]")
        be = next((s['be'] for s in st if 'be' in s), {}) if isinstance(st, list) else {}
        rd = next((s['read'] for s in st if 'read' in s), {}) if isinstance(st, list) else {}
        check("that add, through the view's one write path, lands as the law writes a place — the coordinate and the "
              "element in one `be`, known by Sam's `read` from the map, through its words — and the gate passes it",
              W.get('ok') is True and be.get('at') == ['EPSG:4326;35.6976,51.4023', 'osm:way/42']
              and rd.get('by') == 'sam' and rd.get('of') == [be.get('id')]
              and rd.get('from') == {'someone': 'org', 'at': 'uri:https://www.openstreetmap.org/copyright'}
              and rd.get('through', '').startswith('OpenStreetMap way/42') and not any('name' in s for s in st),
              (W, st))
        rc, out = run(PY, 'core/check.py', '.')
        check("...and the whole garden passes its gate, the two cafés at one element", rc == 0 and '0 error(s)' in out, out[-1200:])

    # ------------------------------------------------------------------ identity
    rc, out = run(PY, '-c', "import json, os, sys; sys.path[:0] = ['bin', '.']; import importlib; "
                  "propose = importlib.import_module('propose'); hub = importlib.import_module('hub'); dmpass = importlib.import_module('pass'); "
                  "from core.check import garden_law; L = garden_law('.'); "
                  "fm = lambda b: propose.core_parse(open('beans/%s.md' % b, encoding='utf-8').read(), b)[0]; "
                  "once = {n for n, r in L.namespaces.items() if str(r.get('once')) == 'true'}; "
                  "print(json.dumps({b: [propose.core_names(fm(b), L), hub._anchors(fm(b), once)] for b in ('cafe-b', 'bookshop')}))")
    try:
        I = json.loads(out.strip().splitlines()[-1])
    except (ValueError, IndexError):
        I = {'error': out[-1200:]}
    check("an OpenStreetMap element never establishes an identity: a being at one is known beyond its garden by no name "
          "from it (a proposal's stub carries only names a namespace gives once), and a hub compares nothing of it",
          I.get('cafe-b') == [[], []] and I.get('bookshop') == [[], []], I)
    put('beans/cafe-b.md', open(os.path.join(G, 'beans', 'cafe-b.md'), encoding='utf-8').read().replace(
        '  - be:', '  - name: { by: osm, of: self, as: "way/42" }\n  - be:', 1))
    rc, out = run(PY, 'core/check.py', '.')
    check("...and a `name` by `osm` is refused: `osm` is a system of positions, no namespace that names a being",
          rc != 0 and 'osm' in out and 'cafe-b' in out, out[-1200:])
finally:
    if TRACES:
        print("TRACEBACKS:\n" + "\n---\n".join(TRACES[:3]))
    shutil.rmtree(T, ignore_errors=True)

print(f"\nview_places: {len(FAILS)} failed" + (": " + ", ".join(FAILS) if FAILS else ""))
sys.exit(1 if FAILS or TRACES else 0)
