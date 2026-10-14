#!/usr/bin/env python3
"""The view finished for a handplace (design V1 → V2): the archetypes engraved from readings — a queue, a timeline,
flows, a sheet — their law, the readings they draw, the one write path a sheet's Save and a drawing's form take, held
values on the sheet, and the renderers in a browser.

A garden of the core is grown here (test/grow.py) taking the view profile, and an invented one is written in it: Sam,
its gardener; Ali, kept by name on her own word (she agreed to the camera's agreement); a reader kept under an opaque
id; the camera and the lens Sam and Ali bought, each paid by one and borne by both in shares, one of them uneven; a
loan repaid in six monthly instalments (a clause with a due day and a repetition) and a deposit due within days; a
dinner; Ali's phone, held off git on this machine's store; a decision parked; and a page of four drawings, none drawn by
a module. Then:

  part 1, the law   the law offers the four archetypes, each with the axes it runs on; the page passes the core's gate
                    with no drawing module; and the gate refuses by name an order on an axis its row does not run on,
                    a timeline with no reading, flows that do not say what their nodes are, a sheet or a new kind whose
                    page names no facts for it, an entry form of no verb of the law or of a role its verb lacks
  part 2, the readings  `view check` agrees with no module; the flows are `bin/ledger.py --json`'s net, the timeline's
                    repetition `bin/stale.py`'s occurrences, the queue `bin/leads.py --json`'s leads for the reader; a
                    sheet shows a payment's shares and the clause that asks it beneath it, and the law's default where no
                    share is written; the report carries a held value's place and never the value
  part 3, the one write path, through the served page   each viewer's readings their own; the held phone sent to the
                    gardener on the machine that keeps it, and nothing of Ali to a reader who may not read her; a Save of
                    a change, an add and a remove is one commit with one journal entry naming each, through bin/safe.py,
                    and the gate passes it; a refused Save keeps nothing, its message at its fact; the title edited by
                    the gardener, refused to a reader with no grant, written by one a `cover: {parts: [title]}` opens it
                    to, and nothing else of the being; a new being minted from an empty sheet; a drawing's form of a verb
                    with its presets; a held value changed in the Save, sealed, the commit keeping only the pointer;
                    no being named to a reader who may not read it (a default's payer, the machine that keeps a held
                    value, the gardener); and the served page in a browser UNDER ITS POLICY — the renderers allowed by
                    their hashes (view_report.SCRIPTS), a script injected refused, and a sheet's Save from the page
  part 4, the browser   the report in `en` and in `fa`, and the served page in `fa`: every drawing at every lens, the
                    timeline's three layouts and a sheet opened, in a left-to-right and a right-to-left page, with no
                    exception; and on the served page the sheet's one Edit

Run: python3 test/view_handplace.py   (0 = green; about two minutes)
"""
import datetime, json, os, re, shutil, socket, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'test'))
import grow  # noqa: E402

PY = sys.executable
FAILS, TRACES = [], []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-1500:]))
    if not cond:
        FAILS.append(name)


def run(*a, cwd=None, env=None, stdin=None):
    r = subprocess.run(list(a), capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=cwd or G,
                       env=env or grow.ENV, input=stdin)
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


def gate():
    """The core's findings on the working tree, one a line: `<rule>  <where>: <what>`."""
    rc, out = run(PY, 'core/check.py', '.')
    return rc, [ln for ln in out.splitlines() if ln and not ln.startswith('core check')]


def head():
    return run('git', 'rev-parse', 'HEAD')[1].strip()


def clean():
    return run('git', 'status', '--porcelain')[1].strip() == ''


T = tempfile.mkdtemp(prefix='view-handplace-')
REL, G, STORE = os.path.join(T, 'release'), os.path.join(T, 'garden-sam'), os.path.join(T, 'vault')
TODAY = datetime.date.today()
D = lambda n: (TODAY + datetime.timedelta(days=n)).isoformat()                      # noqa: E731
FIRST = (TODAY.replace(day=1) - datetime.timedelta(days=40)).replace(day=1).isoformat()  # the 1st, two months back
HOST = socket.gethostname().lower()
READER = 'p-0a1b2c3d'

BEANS = {
    'laptop': f'''bean: laptop
kind: host
title: "laptop — the machine the garden is kept on"
summary: "Sam's laptop: the garden, and the store its held values are kept in."
statements:
  - read: {{ by: sam, at: now }}
  - own:  {{ by: sam, of: self }}
  - name: {{ by: anchor-hostname, of: self, as: {HOST} }}
details:
  roots:
    vault: {{ system: unix-filesystem, at: "{HOST}:{STORE}", keeps: special-category, readable_from: this-host }}
''',
    'ali': '''bean: ali
kind: person
title: "Ali"
summary: "Ali, who shares costs with Sam."
statements:
  - say:    { by: sam, at: now }
  - own:    { by: theone, of: self }
  - answer: { by: self, of: self, as: law }
  - name:   { id: phone, by: e164, of: self, as: "+15555550100" }
''',
    READER: f'''bean: {READER}
kind: person
title: "{READER}"
summary: "a reader of the garden's pages"
statements:
  - say:    {{ by: sam, at: now }}
  - own:    {{ by: theone, of: self }}
''',
    'camera': '''bean: camera
kind: contract
title: "camera — Sam and Ali bought a camera and a lens together"
summary: "Ali paid for the camera, Sam for the lens; they bear the camera two to one and the lens one to two."
statements:
  - say:    { by: sam, at: now }
  - own:    { by: theone, of: self }
  - answer: { by: sam, of: self, as: law }
  - answer: { by: ali, of: self, as: law }
  - agree:  { id: agreed, by: [sam, ali], of: "a camera and a lens the two of them use", through: spoken }
  - pay:    { id: camera, by: ali, of: { count: "90.00", unit: XTS }, through: agreed, note: "the camera" }
  - bear:   { id: camera-sam, by: sam, of: camera, share: "2" }
  - bear:   { id: camera-ali, by: ali, of: camera, share: "1" }
  - pay:    { id: lens, by: sam, of: { count: "100.00", unit: XTS }, through: agreed, note: "the lens" }
  - bear:   { id: lens-ali, by: ali, of: lens, share: "2" }
  - bear:   { id: lens-sam, by: sam, of: lens, share: "1" }
''',
    'loan': f'''bean: loan
kind: contract
title: "loan — Sam lent Ali the price of a washer, repaid monthly"
summary: "Sam paid for Ali's washer; Ali repays it in six monthly instalments, and a deposit is due within days."
statements:
  - say:        {{ by: sam, at: now }}
  - own:        {{ by: theone, of: self }}
  - answer:     {{ by: sam, of: self, as: law }}
  - answer:     {{ by: ali, of: self, as: law }}
  - agree:      {{ id: lends, by: sam, of: "the price of Ali's washer", through: spoken, as: lender }}
  - agree:      {{ id: borrows, by: ali, of: "the price of Ali's washer", through: spoken, as: borrower }}
  - pay:        {{ id: the-loan, by: sam, of: {{ count: "120.00", unit: XTS }}, note: "Sam paid the shop" }}
  - bear:       {{ id: ali-bears, by: ali, of: the-loan, share: "1" }}
  - pay:        {{ id: instalment, by: ali, to: sam, of: {{ count: "20.00", unit: XTS }} }}
  - obligatory: {{ id: instalments, of: instalment, through: self, note: "Ali repays 20 XTS on the first day of each month, six times", clause: {{ due: "{FIRST}", every: {{ of: time, in: gregorian-civil, each: month, at: "1", times: "6" }} }} }}
  - pay:        {{ id: deposit, by: ali, to: sam, of: {{ count: "5.00", unit: XTS }} }}
  - obligatory: {{ id: deposit-due, of: deposit, through: self, note: "a deposit, once", clause: {{ due: "{D(3)}" }} }}
''',
    'dinner': f'''bean: dinner
kind: event
title: "dinner — Sam's dinner with friends"
summary: "A dinner Sam gives at home."
statements:
  - say:    {{ by: sam, at: now }}
  - be:     {{ id: when, by: self, at: "{D(5)} 19:00+03:00" }}
  - own:    {{ by: theone, of: self }}
  - answer: {{ by: sam, of: self, as: law }}
  - attend: {{ id: sam-comes, by: sam, of: self }}
''',
}

