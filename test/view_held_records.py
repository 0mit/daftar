#!/usr/bin/env python3
"""A record held off git, written from a page: what a being points to off git — a person's contact, pointed to from
their bean's body; a record of `details` — read on its sheet by its page's own words, and written by the view's one
write path into the store of the host that keeps it, never into git, to the bar of every held value (only a grant that
names its part, the gardener aside).

A garden of the core is grown here (test/grow.py) taking the view profile: Sam keeps it on a machine whose store keeps
what is held, and gives guitar lessons. A pupil is kept off git by name (bin/held.py person: an opaque id, their name
and phone in the store); a first course of lessons keeps an intake record of its pupil off git (a record of `details`:
their level, their instrument, the kit lent them); a second has none yet; a page names the record's fields in Persian
(`intake.level`, …). A reader may read and write the lessons and the people whole; another is granted, by name, the part
each is held in (`details`, the body). Then:

  the sheet     Sam's: the first lessons' level and instrument read from their record, under the page's words; the
                record offered in Edit with its fields; the second lessons offered a record to make; the pupil's contact
                offered too. The reader of the whole beans: none of it. The reader granted the parts by name: all of it
  the write     Sam changes the level: a new record in the store, the lessons' pointer swapped for it, the old record
                gone, the commit holding no level; the phone likewise, through the body; a record made on the second
                lessons, a label of its `details`; a contact made for a person who had none, a line of the body. The
                reader of the whole beans is refused; the reader granted the part by name writes it
  the check     `view check` takes a page that names a path into a record held off git, of `details` or the body
  a browser     Sam's sheet in Persian, in Edit: the record's fields by the page's words, the contact's too where the
                page names them (`contact.phone`), else the release's; the phone left to right; a field changed and Save
                sends that field alone, as a held op

Run: python3 test/view_held_records.py   (0 = green; a NOTE, and no browser check, where no Chromium is on the machine)
"""
import html, json, os, re, shutil, socket, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'test'))
import grow  # noqa: E402

PY = sys.executable
FAILS, TRACES = [], []
A, B, BARE = 'p-0a0a0a0a', 'p-0b0b0b0b', 'p-0d0d0d0d'
NAME, PHONE, NEWPHONE = 'Ayla Kaya', '+15555550123', '+15555550124'


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


