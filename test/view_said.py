#!/usr/bin/env python3
"""The readings a handplace draws, said in its reader's language and calendar: a lead by what it is and what it is
about — never the English sentence bin/leads.py writes for a log — a case's step by its walk's own words, a clause by
its words and its day in the reader's calendar, whatever calendar the clause counts in; and the timeline's happenings at
their own time: an attendance at its moment, and each session of a series at that moment's hour.

A garden of the core is grown here (test/grow.py) taking the view profile: Sam keeps it; a bicycle repair waits on its
walk at a step; a class meets on two days of each ISO week, its first session an attendance at a moment and its
repetition a clause over that attendance; a page of a queue and a timeline. Then:

  the queue     each lead carries what its sentence says: a case its walk's words for its step, a clause its words (not
                the id of the statement it repeats) and its day as a Gregorian day, though the clause counts in ISO weeks;
                drawn in Persian, the case's line reads «در گام «…» منتظر است» and the clause's day is in the Persian
                calendar, and drawn in English, "waits at “…”" — and no line shows bin/leads.py's English sentence
  the timeline  the class's first session is placed at its own moment; each later session at that moment's hour, and
                named by its series, never by the id of the attendance its clause repeats; and a lease whose meeting
                falls on the day its monthly rent is due draws both: a session of a series is left out only on the day
                of its own statement's session, never because its being has some other happening that day

Run: python3 test/view_said.py   (0 = green)
"""
import datetime, json, os, re, shutil, subprocess, sys, tempfile

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


T = tempfile.mkdtemp(prefix='view-said-')
REL, G = os.path.join(T, 'release'), os.path.join(T, 'garden-sam')
TODAY = datetime.date.today()
# the class: its first session three days ago at 08:30, then each Tuesday and Sunday of an ISO week
FIRST = TODAY - datetime.timedelta(days=3)
# the lease: its rent due each month from a day soon (one every month has), and a meeting on that same day
RENT = next(TODAY + datetime.timedelta(days=d) for d in range(2, 40) if (TODAY + datetime.timedelta(days=d)).day <= 28)
WEEK = f"{FIRST.isocalendar()[0]}-W{FIRST.isocalendar()[1]:02d}-{FIRST.isocalendar()[2]}"
STORY = ('purpose: "{p}", outcome: "{p}", stages: [{{label: Read, doer: the view}}, {{label: Draw, doer: the view}}, '
         '{{label: Open, doer: the reader}}], questions: [{{lens: orient, ask: "{p}"}}], blind: [{{what: "what nobody wrote down"}}]')