STORY = ('label: "{l}", purpose: "{p}", outcome: "{o}", stages: [{{label: Read the garden, doer: the view}}, {{label: Draw what it says, '
         'doer: the reader}}, {{label: Open a being, doer: the reader}}], questions: [{{lens: orient, ask: "{q}"}}], '
         'blind: [{{what: "{b}"}}]')


def drawing(did, of, archetype, extra='', **story):
    s = STORY.format(**story)
    return f"  - draw: {{ id: {did}, by: self, of: [{of}], drawing: {{ {s}, archetype: {archetype}{', ' + extra if extra else ''} }} }}\n"


PAGE_HEAD = '''bean: handplace
kind: service
title: "handplace — Sam's pages"
summary: "What waits, when, who owes whom, and the sheet of each being."
statements:
  - say:    { by: sam, at: now }
  - own:    { by: sam, of: self }
  - be:     { id: at-1, by: self, at: "uri:https://garden.example.org/", as: location, placed: { openness: here } }
  - reckon: { id: dated, reading: { what: "what has a day: the agreements and the happenings", steps: [ { id: c, op: select, kind: contract }, { id: e, op: select, kind: event }, { id: all, op: union, of: c, with: e } ] } }
  - reckon: { id: agreements, reading: { what: "the agreements", steps: [ { id: c, op: select, kind: contract } ] } }
'''
DRAWINGS = (drawing('waits', 'handplace', 'queue', l="Now", p="What waits for the reader", o="Nothing waits unseen",
                    q="What needs me now?", b="what nobody has written down")
            + drawing('time', 'handplace', 'timeline', 'selection: dated, layouts: [week, month, list], axes: { inline: time }',
                      l="Time", p="When each thing falls", o="No day passes unseen", q="When?", b="what has no day")
            + drawing('money', 'handplace', 'flows', 'nodes: parties, selection: agreements',
                      l="Money", p="Who owes whom", o="Every debt is read, never kept", q="Who owes whom?", b="money not recorded")
            + drawing('ali', 'ali', 'sheet', 'new: [person], writes: [{ verb: pay, preset: { to: sam } }]',
                      l="Ali", p="Ali as she stands", o="One place to change her", q="Who is Ali?", b="what she has not said"))
FIELDS = ('[{kind: person, fact: title, shown_from: understand}, {kind: person, fact: summary, shown_from: understand}, '
          '{kind: person, fact: name, shown_from: inspect}, {kind: contract, fact: title, shown_from: understand}, '
          '{kind: contract, fact: agree, shown_from: understand}, {kind: contract, fact: pay, shown_from: understand}, '
          '{kind: contract, fact: obligatory, shown_from: understand}, {kind: event, fact: be, shown_from: understand}]')
PAGE_DRAW = f"  - draw:   {{ id: page, by: self, of: [waits, time, money, ali], page: {{ visibility: private, fields: {FIELDS} }} }}\n"
PAGE = PAGE_HEAD + DRAWINGS + PAGE_DRAW

