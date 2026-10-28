#!/usr/bin/env python3
"""view_pages_garden — a garden test/render/view_pages.mjs serves as its page beans: invented beings, grown from a daftar
tree whose view draws pages of readings, taking the view profile. Not a suite: view_pages.mjs runs it.

    python3 test/render/view_pages_garden.py <daftar tree> <folder>      # prints {"garden": …}

Sam keeps it and mends bicycles on a walk (handed over, looked at, collected); a repair waits at its second step. A
yoga class meets each Tuesday and Sunday of an ISO week, its first session an attendance at its moment. Three page
beans, placed first, second and third: what waits (a queue), the repair (its sheet, its summary Sam may change), and
the time (a timeline of what has a day).
"""
import datetime
import json
import os
import sys

tree, folder = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(tree, 'test'))
import grow  # noqa: E402

PY = sys.executable
G = os.path.join(folder, 'garden')
TODAY = datetime.date.today()
FIRST = TODAY - datetime.timedelta(days=3)
WEEK = f"{FIRST.isocalendar()[0]}-W{FIRST.isocalendar()[1]:02d}-{FIRST.isocalendar()[2]}"
STORY = ('purpose: "{p}", outcome: "{p}", stages: [{{label: Read, doer: the view}}, {{label: Draw, doer: the view}}, '
         '{{label: Open, doer: the reader}}], questions: [{{lens: orient, ask: "{p}"}}], blind: [{{what: "what nobody wrote down"}}]')


def write(rel, text):
    p = os.path.join(G, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)


def read(rel):
    with open(os.path.join(G, rel), encoding='utf-8') as fh:
        return fh.read()


def must(r, what):
    if r.returncode != 0:
        sys.exit(f'{what}: {r.out[-1500:]}')


rel = grow.release(os.path.join(folder, 'release'))
must(grow.garden(rel, G, 'sam', '--gardener-name', 'Sam', '--profile', 'view'), 'the garden')
v = read('VOCAB.md')
kind = '  - { kind: procedure, nature: sayable, meaning: "a way a thing is done, step by step: a walk" }\n'
write('VOCAB.md', v.replace('kinds: []\n', 'kinds:\n' + kind, 1) if 'kinds: []\n' in v else v.replace('---\n', '---\nkinds:\n' + kind, 1))
write('mappings/walk-repair.md', '''---
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
write('beans/repair-1.md', '''---
bean: repair-1
kind: contract
title: "repair-1 — a bicycle with a bent wheel"
summary: "Sam mends a bicycle"
statements:
  - say:  { by: sam, at: now }
  - own:  { by: theone, of: self }
  - be:   { id: course, by: self, at: walk-repair, as: order }
  - move: { by: sam, of: self, through: course, at: [now, "walk-repair#handed-over"] }
  - move: { by: sam, of: self, through: course, at: [now, "walk-repair#looked-at"] }
---
A repair.
''')
write('beans/class-yoga.md', f'''---
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
PAGES = (
    ('page-now', 'Now', 1, f'  - draw: {{ id: waits, by: self, of: [sam], drawing: {{ label: Now, archetype: queue, {STORY.format(p="what waits")} }} }}\n'
                           '  - draw: { id: page, by: self, of: [waits], page: { visibility: private } }\n'),
    ('page-repair', 'Repair', 2, f'  - draw: {{ id: repair, by: self, of: [repair-1], drawing: {{ label: Repair, archetype: sheet, {STORY.format(p="the repair")} }} }}\n'
                                 '  - draw: { id: page, by: self, of: [repair], page: { visibility: private, fields: [ { kind: contract, fact: summary, shown_from: understand }, { kind: contract, fact: move, shown_from: understand } ] } }\n'),
    ('page-time', 'Time', 3, '  - reckon: { id: dated, reading: { what: "what has a day", steps: [ { id: e, op: select, kind: event } ] } }\n'
                             f'  - draw: {{ id: time, by: self, of: [sam], drawing: {{ label: Time, archetype: timeline, selection: dated, layouts: [list, week], {STORY.format(p="when")} }} }}\n'
                             '  - draw: { id: page, by: self, of: [time], page: { visibility: private } }\n'))
for bid, title, place, draws in PAGES:
    write(f'beans/{bid}.md', f'---\nbean: {bid}\nkind: service\ntitle: "{title}"\nsummary: "a page of Sam\'s handplace"\n'
          'statements:\n  - say: { by: sam, at: now }\n  - own: { by: sam, of: self }\n'
          '  - be: { by: self, at: "uri:http://127.0.0.1:8770/", as: location }\n'
          f'  - be: {{ by: self, at: "ordinal:{place}", as: order }}\n' + draws + '---\nA page.\n')
must(grow.run(PY, 'bin/save.py', 'sam', 'RULE-CHANGE: a repair on its walk, a class, and three pages', '--body',
              '- ratified_by: sam', '- action: wrote [[walk-repair]], [[repair-1]], [[class-yoga]], [[page-now]], '
              '[[page-repair]] and [[page-time]]; VOCAB.md holds the kind of a walk', cwd=G), 'the save')
print(json.dumps({'garden': G}))