try:
    grow.release(REL)
    rc, out = run(PY, os.path.join(REL, 'seed', 'germinate.py'), G, '--gardener', 'sam', '--gardener-name', 'Sam',
                  '--profile', 'view', cwd=T)
    check("a garden of the core grows taking the view profile, kept by Sam", rc == 0, out[-800:])
    run(PY, 'bin/install.py')
    put('mappings/walk-repair.md', '''---
bean: walk-repair
kind: procedure
title: "walk-repair"
summary: "how a bicycle repair goes"
statements:
  - say:  { by: sam, at: now }
  - step: { id: handed-over, as: "the owner brings the bicycle", to: [looked-at] }
  - step: { id: looked-at, as: "what is wrong is found", to: [collected] }
  - step: { id: collected, as: "the owner takes it home", walk: { final: "true" } }
---
Steps.
''')
    put('beans/repair-1.md', '''---
bean: repair-1
kind: contract
title: "repair-1"
summary: "Sam mends a bicycle"
statements:
  - say:    { by: sam, at: now }
  - own:    { by: theone, of: self }
  - be:     { id: course, by: self, at: walk-repair, as: order }
  - move:   { by: sam, of: self, through: course, at: [now, "walk-repair#handed-over"] }
  - move:   { by: sam, of: self, through: course, at: [now, "walk-repair#looked-at"] }
---
A repair.
''')
    put('beans/class-yoga.md', f'''---
bean: class-yoga
kind: event
title: "class-yoga — yoga, twice a week"
summary: "a class Sam attends"
statements:
  - say:    {{ by: sam, at: now }}
  - own:    {{ by: sam, of: self }}
  - attend: {{ id: attends, by: sam, of: self, at: "{FIRST.isoformat()}T08:30+03:00/{FIRST.isoformat()}T10:00+03:00" }}
  - can:    {{ id: weekly, by: sam, of: attends, clause: {{ due: "{FIRST.isoformat()}", every: {{ of: time, in: iso-week, each: week, at: ["2", "7"], from: "{WEEK}" }} }} }}
---
A class.
''')
    put('beans/lease-1.md', f'''---
bean: lease-1
kind: event
title: "lease-1 — a room let by the month"
summary: "a lease whose meeting falls on a rent day"
statements:
  - say:    {{ by: sam, at: now }}
  - own:    {{ by: sam, of: self }}
  - be:     {{ id: meeting, by: self, at: "{RENT.isoformat()}T10:00+03:00/{RENT.isoformat()}T11:00+03:00" }}
  - can:    {{ id: rent, by: sam, of: "pay the month's rent", to: theone, clause: {{ due: "{RENT.isoformat()}", every: {{ of: time, in: gregorian-civil, each: month, at: "{RENT.day}" }}, amount: {{ count: "300", unit: XTS }} }} }}
---
A lease.
''')
    put('beans/page.md', f'''---
bean: page
kind: service
title: "Sam's handplace"
summary: "what waits, and when"
statements:
  - say:    {{ by: sam, at: now }}
  - own:    {{ by: sam, of: self }}
  - be:     {{ by: self, at: "uri:https://garden.example.org/", as: location }}
  - reckon: {{ id: dated, reading: {{ what: "what has a day", steps: [ {{ id: e, op: select, kind: event }} ] }} }}
  - draw:   {{ id: waits, by: self, of: [sam], drawing: {{ label: Now, archetype: queue, {STORY.format(p='what waits')} }} }}
  - draw:   {{ id: time, by: self, of: [sam], drawing: {{ label: Time, archetype: timeline, selection: dated, layouts: [list, week], {STORY.format(p='when')} }} }}
  - draw:   {{ id: page, by: self, of: [waits, time], page: {{ visibility: private }} }}
---
A page.
''')
    rc, out = run(PY, 'bin/save.py', 'sam', "RULE-CHANGE: a repair on its walk, a class, and a page", '--body', '- ratified_by: sam',
                  '- action: wrote [[walk-repair]], [[repair-1]], [[class-yoga]], [[lease-1]] and [[page]]; VOCAB.md holds the kind of a walk')
    check("the repair, the class and the page are saved through the core's gate", rc == 0 and '0 error(s)' in out, out[-1500:])

    code = ("import json, os, sys; sys.path[:0] = [os.path.join(%r, 'assets', 'view', 'lib'), os.path.join(%r, 'bin')]; "
            "import view_model as vm, view_engraved as ve; vm.init(%r); "
            "print(json.dumps(ve.page(lambda *a, **k: True, 'sam'), default=str))" % (G, G, G))
    rc, out = run(PY, '-c', code)
    try:
        P = json.loads(out.strip().splitlines()[-1])
    except (ValueError, IndexError):
        P = {'error': out[-1500:]}
    leads = ((P.get('drawings') or {}).get('waits') or {}).get('leads') or []
    case = next((x for x in leads if x.get('kind') == 'case'), {})
    due = next((x for x in leads if x.get('kind') == 'obligation' and x.get('about') == 'class-yoga'), {})
    check("a case's lead carries its step in its walk's own words", case.get('step_says') == 'what is wrong is found', (case, P.get('error')))
    check("a clause's lead carries its day as a Gregorian day, though it counts in ISO weeks, and no words where its "
          "words would be a statement's id", re.fullmatch(r'\d{4}-\d{2}-\d{2}', str(due.get('day') or '')) is not None
          and 'what' not in due, due)
    ev = ((P.get('drawings') or {}).get('time') or {}).get('events') or []
    first = [e for e in ev if e.get('kind') == 'happening' and e.get('bean') == 'class-yoga']
    later = [e for e in ev if e.get('kind') == 'due' and e.get('bean') == 'class-yoga']
    check("the class's first session is placed at its own moment, as a happening", [(e['day'], e['time']) for e in first]
          == [(FIRST.isoformat(), '08:30')], first)
    check("...each later session at that moment's hour, its words none (never the id `attends`), and none on the "
          "first session's own day twice", later and all(e.get('time') == '08:30' and not e.get('what') for e in later)
          and FIRST.isoformat() not in [e['day'] for e in later], later[:3])
    lease = [(e['kind'], e.get('clause') or e.get('statement')) for e in ev if e.get('bean') == 'lease-1' and e.get('day') == RENT.isoformat()]
    check("a lease's meeting and its monthly rent, due the same day, are both drawn on it", sorted(lease)
          == [('due', 'rent'), ('happening', 'meeting')], [e for e in ev if e.get('bean') == 'lease-1'][:4])

    browser = next((b for b in ('chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable') if shutil.which(b)), None)
    DRIVE = """<script>
window.__errs = []; window.addEventListener('error', e => window.__errs.push(String(e.message)));
window.addEventListener('load', () => { const out = {};
 try { document.querySelector('.tab[data-t="waits"]').click(); document.querySelector('#lens button[data-l="understand"]').click();
  out.queue = document.querySelector('#view').innerText;
  document.querySelector('.tab[data-t="time"]').click(); document.querySelector('[data-layout="list"]').click();
  out.time = document.querySelector('#view').innerText; } catch (e) { window.__errs.push('driver: ' + e.message); }
 const pre = document.createElement('pre'); pre.id = '__result'; pre.textContent = JSON.stringify({errs: window.__errs, out}); document.body.appendChild(pre); });
</script>"""
    import html as _html
    for lang in ('fa', 'en'):
        src = os.path.join(T, f'page-{lang}.html')
        rc, out = run(PY, 'assets/view/bin/view.py', 'report', '--out', src, '--lang', lang)
        if not browser or rc != 0:
            check(f"view report --lang {lang} is written", rc == 0, out[-600:])
            continue
        dr = os.path.join(T, f'drive-{lang}.html')
        with open(dr, 'w', encoding='utf-8') as fh:
            fh.write(open(src, encoding='utf-8').read().replace('<head>', '<head>' + DRIVE, 1))
        r = subprocess.run([browser, '--headless=new', '--disable-gpu', '--no-sandbox', '--virtual-time-budget=6000', '--dump-dom',
                            'file://' + dr], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=120)
        m = re.search(r'<pre id="__result">(.*?)</pre>', r.stdout, re.S)
        res = json.loads(_html.unescape(m.group(1))) if m else {'errs': ['no result'], 'out': {}}
        q, tl = (res.get('out') or {}).get('queue') or '', (res.get('out') or {}).get('time') or ''
        if lang == 'fa':
            check("in Persian the case's line reads «در گام «what is wrong is found» منتظر است», the clause's day in Persian "
                  "digits, and no line shows bin/leads.py's English", not res['errs'] and 'در گام «what is wrong is found» منتظر است' in q
                  and 'waits at' not in q and 'falls due on' not in q and re.search('[۰-۹]', q), res)
            check("...and the timeline's sessions at ۰۸:۳۰, the hour of the first", '۰۸:۳۰' in tl and 'attends' not in tl, res)
        else:
            check("in English the case's line reads \"waits at “what is wrong is found”\"", not res['errs']
                  and 'waits at “what is wrong is found”' in q and 'falls due on' not in q, res)
    if not browser:
        print("NOTE  the pages were not drawn in a browser: none on this machine")
finally:
    if TRACES:
        print("TRACEBACKS:\n" + "\n---\n".join(TRACES[:3]))
    shutil.rmtree(T, ignore_errors=True)

print(f"\nview_said: {len(FAILS)} failed" + (": " + ", ".join(FAILS) if FAILS else ""))
sys.exit(1 if FAILS or TRACES else 0)