try:
    grow.release(REL)
    rc, out = run(PY, os.path.join(REL, 'seed', 'germinate.py'), G, '--gardener', 'sam', '--gardener-name', 'Sam',
                  '--profile', 'view', cwd=T)
    check("a garden of the core grows taking the view profile, kept by Sam", rc == 0 and os.path.isfile(
        os.path.join(G, 'assets', 'view', 'bin', 'view.py')), out[-800:])
    run(PY, 'bin/install.py')
    put('VOCAB.md', get('VOCAB.md').replace(
        "namespaces: []\n",
        "namespaces:\n  - { namespace: anchor-hostname, once: \"false\", meaning: \"a machine's own name for itself\" }\n", 1))
    for bid, text in BEANS.items():
        put(f'beans/{bid}.md', '---\n' + text + '---\n' + bid + ', as Sam records it.\n')
    put('log/pending.md', get('log/pending.md').rstrip('\n') + f'''

## camera-insurance · whether the camera is insured, and who pays for it · proposed {D(0)} by sam
- class: D
- neighborhood: camera
- proposal: Sam insures it; the two bear it as they bear the camera
- status: proposed
''')
    rc, out = run(PY, 'bin/save.py', 'sam', "the camera, the loan, Ali, a reader and a dinner",
                  '--body', '- action: recorded [[laptop]], [[ali]], [[p-0a1b2c3d]], [[camera]], [[loan]] and [[dinner]]. '
                  'RULE-CHANGE: VOCAB.md names the namespace a machine names itself in.')
    check("the invented garden is saved through the core's gate", rc == 0 and '0 error(s)' in out, out[-1500:])
    rc, out = run(PY, 'bin/held.py', 'put', 'ali', 'phone', '--basis', 'camera#agreed')
    rc2, out2 = run(PY, 'bin/save.py', 'sam', "Ali's phone, held off git", '--body', "- action: sealed [[ali]]'s phone",
                    '- held: ali phone added')
    check("Ali's phone is held off git on this machine's store, held while her word on the camera stands, and saved",
          rc == 0 and rc2 == 0 and '+15555550100' not in get('beans/ali.md') and 'while: "camera#agreed"' in get('beans/ali.md'),
          out + out2[-800:])

    # ------------------------------------------------------------------ part 1: the law
    sys.path.insert(0, ROOT)
    from core.law import Law
    L = Law.load()
    arch = {r['archetype']: r for r in L.profile_tables.get('archetypes') or []}
    check("law: the four archetypes engraved from readings, each with the order it runs on — a queue down the page, a "
          "timeline's time and flows' flow along the reader's line — the timeline laid along time, the flows read from "
          "pay, bear and pass; each declared whole, vacant until a garden draws it",
          {'queue', 'timeline', 'flows', 'sheet'} <= set(arch) and arch['queue'].get('axes') == {'block': 'ordinal'}
          and arch['timeline'].get('axes') == {'inline': 'time'} and arch['timeline'].get('frame') == ['time']
          and arch['flows'].get('axes') == {'inline': 'flow'} and arch['flows'].get('reads') == ['pay', 'bear', 'pass']
          and arch['table'].get('axes') == {'inline': 'taxis', 'block': 'ordinal'} and not L.problems()
          and {'queue', 'timeline', 'flows', 'sheet'} <= {str(v.get('position')) for v in L.vacancies
                                                         if v.get('at') == 'table:archetypes' and v.get('reason') == 'universal'},
          (sorted(arch), L.problems()[:3]))
    dattrs = (L.forms.get('drawing') or {}).get('attrs') or {}
    check("law: a drawing says where each order runs (`axes`), a timeline's span and layouts, what flows' nodes are, the "
          "kinds a page may make (`new`), and an entry form of a verb of the law (`writes.verb`, `preset`)",
          all(a in dattrs for a in ('axes', 'span', 'layouts', 'nodes', 'new'))
          and {'verb', 'preset', 'term'} <= set(((dattrs['writes'].get('in') or {}).get('entries') or {}))
          and not (L.forms.get('page') or {}).get('attrs', {}).get('drawings', {}).get('required'), sorted(dattrs))
    rc, out = run(PY, 'core/check.py', '--law')
    check("law: python3 core/check.py --law proves it one", rc == 0 and '— 0 error(s)' in out, out[-600:])

    put('beans/handplace.md', '---\n' + PAGE + '---\nSam\'s pages.\n')
    rc, out = run(PY, 'bin/save.py', 'sam', "Sam's pages: what waits, when, who owes whom, and Ali's sheet",
                  '--body', '- action: wrote [[handplace]]: a queue, a timeline, flows and a sheet, none drawn by a module.')
    check("the page — a queue, a timeline, flows and a sheet, and no drawing module — passes the core's gate",
          rc == 0 and '0 error(s)' in out, out[-1500:])

    REFUSED = [
        ("an order on an axis its row does not run on: a magnitude along the reader's line",
         "axes: { inline: time }", "axes: { inline: magnitude }", ("profile", "magnitude", "vertical axis", "never inline")),
        ("...and time down the page", "axes: { inline: time }", "axes: { block: time }",
         ("profile", "`time` runs on the inline axis", "never block")),
        ("an axis a drawing does not have", "axes: { inline: time }", "axes: { depth: time }", ("depth", "no attribute")),
        ("a timeline with no reading", "archetype: timeline, selection: dated, ", "archetype: timeline, ",
         ("archetype: timeline requires `selection`",)),
        ("a layout no timeline has", "layouts: [week, month, list]", "layouts: [week, year]", ("'year'", "not one of")),
        ("flows that do not say what their nodes are", "nodes: parties, ", "", ("archetype: flows requires `nodes`",)),
        ("a sheet whose page names no facts for its kind", "{kind: person, fact: title, shown_from: understand}, "
         "{kind: person, fact: summary, shown_from: understand}, {kind: person, fact: name, shown_from: inspect}, ", "",
         ("a sheet of ali", "names none")),
        ("a new kind whose page names no facts for it", "new: [person]", "new: [person, host]", ("a new host", "names none")),
        ("an entry form of no verb of the law", "writes: [{ verb: pay,", "writes: [{ verb: paid,", ("'paid' is no verb",)),
        ("...or of a role its verb does not take", "preset: { to: sam }", "preset: { towards: sam }",
         ("`pay` takes no `towards`",)),
        ("...or of a verb and a term at once", "writes: [{ verb: pay,", "writes: [{ term: payments, verb: pay,",
         ("a verb of the law, or a term", "one of the two")),
    ]
    for name, old, new, words in REFUSED:
        if old not in PAGE:
            check(f"REFUSED: {name}", False, f"the probe cannot be written: {old!r} is not in the page")
            continue
        put('beans/handplace.md', '---\n' + PAGE.replace(old, new, 1) + '---\nSam\'s pages.\n')
        rc, found = gate()
        hit = [ln for ln in found if 'handplace' in ln and all(w in ln for w in words)]
        check(f"REFUSED by name: {name}", rc == 1 and bool(hit), found[:6])
    run('git', 'checkout', '--', 'beans/handplace.md')
    check("...and the page as it was passes again", gate()[0] == 0, gate()[1][:4])

    # ------------------------------------------------------------------ part 2: the readings, as the tools read them
    rc, out = run(PY, 'assets/view/bin/view.py', 'check')
    check("view check: the page of four engraved drawings agrees, with no drawing module", rc == 0 and 'agree' in out, out[-800:])
    code = ("import json, os, sys; sys.path.insert(0, os.path.join(%r, 'assets', 'view', 'lib')); import view_model as vm, "
            "view_report; p = vm.init(%r); assert not p, p; print(json.dumps(view_report.payload(), default=str))" % (G, G))
    rc, out = run(PY, '-c', code)
    try:
        P = json.loads(out.strip().splitlines()[-1])
    except (ValueError, IndexError):
        P = {'error': out[-1500:]}
    E = P.get('engraved') or {}
    check("the report's page carries each engraved drawing — no svg, no module — with its archetype and the axes it runs on",
          all(((P.get('views') or {}).get(k) or {}).get('engraved', {}).get('archetype') == a
              for k, a in (('waits', 'queue'), ('time', 'timeline'), ('money', 'flows'), ('ali', 'sheet')))
          and P['views']['time']['engraved']['axes'] == {'inline': 'time'}
          and P['views']['money']['engraved']['axes'] == {'inline': 'flow'}, str(P)[-1200:])
    rc, out = run(PY, 'bin/ledger.py', 'camera', 'loan', '--json')
    net = [(x['from'], x['to'], x['count'], x['unit']) for x in json.loads(out)['net']] if rc == 0 else out
    arrows = [(x['from'], x['to'], x['count'], x['unit']) for x in E['drawings']['money']['arrows']]
    check("flows: the arrows are bin/ledger.py --json's net over the agreements the reading holds, exactly — Ali owes Sam "
          "380/3 XTS, the camera's 60 against the lens's 200/3 and the loan's 120", arrows == net == [('ali', 'sam', '380/3', 'XTS')],
          (arrows, net))
    code = ("import datetime, json, sys; sys.path.insert(0, 'bin'); import stale; t = datetime.date.today().toordinal(); "
            "f = stale.day_of(%r); r = {'of': 'time', 'in': 'gregorian-civil', 'each': 'month', 'at': '1', 'times': '6'}; "
            "print(json.dumps([datetime.date.fromordinal(n).isoformat() for n in stale.occurrences(f, r) if t - 42 <= n <= t + 42]))"
            % FIRST)
    rc, out = run(PY, '-c', code)
    occ = json.loads(out) if rc == 0 else out
    tl = E['drawings']['time']
    got = [x['day'] for x in tl['events'] if x.get('clause') == 'instalments']
    check("timeline: the instalments are bin/stale.py's occurrences within the span, six weeks each side of today, and "
          "nothing the browser walked", got == occ and len(got) >= 2, (got, occ))
    check("...and the deposit falls on its day, and the dinner at its time",
          [x['day'] for x in tl['events'] if x.get('clause') == 'deposit-due'] == [D(3)]
          and [(x['day'], x['time']) for x in tl['events'] if x['bean'] == 'dinner'] == [(D(5), '19:00')], tl['events'])
    rc, out = run(PY, 'bin/leads.py', '--for', 'sam', '--json')
    leads = json.loads(out) if rc == 0 else []
    q = E['drawings']['waits']
    check("queue: the reader's leads are bin/leads.py --json's for them, grouped by what each waits on — Sam's parked "
          "decision, and not Ali's deposit, which is hers",
          sorted((x['kind'], x['about']) for x in q['leads']) == sorted((x['kind'], x['about']) for x in leads)
          and ('decision', 'camera-insurance') in [(x['kind'], x['about']) for x in q['leads']]
          and not [x for x in q['leads'] if x['kind'] == 'obligation'], (q, leads))
    sh = (E.get('sheets') or {}).get('camera') or {}
    pay = next((x for r in sh.get('rows', []) if r['verb'] == 'pay' for x in r['statements'] if x['key'] == 'pay#camera'), {})
    check("sheet: a payment shows the shares that take it as their `of` beneath it — its `bear`s — and who said it",
          sorted(d['key'] for d in pay.get('dependents', [])) == ['bear#camera-ali', 'bear#camera-sam']
          and (pay.get('known') or {}).get('by') == 'sam' and sh['verbs']['pay']['required'] == ['by', 'of'], pay)
    ins = next((x for r in ((E.get('sheets') or {}).get('loan') or {}).get('rows', []) for x in r['statements']
                if x['key'] == 'pay#the-loan'), {})
    dep = next((x for r in ((E.get('sheets') or {}).get('loan') or {}).get('rows', []) for x in r['statements']
                if x['key'] == 'pay#deposit'), {})
    check("...a clause that asks a payment stands under it, and a payment no `bear` names shows the law's default: its "
          "payer bears it, alone",
          [d['key'] for d in dep.get('dependents', [])] == ['obligatory#deposit-due']
          and [(d['verb'], d['by']) for d in dep.get('defaults', [])] == [('bear', 'ali')]
          and not ins.get('defaults'), (dep, ins))
    ph = next((x for r in ((E.get('sheets') or {}).get('ali') or {}).get('rows', []) for x in r['statements']
               if x['key'] == 'name#phone'), {})
    check("held: the report — the gardener's page of one file — carries the held phone's place and never its value",
          (ph.get('held') or {}).get('host') == 'laptop' and 'roles' not in ph and '5555550100' not in json.dumps(P), ph)
    code = ("import json, os, sys; sys.path.insert(0, os.path.join(%r, 'assets', 'view', 'lib')); import view_model as vm, "
            "view_engraved as ve; p = vm.init(%r); assert not p, p; s = ve.sheet('ali', lambda a, b, p=None: b != 'laptop'); "
            "print(json.dumps([x['held'] for r in s['rows'] for x in r['statements'] if x['key'] == 'name#phone']))" % (G, G))
    rc, out = run(PY, '-c', code)
    check("...and to a reader who may not read the machine that keeps it, the machine is not named: kept on one this page "
          "does not name", rc == 0 and [(x['host'], x['here']) for x in json.loads(out.strip().splitlines()[-1])] == [(None, False)],
          out[-600:])
    for lang in ('en', 'fa'):
        rc, out = run(PY, 'assets/view/bin/view.py', 'report', '--out', os.path.join(T, f'page-{lang}.html'), '--lang', lang)
        check(f"view report --lang {lang}: the offline page is written", rc == 0, out[-600:])

    # ------------------------------------------------------------------ part 3: the one write path, through the served page
    import http.cookiejar, time, urllib.error, urllib.parse, urllib.request
    put('beans/sam.md', get('beans/sam.md').replace('\n---\n', '\n  - grant: { id: reader-reads, by: self, to: [%s], of: [handplace, camera, loan, dinner], as: read }\n'
                                                   '  - say: { by: sam, of: [reader-reads], at: now }\n---\n' % READER, 1))
    rc, out = run(PY, 'bin/save.py', 'sam', "the reader may read the page, the agreements and the dinner",
                  '--body', f'- action: [[sam]] grants [[{READER}]] to read [[handplace]], [[camera]], [[loan]] and [[dinner]].')
    check("the gardener's grant to the reader is saved", rc == 0, out[-800:])
    CFG = os.path.join(T, 'host', 'serve.json')
    for user, bean in (('sam', 'sam'), ('reader', READER)):
        rc, out = run(PY, 'assets/view/bin/view.py', 'serve-init', '--config', CFG, '--user', user, '--bean', bean)
    import socket as _so
    _s = _so.socket(); _s.bind(('127.0.0.1', 0)); PORT = _s.getsockname()[1]; _s.close()
    C = json.load(open(CFG))
    C.update(listen='127.0.0.1:%d' % PORT, recheck_seconds=1, request_seconds=5)
    C['users']['sam']['lang'] = 'fa'
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
            r = op.open(BASE + '/'); html_ = r.read().decode()
        except urllib.error.HTTPError as e:
            return e.code, {}, ''
        m = re.search(r'<script type="application/json" id="viewdata">(.*?)</script>', html_, re.S)
        return 200, (json.loads(m.group(1).replace('<\\/', '</')) if m else {}), html_

    def settle(op):
        """The host starts itself again on a ledger head another hand moved (view_serve `maybe_reexec`): asked again
        until it answers on the new head."""
        want = head()[:10]
        for _ in range(200):
            try:
                st_, p_, _h = page_of(op)
                if st_ == 200 and (p_.get('live') or {}).get('head') == want:
                    return p_
            except Exception:                   # a connection the host closed as it started again
                pass
            time.sleep(0.25)
        return {}

    def post(op, obj, csrf):
        req = urllib.request.Request(BASE + '/api/write', json.dumps(obj).encode(),
                                     {'Content-Type': 'application/json', 'X-View-CSRF': csrf})
        try:
            r = op.open(req, timeout=300); return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b'{}')
    try:
        SAM, RDR = session('sam'), session('reader')
        st, PS, html_sam = page_of(SAM)
        st2, PR, html_rdr = page_of(RDR)
        check("serve: each viewer is sent the page, the engraved readings their own", st == 200 and st2 == 200
              and PS['engraved']['reader'] == 'sam' and PR['engraved']['reader'] == READER, (st, st2))
        phs = next((x for r in PS['engraved']['sheets']['ali']['rows'] for x in r['statements'] if x['key'] == 'name#phone'), {})
        check("held: the host that holds the store sends the phone to the gardener, who may read it — on this machine only",
              (phs.get('roles') or {}).get('as') == '+15555550100' and phs['held']['here'] is True, phs)
        check("...and to the reader, who may not read Ali, nothing of her: no sheet, no phone, not her name in a reading",
              'ali' not in PR['engraved']['sheets'] and '5555550100' not in html_rdr
              and not any(n.get('title') == 'Ali' for n in PR['engraved']['drawings']['money']['nodes']),
              (sorted(PR['engraved']['sheets']), PR['engraved']['drawings']['money']['nodes']))
        check("...and the reader's flows name the party they may not read `someone`, never by id",
              [n['id'] for n in PR['engraved']['drawings']['money']['nodes'] if n.get('someone')]
              and all(a['from'].startswith('someone-') or a['from'] != 'ali' for a in PR['engraved']['drawings']['money']['arrows']),
              PR['engraved']['drawings']['money'])
        dflt = lambda p: next((x for r in ((p['engraved']['sheets'].get('loan') or {}).get('rows') or [])
                               for x in r['statements'] if x['key'] == 'pay#deposit'), {}).get('defaults') or [{}]
        check("...and nowhere else a being is named: the deposit's default names its payer by the payment's own word, "
              "and her title only to whom may read her; the gardener only to whom may read the gardener",
              dflt(PS)[0].get('title') == 'Ali' and dflt(PR)[0].get('by') == 'ali' and dflt(PR)[0].get('title') is None
              and PS['engraved']['settings']['garden']['gardener'] == 'sam'
              and PR['engraved']['settings']['garden']['gardener'] == ''
              and PR['engraved']['settings']['garden']['me'] == READER and '"title": "Ali"' not in json.dumps(PR['engraved']),
              (dflt(PS), dflt(PR), PR['engraved']['settings']))
        csrf_s, csrf_r = PS['live']['csrf'], PR['live']['csrf']
        h0, j0 = head(), get('log/journal.md')
        st, a = post(SAM, {'bean': 'camera', 'ops': [
            {'op': 'change', 'key': 'pay#lens', 'roles': {'by': 'sam', 'of': {'count': '120.00', 'unit': 'XTS'}, 'through': 'agreed',
                                                          'note': 'the lens, and its hood'}},
            {'op': 'add', 'verb': 'bear', 'roles': {'by': 'sam', 'of': 'lens', 'share': '2'}},
            {'op': 'remove', 'key': 'bear#lens-sam'}]}, csrf_s)
        entry = get('log/journal.md')[len(j0):]
        log = run('git', 'log', '--format=%H', f'{h0}..HEAD')[1].split()
        check("sheet: a Save of a change, an add and a remove is ONE commit with ONE journal entry naming each, and the "
              "gate passes it", st == 200 and a.get('ok') and len(log) == 1 and len(re.findall(r'(?m)^## ', entry)) == 1
              and 'changed `pay#lens`' in entry and 'added `bear#bear-1`' in entry and 'removed `bear#lens-sam`' in entry
              and clean() and gate()[0] == 0, (st, a, entry))
        bean = get('beans/camera.md')
        check("...each through bin/safe.py by its key — the lens rewritten in place, the share appended, the other taken "
              "out — known by the writer's `say`", "count: '120.00'" in bean and 'id: bear-1' in bean and 'lens-sam' not in bean
              and re.search(r'say: \{ by: sam, of: \[lens, bear-1\], at: "\d{4}', bean), bean[-900:])
        h1 = head()
        st, a = post(SAM, {'bean': 'camera', 'ops': [
            {'op': 'add', 'verb': 'pay', 'id': 'strap', 'roles': {'by': 'ali', 'of': {'count': '7.00', 'unit': 'XTS'}}},
            {'op': 'add', 'verb': 'bear', 'roles': {'by': 'ali', 'of': 'strap'}}]}, csrf_s)
        check("a refused Save keeps nothing — no commit, the tree clean, no journal entry — and its message lands on its "
              "fact: the share that only says what the law derives (its payer bears it alone)",
              st == 422 and not a.get('ok') and head() == h1 and clean() and get('log/journal.md') == j0 + entry
              and any(x.get('op') == 1 and 'placeholder' in x['message'] for x in a.get('refusals', [])), (st, a))
        st, a = post(SAM, {'bean': 'camera', 'ops': [{'op': 'add', 'verb': 'pay', 'roles': {'by': 'ali', 'towards': 'sam',
                                                                                             'of': {'count': '1', 'unit': 'XTS'}}}]}, csrf_s)
        check("...and a role the verb does not take is refused before anything is written, at its op",
              st == 422 and a['refusals'][0]['op'] == 0 and 'takes no towards' in a['refusals'][0]['message'] and clean(), a)
        st, a = post(SAM, {'bean': 'camera', 'ops': [{'op': 'remove', 'key': 'bear#camera-ali'},
                                                     {'op': 'remove', 'key': 'bear#camera-ali'}]}, csrf_s)
        check("...two ops on one statement are refused, at the second", st == 422 and a['refusals'][0]['op'] == 1 and clean(), a)
        st, a = post(SAM, {'bean': 'camera', 'ops': [{'op': 'change', 'header': 'title',
                                                     'value': 'camera — Sam and Ali bought a camera and a lens together'}]}, csrf_s)
        check("...and a Save that says what the being says already writes nothing", st == 422 and head() == h1
              and 'nothing to write' in a['refusals'][0]['message'], a)
        st, a = post(RDR, {'bean': 'dinner', 'ops': [{'op': 'change', 'header': 'title', 'value': 'dinner — شام سام'}]}, csrf_r)
        check("title: a reader with no grant to write is refused, at the title, and nothing is written",
              st == 422 and a['refusals'][0]['fact'] == 'header:title' and 'no grant opens the title' in a['refusals'][0]['message']
              and clean(), a)
        st, a = post(SAM, {'bean': 'loan', 'ops': [{'op': 'change', 'header': 'title', 'value': 'loan — وام سام به علی، Sam to Ali'}]}, csrf_s)
        check("title: the gardener edits a title, in the garden's language and mixed scripts, as a header edit through "
              "bin/safe.py, journalled", st == 200 and a.get('ok') and 'title: "loan — وام سام به علی، Sam to Ali"' in get('beans/loan.md')
              and 'changed the title' in get('log/journal.md').rsplit('\n## ', 1)[-1] and clean(), a)
        put('beans/sam.md', get('beans/sam.md').replace('\n---\n', '\n  - grant: { id: reader-titles, by: self, to: [%s], of: [dinner], as: write, cover: { parts: [title] } }\n'
                                                       '  - say: { by: sam, of: [reader-titles], at: now }\n---\n' % READER, 1))
        rc, out = run(PY, 'bin/save.py', 'sam', "the reader may write the dinner's title",
                      '--body', f'- action: [[sam]] grants [[{READER}]] to write the title of [[dinner]], and nothing else of it.')
        settle(RDR)
        st, a = post(RDR, {'bean': 'dinner', 'ops': [{'op': 'change', 'header': 'title', 'value': 'dinner — شام سام'}]}, csrf_r)
        check("title: a grant whose `cover` opens the title alone lets the reader write it — admin mode is the sheet with a "
              "write grant", rc == 0 and st == 200 and a.get('ok') and 'title: "dinner — شام سام"' in get('beans/dinner.md'), (out[-400:], st, a))
        st, a = post(RDR, {'bean': 'dinner', 'ops': [{'op': 'remove', 'key': 'attend#sam-comes'}]}, csrf_r)
        check("...and nothing else of the being: a statement the cover does not open is refused, at its fact",
              st == 422 and a['refusals'][0]['fact'] == 'attend#sam-comes' and 'id: sam-comes' in get('beans/dinner.md'), a)
        st, a = post(SAM, {'kind': 'person', 'ops': [{'op': 'change', 'header': 'summary', 'value': 'a neighbour Sam lends tools to'},
                                                     {'op': 'add', 'verb': 'own', 'roles': {'by': 'theone', 'of': 'self'}}]}, csrf_s)
        nb = a.get('bean') or ''
        check("new being: an empty sheet's first Save mints an opaque person, its title its id, its file written whole and "
              "saved", st == 200 and a.get('ok') and re.fullmatch(r'p-[0-9a-f]{8}', nb)
              and f'title: "{nb}"' in get(f'beans/{nb}.md') and clean(), (st, a))
        st, a = post(RDR, {'kind': 'person', 'ops': [{'op': 'add', 'verb': 'own', 'roles': {'by': 'theone', 'of': 'self'}}]}, csrf_r)
        check("...and a reader no grant opens it to may not make one", st == 422 and 'may not make' in a['refusals'][0]['message'], a)
        st, a = post(SAM, {'m': 'ali', 'w': 0, 'ops': [{'op': 'add', 'verb': 'pay', 'roles': {'by': 'ali', 'to': 'ali',
                                                                                              'of': {'count': '3.00', 'unit': 'XTS'}}}]}, csrf_s)
        check("a drawing's form of a verb adds only its verb, with the roles it presets as it fixes them",
              st == 400 and 'as it fixes them' in json.dumps(a), (st, a))
        st, a = post(SAM, {'m': 'ali', 'w': 0, 'ops': [{'op': 'add', 'verb': 'pay', 'roles': {'by': 'ali', 'to': 'sam',
                                                                                              'of': {'count': '3.00', 'unit': 'XTS'}}}]}, csrf_s)
        check("...and adds it to the being the drawing draws, by the one write path, judged as a Save is",
              st == 200 and a.get('ok') and a.get('bean') == 'ali' and "to: sam" in get('beans/ali.md'), (st, a))
        st, a = post(SAM, {'bean': 'ali', 'ops': [{'op': 'change', 'key': 'name#phone', 'held': True,
                                                   'roles': {'by': 'e164', 'of': 'self', 'as': '+15555550199'}}]}, csrf_s)
        rec = run(PY, 'bin/held.py', 'resolve', re.search(r'root:vault/[0-9a-f]{32}', get('beans/ali.md')).group(0))[1]
        check("held: a held value edited in the Save is sealed by bin/held.py — the store holds the new value, the commit "
              "only the pointer", st == 200 and a.get('ok') and '+15555550199' in rec and '5555550199' not in
              run('git', 'show', 'HEAD')[1] and '5555550199' not in get('beans/ali.md'), (st, a, rec))
        audit = open(C['audit_log']).read()
        check("every write is audited with its answer: saved, or refused and why", '"mode": "saved"' in audit
              and '"mode": "refused"' in audit and 'no grant opens the title' in audit, audit[-600:])
        st, PS2, html_sam = page_of(SAM)
        open(os.path.join(T, 'served-fa.html'), 'w', encoding='utf-8').write(html_sam)

        # THE SERVED PAGE, LIVE, UNDER ITS POLICY (view_serve's Content-Security-Policy: the page's scripts by their
        # hashes, view_report.SCRIPTS, the renderers among them): a proxy in front of the host signs the gardener in and
        # adds a driver, allowed by its own hash and nothing else of the policy changed, and a script the policy must
        # refuse; the driver draws every drawing at every lens, opens Ali's sheet, edits her summary and Saves — the
        # renderers' own fetch, with the page's CSRF token — and the page the Save reloads shows the new head.
        _browser = next((b for b in ('chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable') if shutil.which(b)), None)
        if _browser:
            import base64, hashlib, http.client, threading
            from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
            jar = next(x.cookiejar for x in SAM.handlers if isinstance(x, urllib.request.HTTPCookieProcessor))
            cookie = '; '.join('%s=%s' % (c.name, c.value) for c in jar if c.name == 'view_session')
            SUMMARY = 'Ali, who shares costs with Sam — and a lens, now'
            LIVE_DRIVE = """<script>
window.__errs = []; window.__csp = [];
window.addEventListener('error', e => window.__errs.push(String(e.message)));
window.addEventListener('unhandledrejection', e => window.__errs.push('unhandled: ' + e.reason));
document.addEventListener('securitypolicyviolation', e => window.__csp.push(e.effectiveDirective + ' ' + (e.sample || e.blockedURI)));
const __kept = v => { try { if (v === undefined) return JSON.parse(sessionStorage.getItem('__first') || 'null'); sessionStorage.setItem('__first', JSON.stringify(v)); } catch (e) { return null; } };
// what the Save's write answered, kept as it comes, before the page the Save reloads replaces this one
let __wrote; const __written = new Promise(r => { __wrote = r; });
const __fetch = window.fetch.bind(window);
window.fetch = (u, o) => __fetch(u, o).then(r => { if (String(u) === '/api/write') r.clone().json().then(j => {
  const k = __kept() || {}; k.writes = (k.writes || []).concat([r.status]); k.ok = !!j.ok; k.refusals = j.refusals || []; __kept(k); __wrote(k); }); return r; });
const __wait = ms => new Promise(r => setTimeout(r, ms));
const __done = o => { const pre = document.createElement('pre'); pre.id = '__result'; pre.textContent = JSON.stringify(o); document.body.appendChild(pre); };
const __go = (t, l) => { document.querySelector('.tab[data-t="' + t + '"]').click(); document.querySelector('#lens button[data-l="' + l + '"]').click(); };
window.addEventListener('load', async () => {
 const first = __kept();
 if (first && first.saving) { let summary = '';
  try { __go('ali', 'operate'); summary = (document.querySelector('#view .eg-summary') || {}).textContent || ''; } catch (e) { window.__errs.push('driver: ' + e.message); }
  for (let i = 0; i < 20 && !window.__csp.length; i++) await __wait(100);   // the policy's report is an event of its own
  return __done({first, errs: window.__errs, csp: window.__csp, summary, injected: window.__injected === 1}); }
 const out = {}; let editing = false;
 try {
  const tabs = [...document.querySelectorAll('.tab')].map(b => b.dataset.t), lens = [...document.querySelectorAll('#lens button')].map(b => b.dataset.l);
  for (const t of tabs) for (const l of lens) { __go(t, l); out[t + '/' + l] = (document.querySelector('#view').innerText || '').length; }
  __go('ali', 'operate'); document.querySelector('#view [data-do="edit"]').click();
  const s = document.querySelector('#view [name="header.summary"]'); editing = !!s; s.value = %s;
 } catch (e) { window.__errs.push('driver: ' + e.message); }
 __kept({errs: window.__errs.slice(), csp: window.__csp.slice(), out, editing, injected: window.__injected === 1, saving: true});
 try { document.querySelector('#view [data-do="save"]').click(); } catch (e) { window.__errs.push('driver: ' + e.message); }
 const k = (await Promise.race([__written, __wait(60000)])) || __kept(); await __wait(3000);
 __done({first: k, errs: window.__errs, csp: window.__csp, summary: null, reloaded: false}); });   // a Save refused stays here
</script>""" % json.dumps(SUMMARY)
            body = LIVE_DRIVE[len('<script>'):-len('</script>')]
            dh = "'sha256-%s'" % base64.b64encode(hashlib.sha256(body.encode('utf-8')).digest()).decode()
            plog = []

            class Proxy(BaseHTTPRequestHandler):
                def log_message(self, *a):
                    pass

                def _fwd(self, method):
                    n = int(self.headers.get('Content-Length') or 0)
                    data = self.rfile.read(n) if n else None
                    plog.append((method, self.path))
                    c = http.client.HTTPConnection('127.0.0.1', PORT, timeout=300)
                    hd = {'Cookie': cookie}
                    for k in ('Content-Type', 'X-View-CSRF'):
                        if self.headers.get(k):
                            hd[k] = self.headers[k]
                    c.request(method, self.path, data, hd)
                    r = c.getresponse()
                    data, ctype, csp = r.read(), r.getheader('Content-Type') or '', r.getheader('Content-Security-Policy') or ''
                    if self.path == '/' and ctype.startswith('text/html'):
                        pg = data.decode('utf-8').replace('<head>', '<head>' + LIVE_DRIVE, 1)
                        data = pg.replace('<main>', '<main><script>window.__injected = 1</script>', 1).encode('utf-8')
                        csp = csp.replace('script-src ', 'script-src %s ' % dh, 1)
                    self.send_response(r.status)
                    if ctype:
                        self.send_header('Content-Type', ctype)
                    if csp:
                        self.send_header('Content-Security-Policy', csp)
                    self.send_header('Content-Length', str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)

                def do_GET(self):
                    self._fwd('GET')

                def do_POST(self):
                    self._fwd('POST')
            settle(SAM)
            _ps = socket.socket(); _ps.bind(('127.0.0.1', 0)); PXP = _ps.getsockname()[1]; _ps.close()
            px = ThreadingHTTPServer(('127.0.0.1', PXP), Proxy)
            px.daemon_threads = True
            threading.Thread(target=px.serve_forever, daemon=True).start()
            h2, j2 = head(), get('log/journal.md')
            try:
                r = subprocess.run([_browser, '--headless=new', '--disable-gpu', '--no-sandbox', '--virtual-time-budget=120000',
                                    '--dump-dom', 'http://127.0.0.1:%d/' % PXP], capture_output=True, text=True,
                                   encoding='utf-8', errors='replace', timeout=400)
                m = re.search(r'<pre id="__result">(.*?)</pre>', r.stdout, re.S)
                import html as _html
                lv = json.loads(_html.unescape(m.group(1))) if m else {'errs': ['no result: ' + (r.stderr or '')[-300:]]}
            except (OSError, subprocess.SubprocessError) as e:
                lv = {'errs': ['the browser did not run: %s' % e]}
            finally:
                px.shutdown()
            f1 = lv.get('first') or {}
            draws = {k: v for k, v in (f1.get('out') or {}).items() if '/' in k}
            check("served under its policy, in a browser: every drawing at every lens is drawn by the renderers the policy "
                  "allows by their hashes, with no error and no script refused but the one injected, which does not run",
                  not f1.get('errs') and len(draws) == 4 * 5 and all(v > 20 for v in draws.values())
                  and f1.get('csp') == ['script-src-elem inline'] and f1.get('injected') is False, lv)
            entry2 = get('log/journal.md')[len(j2):]
            check("...and a sheet's Save there is the renderers' own write, its CSRF token the page's: one commit, one "
                  "journal entry, and the page the Save reloads, again under its policy, shows the new head",
                  f1.get('editing') and f1.get('writes') == [200] and f1.get('ok') is True
                  and ('POST', '/api/write') in plog and len(run('git', 'log', '--format=%H', f'{h2}..HEAD')[1].split()) == 1
                  and SUMMARY in get('beans/ali.md') and 'changed the summary' in entry2 and clean()
                  and lv.get('summary') == SUMMARY and not lv.get('errs') and lv.get('csp') == ['script-src-elem inline'],
                  (lv, plog[-6:], entry2[-400:]))
        else:
            print("NOTE  the served page was not driven in a browser under its policy: none on this machine")
    finally:
        srv.terminate()
        srv.wait(timeout=20)

    # ------------------------------------------------------------------ part 4: the pages in a browser
    browser = next((b for b in ('chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable') if shutil.which(b)), None)
    DRIVE = """<script>
window.__errs = []; window.addEventListener('error', e => window.__errs.push(String(e.message)));
window.addEventListener('load', () => { const out = {}; let sheet = '';
 try { const tabs = [...document.querySelectorAll('.tab')].map(b => b.dataset.t), lens = [...document.querySelectorAll('#lens button')].map(b => b.dataset.l);
  for (const t of tabs) for (const l of lens) { document.querySelector('.tab[data-t="' + t + '"]').click(); document.querySelector('#lens button[data-l="' + l + '"]').click();
   out[t + '/' + l] = (document.querySelector('#view').innerText || '').length; }
  for (const lay of ['month', 'list', 'week']) { document.querySelector('.tab[data-t="time"]').click(); document.querySelector('#lens button[data-l="operate"]').click();
   const b = document.querySelector('[data-layout="' + lay + '"]'); if (b) b.click(); out['time/' + lay] = (document.querySelector('#view').innerText || '').length; }
  document.querySelector('.tab[data-t="money"]').click(); document.querySelector('#lens button[data-l="understand"]').click();
  const o = document.querySelector('#view [data-action="open"]'); if (o) o.click();
  const d = document.querySelector('dialog.eg-dialog'); sheet = d ? d.innerText : '';
  const e = d && d.querySelector('[data-do="edit"]'); if (e) { e.click(); out.editing = d.querySelectorAll('.eg-editing').length;
   out.inputs = [...d.querySelectorAll('input,select,textarea')].map(i => i.name + '=' + i.value); }
  out.dir = document.documentElement.dir;
 } catch (e) { window.__errs.push('driver: ' + e.message); }
 const pre = document.createElement('pre'); pre.id = '__result'; pre.textContent = JSON.stringify({errs: window.__errs, out, sheet}); document.body.appendChild(pre); });
</script>"""
    if browser:
        import html as _html
        for name, want in (('page-en.html', 'ltr'), ('page-fa.html', 'rtl'), ('served-fa.html', 'rtl')):
            src = os.path.join(T, name)
            if not os.path.isfile(src):
                check(f"browser: {name} drawn", False, "not written")
                continue
            dr = os.path.join(T, 'drive-' + name)
            with open(dr, 'w', encoding='utf-8') as fh:
                fh.write(open(src, encoding='utf-8').read().replace('<head>', '<head>' + DRIVE, 1))
            r = subprocess.run([browser, '--headless=new', '--disable-gpu', '--no-sandbox', '--virtual-time-budget=6000',
                                '--dump-dom', 'file://' + dr], capture_output=True, text=True, encoding='utf-8',
                               errors='replace', timeout=120)
            m = re.search(r'<pre id="__result">(.*?)</pre>', r.stdout, re.S)
            res = json.loads(_html.unescape(m.group(1))) if m else {'errs': ['no result: ' + r.stderr[-300:]], 'out': {}}
            out = res.get('out') or {}
            check(f"browser: {name} — every drawing at every lens, the timeline's three layouts and a sheet opened, in a "
                  f"{want} page, with no exception", not res['errs'] and out.get('dir') == want
                  and len([k for k in out if '/' in k]) == 4 * 5 + 3 and all(v > 20 for k, v in out.items() if '/' in k)
                  and res.get('sheet'), res)
            if name == 'served-fa.html':
                ins = out.get('inputs') or []
                check("...and on the served page the gardener's sheet of Ali offers its one Edit, which turns every fact "
                      "into its widget in place — her title and summary, and her held phone, its value sent to the holder "
                      "on this machine", out.get('editing') == 1 and any(i.startswith('header.title=Ali') for i in ins)
                      and any(i.startswith('header.summary=') for i in ins) and any(i.endswith('.as=+15555550199') for i in ins),
                      out)
    else:
        print("NOTE  the pages were not drawn in a browser: none on this machine")
finally:
    if TRACES:
        print("TRACEBACKS:\n" + "\n---\n".join(TRACES[:3]))
    shutil.rmtree(T, ignore_errors=True)

print(f"\nview_handplace: {len(FAILS)} failed" + (": " + ", ".join(FAILS) if FAILS else ""))
sys.exit(1 if FAILS or TRACES else 0)