def last_json(out):
    try:
        return json.loads(out.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return {'error': out[-1500:]}


T = tempfile.mkdtemp(prefix='view-held-records-')
REL, G, STORE = os.path.join(T, 'release'), os.path.join(T, 'garden-sam'), os.path.join(T, 'vault')
HOST = socket.gethostname().lower()
STORY = ('purpose: "{p}", outcome: "{p}", stages: [{{label: Read, doer: the view}}, {{label: Draw, doer: the view}}, '
         '{{label: Open, doer: the reader}}], questions: [{{lens: orient, ask: "{p}"}}], blind: [{{what: "what nobody wrote down"}}]')
# the page a host gives each reader, asked of the law's own grants (as view_serve.Host.may asks it)
SCOPED = """import importlib, json, os, sys, types
sys.path[:0] = [os.path.join('.', 'assets', 'view', 'lib'), 'bin']
import view_model as vm, view_engraved as ve, view_serve as vs
vm.init('.', 'page')
dmpass = importlib.import_module('pass')
USERS = ('sam', %r, %r)
def may(user, bean, positions=None, write=False, held=False):
    kw = {'held': True} if held else {}
    a = dmpass.may(user, 'write' if write else 'read', bean, positions=positions, root='.', gardener='sam', **kw)
    return vs.Verdict(a.granted, a.why, a.grants, a.reason_asked)
host = types.SimpleNamespace(cfg={'users': {u: {'bean': u, 'lang': 'fa'} for u in USERS}}, head='h', gardener='sam', may=may)
print(json.dumps({u: ve.scoped(host, u) for u in USERS}, default=str, ensure_ascii=False))""" % (A, B)
# a write by the view's one write path, as `who`, of one held op on `bean`
WRITE = """import json, os, sys; sys.path[:0] = [os.path.join('.', 'assets', 'view', 'lib'), 'bin']
import view_write
who, bean, op = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])
r = view_write.write('.', who, bean, [op])
print(json.dumps({k: r.get(k) for k in ('ok', 'refusals')}))"""
RECORD = """import json, sys; sys.path.insert(0, 'bin'); import held
print(json.dumps([dict(r, record=r['record']) for r in held.records(sys.argv[1], root='.')], default=str))"""


def added(rel):
    """The lines the last commit added to a file, stripped: what git was given of a write."""
    return [ln[1:].strip() for ln in run('git', 'show', 'HEAD', '--format=', '--', rel)[1].splitlines()
            if ln.startswith('+') and not ln.startswith('+++')]


def records(bean):
    return last_json(run(PY, '-c', RECORD, f'beans/{bean}.md')[1])


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
    # the first lessons's intake record, a record of `details` held off git, as a handplace of its own wrote one
    rc, out = run(PY, '-c', """import sys; sys.path.insert(0, 'bin'); import held
print(held.write_record({'bean': 'lessons-1', 'term': 'details', 'key': 'intake', 'about': [%r],
                         'entry': {'level': 'beginner', 'instrument': 'oud', 'kit': {'strings': 'new'}}}, root='.'))""" % PID)
    PTR = out.strip().splitlines()[-1] if rc == 0 else 'root:vault/none'
    for bid, extra in (('lessons-1', f'details:\n  h-{PTR[-32:-24]}: {{ held: "{PTR}" }}\n'), ('lessons-2', '')):
        put(f'beans/{bid}.md', f'''---
bean: {bid}
kind: contract
title: "{bid}"
summary: "guitar lessons Sam gives a pupil"
statements:
  - say:     {{ by: sam, at: now }}
  - own:     {{ by: sam, of: self }}
  - agree:   {{ id: agreed, by: [sam, {PID}], of: self, through: spoken, at: "2026-09-01" }}
  - concern: {{ of: [{PID}] }}
{extra}---
Lessons.
''')
    for rid in (A, B, BARE):
        put(f'beans/{rid}.md', f'''---
bean: {rid}
kind: person
title: "{rid}"
summary: "a person of the garden's pages"
statements:
  - say: {{ by: sam, at: now }}
  - own: {{ by: theone, of: self }}
---
A person.
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
  - draw: {{ id: one, by: self, of: [lessons-1], drawing: {{ label: One, archetype: sheet, {STORY.format(p='the first lessons')} }} }}
  - draw: {{ id: two, by: self, of: [lessons-2], drawing: {{ label: Two, archetype: sheet, {STORY.format(p='the second lessons')} }} }}
  - draw: {{ id: pupil, by: self, of: [{PID}], drawing: {{ label: Pupil, archetype: sheet, {STORY.format(p='the pupil')} }} }}
  - draw: {{ id: bare, by: self, of: [{BARE}], drawing: {{ label: Bare, archetype: sheet, {STORY.format(p='a person')} }} }}
  - draw: {{ id: page, by: self, of: [one, two, pupil, bare], page: {{ fields: [ {{ kind: contract, fact: title, shown_from: understand }}, {{ kind: contract, fact: intake, shown_from: understand, label: "پذیرش" }}, {{ kind: contract, fact: intake.level, shown_from: understand, label: "سطح" }}, {{ kind: contract, fact: intake.instrument, shown_from: understand, label: "ساز" }}, {{ kind: contract, fact: intake.kit.strings, shown_from: understand, label: "سیم‌ها" }}, {{ kind: contract, fact: intake.kit.case, shown_from: understand, label: "جعبه" }}, {{ kind: person, fact: title, shown_from: understand }}, {{ kind: person, fact: contact.phone, shown_from: understand, label: "شمارهٔ همراه" }} ] }} }}
---
A page.
''')
    rc, out = run(PY, 'bin/save.py', 'sam', 'a pupil, two courses of lessons, readers and a page', '--body',
                  f'- action: wrote [[{PID}]], [[lessons-1]], [[lessons-2]], [[{A}]], [[{B}]], [[{BARE}]] and [[page]]',
                  '- held: lessons-1 details.h-' + PTR[-32:-24] + ' added')
    check("the pupil, the lessons and the page are saved; git holds neither the name, the phone nor the record",
          rc == 0 and NAME not in get(f'beans/{PID}.md') and 'oud' not in get('beans/lessons-1.md'), out[-1500:])
    put('beans/sam.md', get('beans/sam.md').replace('\n---\n', (
        '\n  - grant: { id: a-reads, by: self, to: [%s], of: [lessons-1, lessons-2, %s, %s, page], as: read }\n'
        '  - grant: { id: a-writes, by: self, to: [%s], of: [lessons-1, lessons-2, %s, %s], as: write }\n'
        '  - grant: { id: b-reads, by: self, to: [%s], of: [lessons-1, lessons-2, %s, %s, page], as: read }\n'
        '  - grant: { id: b-held, by: self, to: [%s], of: [lessons-1, lessons-2], as: read, cover: { parts: [details] } }\n'
        '  - grant: { id: b-held-w, by: self, to: [%s], of: [lessons-1, lessons-2], as: write, cover: { parts: [details] } }\n'
        '  - grant: { id: b-body, by: self, to: [%s], of: [%s], as: read, cover: { parts: [body] } }\n'
        '  - say: { by: sam, of: [a-reads, a-writes, b-reads, b-held, b-held-w, b-body], at: now }\n---\n')
        % (A, PID, BARE, A, PID, BARE, B, PID, BARE, B, B, B, PID), 1))
    rc, out = run(PY, 'bin/save.py', 'sam', 'two readers granted', '--body',
                  f'- action: [[sam]] grants [[{A}]] the lessons and the people whole, [[{B}]] the part each is held in')
    check("the grants are saved", rc == 0 and '0 error(s)' in out, out[-1500:])

    rc, out = run(PY, 'assets/view/bin/view.py', 'check', '--page', 'page')
    check("view check: a page may name a path into a record held off git (`intake.level`, `contact.phone`), read where "
          "it is kept, and the record itself (`intake`), by the words its fields are gathered under",
          rc == 0, out[-800:])

    P = last_json(run(PY, '-c', SCOPED)[1])
    sam, a, b = (P.get(u) or {} for u in ('sam', A, B))
    s1, s2 = ((sam.get('sheets') or {}).get(x) or {} for x in ('lessons-1', 'lessons-2'))
    r1 = {r['key']: r for r in s1.get('records') or []}
    r2 = {r['key']: r for r in s2.get('records') or []}
    check("Sam's sheet of the first lessons: the level and the instrument read from its record held off git, under the page's "
          "words", (s1.get('details') or {}).get('intake.level') == 'beginner'
          and (s1.get('details') or {}).get('intake.instrument') == 'oud'
          and (s1.get('labels') or {}).get('intake.level') == 'سطح' and (s1.get('labels') or {}).get('intake') == 'پذیرش'
          and 'intake' not in (s1.get('details') or {}), (s1.get('details'), P.get('error')))
    check("...the record offered in Edit with its fields; the second lessons offered a record to make, by the page's fields",
          set((r1.get('intake') or {}).get('fields') or []) >= {'level', 'instrument', 'kit'}
          and (r2.get('intake') or {}).get('new') is True
          and set((r2.get('intake') or {}).get('fields') or []) == {'level', 'instrument', 'kit'}, (r1, r2))
    check("...a map in a record offered by every field of it the page names (`intake.kit.case`), the record's own fields "
          "of it too — whether the map holds it yet or not, or the record is not made yet",
          set(((r1.get('intake') or {}).get('maps') or {}).get('kit') or []) == {'strings', 'case'}
          and set(((r2.get('intake') or {}).get('maps') or {}).get('kit') or []) == {'strings', 'case'}, (r1, r2))
    pc = {r['key']: r for r in ((sam.get('sheets') or {}).get(PID) or {}).get('records') or []}
    nb = {r['key']: r for r in ((sam.get('sheets') or {}).get(BARE) or {}).get('records') or []}
    check("...the pupil's contact offered in Edit; a contact offered to make for a person who has none",
          ((pc.get('contact') or {}).get('entry') or {}).get('phone') == PHONE and (nb.get('contact') or {}).get('new') is True,
          (pc, nb))
    ja = json.dumps(a, ensure_ascii=False)
    check("the reader granted the beans whole: none of what is held — no level, no instrument, no phone, nothing to edit",
          'beginner' not in json.dumps(((a.get('sheets') or {}).get('lessons-1') or {}).get('details'))
          and 'oud' not in ja and PHONE not in ja and not any((x or {}).get('records') for x in (a.get('sheets') or {}).values()),
          ja[-600:])
    bp = ((b.get('sheets') or {}).get('lessons-1') or {})
    check("the reader granted the parts by name: the record read and offered", (bp.get('details') or {}).get(
        'intake.level') == 'beginner' and any(r['key'] == 'intake' for r in bp.get('records') or []), bp)

    before_ptr = next((r['pointer'] for r in records('lessons-1') if (r['record'] or {}).get('key') == 'intake'), None)
    W = last_json(run(PY, '-c', WRITE, A, 'lessons-1', json.dumps({'op': 'held', 'key': 'intake', 'entry': {'level': 'improver'}}))[1])
    check("the write: the reader of the beans whole is refused the record", W.get('ok') is False
          and 'held' in json.dumps(W), W)
    W = last_json(run(PY, '-c', WRITE, 'sam', 'lessons-1', json.dumps({'op': 'held', 'key': 'intake', 'entry': {'level': 'improver'}}))[1])
    now = [r for r in records('lessons-1') if (r['record'] or {}).get('key') == 'intake']
    check("Sam changes the level: a new record in the store, the lessons' pointer swapped for it, the old record gone, the "
          "rest of the record kept, the commit holding no level", W.get('ok') is True and len(now) == 1
          and now[0]['record']['entry'] == {'level': 'improver', 'instrument': 'oud', 'kit': {'strings': 'new'}}
          and now[0]['pointer'] != before_ptr and before_ptr not in get('beans/lessons-1.md')
          and added('beans/lessons-1.md') == [f'h-{PTR[-32:-24]}: {{ held: "{now[0]["pointer"]}" }}']
          and 'details.h-' in run('git', 'show', 'HEAD', '--', 'log/journal.md')[1], (W, now))
    W = last_json(run(PY, '-c', WRITE, B, 'lessons-1', json.dumps({'op': 'held', 'key': 'intake',
                                                               'entry': {'kit': {'strings': '', 'case': 'lent'}}}))[1])
    now = [r for r in records('lessons-1') if (r['record'] or {}).get('key') == 'intake']
    check("...the reader granted `details` by name writes it: a field of a map given empty is taken out",
          W.get('ok') is True and now and now[0]['record']['entry'].get('kit') == {'case': 'lent'}, (W, now))
    W = last_json(run(PY, '-c', WRITE, 'sam', PID, json.dumps({'op': 'held', 'key': 'contact', 'entry': {'phone': NEWPHONE}}))[1])
    c = [r for r in records(PID) if r['part'] == 'body']
    check("Sam changes the pupil's phone: the body's pointer swapped, the name kept, no phone in git",
          W.get('ok') is True and c and c[0]['record']['entry'] == {'name': NAME, 'phone': NEWPHONE}
          and NEWPHONE not in get(f'beans/{PID}.md'), (W, c))
    W = last_json(run(PY, '-c', WRITE, 'sam', 'lessons-2', json.dumps({'op': 'held', 'key': 'intake', 'entry': {'level': 'advanced'}}))[1])
    r2 = [r for r in records('lessons-2') if (r['record'] or {}).get('key') == 'intake']
    check("Sam makes a record on the second lessons: a label of its `details`, the record in the store",
          W.get('ok') is True and r2 and r2[0]['part'].startswith('details.h-') and r2[0]['record']['entry'] == {'level': 'advanced'}
          and 'level' not in get('beans/lessons-2.md'), (W, r2))
    W = last_json(run(PY, '-c', WRITE, 'sam', BARE, json.dumps({'op': 'held', 'key': 'contact', 'entry': {'name': 'Deniz'}}))[1])
    c = [r for r in records(BARE) if r['part'] == 'body']
    check("...and a contact for a person who had none: a line of the body, held off git", W.get('ok') is True and c
          and c[0]['record']['entry'] == {'name': 'Deniz'} and 'Deniz' not in get(f'beans/{BARE}.md'), (W, c))

    browser = next((x for x in ('chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable') if shutil.which(x)), None)
    if not browser:
        print("NOTE  the sheet was not drawn in a browser: none on this machine")
    else:
        P = last_json(run(PY, '-c', SCOPED)[1])
        sam = P.get('sam') or {}
        sys.path.insert(0, os.path.join(ROOT, 'assets', 'view', 'lib'))
        import view_widgets
        LIB = os.path.join(ROOT, 'assets', 'view', 'lib')
        js = view_widgets.bundle() + ''.join(open(os.path.join(LIB, f), encoding='utf-8').read() for f in (
            os.path.join('widgets', 'direction.js'), 'view_engraved.js', 'view_sheet.js'))
        page = """<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><style>%(css)s</style></head>
<body><div id="s" class="vw light" dir="rtl"></div><div id="p" class="vw light" dir="rtl"></div><script>%(js)s</script><script>
const out = {errs: []}, E = %(payload)s;
window.addEventListener('error', e => out.errs.push(String(e.message)));
try {
  const tools = b => window.daftarEngraved.tools({engraved: E, write: x => { out[b] = x; return new Promise(() => {}); }});
  const el = document.getElementById('s'), pl = document.getElementById('p');
  window.daftarArchetypes.sheet(el, E.sheets['lessons-1'], tools('lessons'), null);
  el.querySelector('[data-do="edit"]').click();
  const box = el.querySelector('[data-held-key="intake"]');
  out.labels = box ? [...box.querySelectorAll('.eg-role-name')].map(x => x.textContent) : null;
  out.heading = box && box.querySelector('h4') ? box.querySelector('h4').textContent : null;
  const age = el.querySelector('[name="held.intake.level"]');
  if (age) age.value = 'grade-3';
  el.querySelector('[data-do="save"]').click();
  out.kit1 = box ? [...box.querySelectorAll('[name^="held.intake.kit."]')].map(x => x.getAttribute('name')).sort() : null;
  const two = document.createElement('div'); two.className = 'vw light'; document.body.appendChild(two);
  window.daftarArchetypes.sheet(two, E.sheets['lessons-2'], tools('two'), null);
  two.querySelector('[data-do="edit"]').click();
  const box2 = two.querySelector('[data-held-key="intake"]');
  out.kit2 = box2 ? [...box2.querySelectorAll('[name^="held.intake.kit."]')].map(x => x.getAttribute('name')).sort() : null;
  out.labels2 = box2 ? [...box2.querySelectorAll('.eg-role-name')].map(x => x.textContent) : null;
  const kc = two.querySelector('[name="held.intake.kit.case"]');
  if (kc) kc.value = 'lent';
  two.querySelector('[data-do="save"]').click();
  window.daftarArchetypes.sheet(pl, E.sheets['%(pid)s'], tools('person'), null);
  pl.querySelector('[data-do="edit"]').click();
  const cbox = pl.querySelector('[data-held-key="contact"]');
  out.contact = cbox ? [...cbox.querySelectorAll('.eg-role-name')].map(x => x.textContent) : null;
  const ph = pl.querySelector('[name="held.contact.phone"]');
  out.phoneDir = ph ? getComputedStyle(ph).direction : null;
} catch (e) { out.errs.push('driver: ' + e.message + ' ' + (e.stack || '').split('\\n')[1]); }
const pre = document.createElement('pre'); pre.id = '__out'; pre.textContent = JSON.stringify(out); document.body.appendChild(pre);
</script></body></html>"""
        path = os.path.join(T, 'records.html')
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(page % {'css': view_widgets.css() + open(os.path.join(LIB, 'view_engraved.css'), encoding='utf-8').read(),
                             'js': js, 'payload': json.dumps(sam, ensure_ascii=False), 'pid': PID})
        r = subprocess.run([browser, '--headless=new', '--disable-gpu', '--no-sandbox', '--virtual-time-budget=5000',
                            '--dump-dom', 'file://' + path], capture_output=True, text=True, encoding='utf-8', errors='replace',
                           timeout=180)
        m = re.search(r'<pre id="__out">(.*?)</pre>', r.stdout, re.S)
        Bx = json.loads(html.unescape(m.group(1))) if m else {'errs': ['no result: ' + r.stderr[-600:]]}
        check("in Persian, in Edit: the record's fields by the page's words; a field changed and Save sends it alone, as "
              "a held op, under the page's words for the record", not Bx['errs'] and 'سطح' in (Bx.get('labels') or [])
              and 'ساز' in (Bx.get('labels') or []) and Bx.get('heading') == 'پذیرش'
              and (Bx.get('lessons') or {}).get('ops') == [{'op': 'held', 'key': 'intake', 'entry': {'level': 'grade-3'}}], Bx)
        check("...a map the page names fields of, drawn by them, held or not yet (the map of a record that has none of "
              "it, too); one changed is sent in its map, as a held op",
              Bx.get('kit1') == ['held.intake.kit.case', 'held.intake.kit.strings']
              and Bx.get('kit2') == ['held.intake.kit.case', 'held.intake.kit.strings']
              and 'سیم‌ها' in (Bx.get('labels2') or []) and 'جعبه' in (Bx.get('labels2') or [])
              and (Bx.get('two') or {}).get('ops') == [{'op': 'held', 'key': 'intake', 'entry': {'kit': {'case': 'lent'}}}], Bx)
        check("...the contact's fields by the page's words where it names them (`contact.phone`), else the release's; the "
              "phone left to right", 'شمارهٔ همراه' in (Bx.get('contact') or []) and 'نام' in (Bx.get('contact') or [])
              and 'تلفن' not in (Bx.get('contact') or []) and Bx.get('phoneDir') == 'ltr', Bx)
finally:
    if TRACES:
        print("TRACEBACKS:\n" + "\n---\n".join(TRACES[:3]))
    shutil.rmtree(T, ignore_errors=True)

print(f"\nview_held_records: {len(FAILS)} failed" + (": " + ", ".join(FAILS) if FAILS else ""))
sys.exit(1 if FAILS or TRACES else 0)
