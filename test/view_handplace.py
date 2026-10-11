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

Run: python3 test/view_handplace.py   (0 = green)
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

STORY = ('purpose: "{p}", outcome: "{o}", stages: [{{label: Read the garden, doer: the view}}, {{label: Draw what it says, '
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
DRAWINGS = (drawing('waits', 'handplace', 'queue', p="What waits for the reader", o="Nothing waits unseen",
                    q="What needs me now?", b="what nobody has written down")
            + drawing('time', 'handplace', 'timeline', 'selection: dated, layouts: [week, month, list], axes: { inline: time }',
                      p="When each thing falls", o="No day passes unseen", q="When?", b="what has no day")
            + drawing('money', 'handplace', 'flows', 'nodes: parties, selection: agreements',
                      p="Who owes whom", o="Every debt is read, never kept", q="Who owes whom?", b="money not recorded")
            + drawing('ali', 'ali', 'sheet', 'new: [person], writes: [{ verb: pay, preset: { to: sam } }]',
                      p="Ali as she stands", o="One place to change her", q="Who is Ali?", b="what she has not said"))
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
finally:
    if TRACES:
        print("TRACEBACKS:\n" + "\n---\n".join(TRACES[:3]))
    shutil.rmtree(T, ignore_errors=True)

print(f"\nview_handplace: {len(FAILS)} failed" + (": " + ", ".join(FAILS) if FAILS else ""))
sys.exit(1 if FAILS or TRACES else 0)
