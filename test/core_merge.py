#!/usr/bin/env python3
"""The statement merge (core/guide/MERGE.md), and the gate and the merge each taken by the law a garden runs (v1 part 3).

Part one merges beans as texts through core/merge.py: a case for each rule of MERGE.md — a statement's form, the set
three ways, a disagreement side by side, an id naming one statement, knowing kept, the order, the header key by key,
`tags` as a set, `details` leaf by leaf, the body line by line, a bean both sides added — and the invariants measured on
every merge the suite makes: one result whichever side is ours (byte for byte), lossless, idempotent, and no moment of
its own. The driver's refusal leaves ours as it was.

Part two grows a garden (seed/germinate.sh), which takes the hooks and the merge driver from bin/install.py. While it
pins std-vocab, its gate is today's; once it pins the core — the adoption judged by the core — `daftar check`,
bin/dmcheck.py and the hooks run the core's gate. Then two branches change one bean and git merges them for real: the
driver merges the statements, a merge git commits itself is refused until an entry of its own names the bean it merged,
and `git merge --no-commit` with bin/dmsave.py commits it through the core's gate; a bean only the other side changed
comes through as it was committed; a true conflict leaves ours for a person, who settles it; sides written in two laws
are refused; and a bean one side removed and the other changed is git's own conflict.

Run: python3 test/core_merge.py   (0 = green; about a minute, since a save waits for the minute to turn once)
"""
import os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from core import merge as M, read  # noqa: E402

FAILS = []
PY = sys.executable
KNOWING = M.knowing_verbs()


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:1500]))
    if not cond:
        FAILS.append(name)


# ---------------------------------------------------------------------------------------------- part one: texts
ASYM, LOSSY, MOMENTS = [], [], []
STAMP = re.compile(r'\d{4}-\d\d-\d\d \d\d:\d\d')


def forms(text, drop_of=False):
    """The forms of a bean's statements, a knowing act's `of` left out where asked."""
    out = []
    for it in M.Side(text.replace('\r\n', '\n'), 'a side').items:
        v = it.value
        if drop_of and it.verb in KNOWING:
            v = {it.verb: {k: x for k, x in it.roles.items() if k != 'of'}}
        out.append(M.canon(v))
    return out


def merge(o, a, b, label):
    """Merged both ways round; the invariants measured on every clean merge."""
    one, said = M.merge(o, a, b, KNOWING)
    two, said2 = M.merge(o, b, a, KNOWING)
    sides = lambda said: sorted(re.sub(r'\b(ours|theirs)\b', 'a side', p) for p, *_ in said)
    if one != two or (one is None and sides(said) != sides(said2)):
        ASYM.append(label)
    if one is not None and o.strip():
        fo, fa, fb, fr = (set(forms(t, True)) if t.strip() else set() for t in (o, a, b, one))
        if not ((fa - (fo - fb)) | (fb - (fo - fa))) <= fr:      # kept: all but what the other side removed
            LOSSY.append(label)
        if set(STAMP.findall(one)) - set(STAMP.findall(o + a + b)):
            MOMENTS.append(label)
    return one, said


BASE = """---
bean: pot
kind: document
title: "The pot"
summary: "What is in it."
tags: [money, shared]
statements:
  - say: { by: ada, of: [paid, owed], at: "2026-09-20 10:00+03:30" }
  - pay: { id: paid, by: ada, of: { count: "10.00", unit: XTS }, at: 2026-09-20 }
  - obligatory: { id: owed, of: paid }
details:
  ledger: { book: one, pages: [1, 2] }
  note: kept
---
What ada put in.

A second paragraph.
"""


def add(text, *lines):
    """Statements added at the end of the list."""
    return text.replace('\ndetails:', '\n' + '\n'.join('  - ' + ln for ln in lines) + '\ndetails:', 1)


def stmts(text):
    return [ln.strip() for ln in text.split('---')[1].split('\n') if ln.strip().startswith('- ')]


try:
    # A STATEMENT'S FORM: written two ways it is one; differing, two
    a = add(BASE, 'say: { by: ben, of: [x], at: "2026-09-21 09:00+03:30" }', 'pay: { id: x, by: ben, of: { count: "1", unit: XTS } }')
    b = add(BASE, 'say: { by: ben, of: [x], at: "2026-09-21 09:00+03:30" }', "pay: {of: {unit: XTS, count: '1'}, by: ben, id: x}")
    out, _ = merge(BASE, a, b, 'form')
    check("a statement both sides added, written two ways (spacing, quoting, key order), is one: kept once",
          out is not None and len([s for s in stmts(out) if 'id: x' in s]) == 1 and len(stmts(out)) == 5, out)

    a = add(BASE, 'say: { by: ben, of: [rent-a], at: "2026-09-21 09:00+03:30" }', 'pay: { id: rent-a, by: ben, to: ada, of: { count: "5.00", unit: XTS } }')
    b = add(BASE, 'say: { by: cy, of: [rent-b], at: "2026-09-21 09:30+03:30" }', 'pay: { id: rent-b, by: ben, to: ada, of: { count: "6.00", unit: XTS } }')
    out, _ = merge(BASE, a, b, 'disagree')
    check("a disagreement stands side by side: two amounts for one rent are both kept, each with the act that knows it, "
          "and no marker is written",
          out is not None and '"5.00"' in out and '"6.00"' in out and 'by: ben, of: [rent-a]' in out
          and 'by: cy, of: [rent-b]' in out and not re.search(r'conflict|merge_open|<<<<', out), out)

    # THE SET, THREE WAYS
    a = BASE.replace('  - obligatory: { id: owed, of: paid }\n', '').replace('of: [paid, owed]', 'of: [paid]')
    b = BASE.replace('count: "10.00"', 'count: "12.00"').replace('\ndetails:', '\n  - say: { by: ada, of: [paid], at: "2026-09-22 10:00+03:30" }\ndetails:')
    out, _ = merge(BASE, a, b, 'removed')
    check("a statement one side removed is removed, and one the other side changed is the changed one: the change stands",
          out is not None and 'obligatory' not in out and '"12.00"' in out and '"10.00"' not in out, out)

    a = add(BASE, 'say: { by: ben, of: [x], at: "2026-09-21 09:00+03:30" }', 'pay: { id: x, by: ben, of: { count: "1", unit: XTS } }')
    b = add(BASE, 'read: { by: cy, of: [y], at: "2026-09-21 09:30+03:30" }', 'pay: { id: y, by: cy, of: { count: "2", unit: XTS } }')
    out, _ = merge(BASE, a, b, 'order')
    s = stmts(out or '---\n---')
    check("the order: the base's statements in the base's order, then what either side added, by its form",
          s[:3] == stmts(BASE) and s[3:] == sorted(s[3:], key=lambda t: M.canon(read.loads(t)[0])), s)

    # AN ID NAMES ONE STATEMENT
    a = BASE.replace('count: "10.00"', 'count: "11.00"').replace('\ndetails:', '\n  - say: { by: ada, of: [paid], at: "2026-09-22 10:00+03:30" }\ndetails:')
    b = BASE.replace('count: "10.00"', 'count: "12.00"').replace('\ndetails:', '\n  - say: { by: ada, of: [paid], at: "2026-09-22 11:00+03:30" }\ndetails:')
    out, said = merge(BASE, a, b, 'id-changed')
    check("both sides changed one statement differently: refused, the id named with both values",
          out is None and any('`paid`' in p and '11.00' in x and '12.00' in y for p, x, y in said), said)
    a = add(BASE, 'say: { by: ben, of: [z], at: "2026-09-21 09:00+03:30" }', 'pay: { id: z, by: ben, of: { count: "1", unit: XTS } }')
    b = add(BASE, 'say: { by: ben, of: [z], at: "2026-09-21 09:00+03:30" }', 'pay: { id: z, by: ben, of: { count: "2", unit: XTS } }')
    out, said = merge(BASE, a, b, 'id-added')
    check("both sides added two statements under one id: refused", out is None and any('`z`' in p for p, *_ in said), said)

    # KNOWING IS KEPT
    a = add(BASE, 'say: { by: ben, at: "2026-09-21 09:00+03:30" }', 'pay: { id: rent, by: ben, to: ada, of: { count: "5.00", unit: XTS } }')
    b = add(BASE, 'make: { by: ada, of: [gift], at: "2026-09-21 09:30+03:30" }', 'pay: { id: gift, by: ada, to: ben, of: { count: "1.00", unit: XTS } }')
    out, said = merge(BASE, a, b, 'knowing')
    check("an act one side added with no `of` is given one, the ids it covered on its own side; the other side's act is "
          "as it was", out is not None and re.search(r"- say: \{by: ben, of: \[rent\], at: '2026-09-21 09:00\+03:30'\}", out)
          and 'make: { by: ada, of: [gift]' in out and said.get('acts given their `of`') == 1, out)
    out2, _ = merge(BASE, a, BASE, 'knowing-alone')
    check("...and none is given where the other side added nothing it would cover", out2 == a, out2)
    a2 = add(BASE, 'say: { by: ben, at: "2026-09-21 09:00+03:30" }', 'pay: { by: ben, to: ada, of: { count: "5.00", unit: XTS } }')
    out, said = merge(BASE, a2, b, 'knowing-noid')
    check("...refused where what it covered has no id, which an `of` cannot name: given one on its branch, merged again",
          out is None and any('no id' in y for _p, _x, y in said), said)
    a3 = add(a, 'read: { by: cy, at: "2026-09-21 10:00+03:30" }')
    out, said = merge(BASE, a3, b, 'knowing-two')
    check("...refused where one side added two acts with no `of`: which knew what cannot be told from the three sides",
          out is None and any('2 knowing acts' in p for p, *_ in said), said)

    # THE HEADER, KEY BY KEY
    a = BASE.replace('title: "The pot"', 'title: "The pot ada keeps"')
    b = BASE.replace('summary: "What is in it."', 'summary: "What ada put in."')
    out, _ = merge(BASE, a, b, 'header')
    check("the header merges key by key: a key one side changed is that side's",
          out is not None and 'title: "The pot ada keeps"' in out and 'summary: "What ada put in."' in out, out)
    out, said = merge(BASE, a, BASE.replace('title: "The pot"', 'title: "The shared pot"'), 'header-conflict')
    check("...and one both changed differently is a true conflict, named with both values",
          out is None and said == [('title', 'The pot ada keeps', 'The shared pot')], said)
    out, _ = merge(BASE, a, a.replace('summary: "What is in it."', 'summary: "In it."'), 'header-alike')
    check("...one both changed alike is that", out is not None and out.count('The pot ada keeps') == 1 and 'In it.' in out, out)
    a = BASE.replace('tags: [money, shared]', 'tags: [money, cash]')
    b = BASE.replace('tags: [money, shared]', 'tags: [money, shared, bank]')
    out, _ = merge(BASE, a, b, 'tags')
    check("`tags` merge as a set: one removed is removed, each added is kept",
          out is not None and read.loads(out.split('---')[1])['tags'] == ['money', 'bank', 'cash'], out)

    # DETAILS, LEAF BY LEAF
    a = BASE.replace('note: kept', 'note: changed')
    b = BASE.replace('book: one', 'book: two')
    out, _ = merge(BASE, a, b, 'details')
    d = read.loads(out.split('---')[1])['details'] if out else {}
    check("`details` merges leaf by leaf: each side's change to its own leaf stands",
          d == {'ledger': {'book': 'two', 'pages': ['1', '2']}, 'note': 'changed'}, out)
    a = BASE.replace('  note: kept\n', '')
    out, _ = merge(BASE, a, b, 'details-removed')
    d = read.loads(out.split('---')[1])['details'] if out else {}
    check("...a key one side removed stays removed", 'note' not in d and d.get('ledger', {}).get('book') == 'two', out)
    out, said = merge(BASE, BASE.replace('[1, 2]', '[1, 2, 3]'), BASE.replace('[1, 2]', '[2]'), 'details-list')
    check("...a list is one leaf: both changing it differently is a true conflict",
          out is None and [p for p, *_ in said] == ['details.ledger.pages'], said)
    c = BASE.replace('  note: kept\n', '  note: kept   # said by ada\n')
    out, said = merge(c, c.replace('note: kept', 'note: changed'), c.replace('book: one', 'book: two'), 'details-comment')
    check("...refused where `details` is written anew and a comment in it would be lost",
          out is None and any('comment' in p for p, *_ in said), said)

    # THE BODY, LINE BY LINE
    a = BASE.replace('What ada put in.', 'What ada put in, in September.')
    b = BASE + '\nA third paragraph.\n'
    out, _ = merge(BASE, a, b, 'body')
    check("the body merges line by line: both sides' changes to different lines stand",
          out is not None and 'in September.' in out and 'A third paragraph.' in out, out)
    out, said = merge(BASE, a, BASE.replace('What ada put in.', 'What ada gave.'), 'body-conflict')
    check("...lines both changed differently are a true conflict", out is None and 'the body' in said[0][0], said)
    out, said = merge(BASE, BASE.split('\n---\n')[0] + '\n---\n', b, 'body-empty')
    check("...refused where the merged bean would keep no body", out is None, (out, said))

    # A BEAN BOTH SIDES ADDED
    a = add(BASE.replace('  - obligatory: { id: owed, of: paid }\n', '').replace('of: [paid, owed]', 'of: [paid]'))
    b = add(BASE, 'say: { by: ben, of: [x], at: "2026-09-21 09:00+03:30" }', 'pay: { id: x, by: ben, of: { count: "1", unit: XTS } }')
    out, _ = merge('', a, b, 'both-added')
    check("a bean both sides added: its statements are the union of both",
          out is not None and 'obligatory' in out and 'id: x' in out and 'of: [paid, owed]' in out and 'of: [paid],' in out, out)
    out, said = merge('', a, b.replace('"The pot"', '"Another pot"'), 'both-added-title')
    check("...and a header key the two wrote differently is a true conflict", out is None and said[0][0] == 'title', said)
    out, said = merge('', a, b.replace('What ada put in.', 'What ben put in.'), 'both-added-body')
    check("...and so is a body the two wrote differently", out is None and 'the body' in said[0][0], said)

    # WHAT A SIDE WROTE IS KEPT AS IT WROTE IT
    a = BASE.replace('\ndetails:', '\n  # ben said this at the door\n  - read: { by: ben, of: [x], at: "2026-09-21 09:00+03:30" }\n'
                                   '  - pay: { id: x, by: ben, of: { count: "1", unit: XTS } }\ndetails:')
    b = BASE.replace('statements:\n  - ', 'statements:\n- ').replace('\n  - pay', '\n- pay').replace('\n  - obligatory', '\n- obligatory') \
        .replace('note: kept', 'note: changed')
    out, _ = merge(BASE, a, b, 'indent')
    check("a comment above a statement travels with it, and statements a side indented otherwise are written at one indent",
          out is not None and '  # ben said this at the door\n  - read: { by: ben' in out and '\n- ' not in out.split('details:')[0]
          and read.loads(out.split('---')[1])['details']['note'] == 'changed', out)
    c = BASE.replace('\ndetails:', '\n  - say:\n      by: ada\n      note: |\n        # not a comment: the note\'s own line\n\n'
                     '        and a line after a blank one\n      at: "2026-09-20 11:00+03:30"\ndetails:')
    out, _ = merge(c, add(c, 'pay: { id: q, by: ada, of: { count: "1", unit: XTS } }'),
                   c.replace('title: "The pot"', 'title: "Pot"'), 'block')
    note = [x for x in (read.loads(out.split('---')[1]) if out else {}).get('statements', []) if 'note' in x.get('say', {})]
    check("a line inside a block scalar is the value's text, never a comment moved with the next statement",
          note and note[0]['say']['note'] == "# not a comment: the note's own line\n\nand a line after a blank one\n", out)
    a = BASE.replace('\n', '\r\n')
    out, _ = merge(a, a.replace('note: kept', 'note: one'), a.replace('book: one', 'book: two'), 'crlf')
    check("a bean all three sides wrote with CR LF line ends is written so", out is not None and out.count('\r\n') == out.count('\n'), repr(out)[:300])

    # THE INVARIANTS, on every merge above
    a = add(BASE, 'say: { by: ben, at: "2026-09-21 09:00+03:30" }', 'pay: { id: rent, by: ben, to: ada, of: { count: "5.00", unit: XTS } }')
    b = BASE.replace('title: "The pot"', 'title: "Our pot"').replace('note: kept', 'note: two') + 'More.\n'
    out, _ = merge(BASE, a, b, 'idem')
    check("idempotent: a bean merged with itself is itself, and with a side that is the base it is the other side",
          out is not None and M.merge(out, out, out, KNOWING)[0] == out and M.merge(BASE, out, BASE, KNOWING)[0] == out)
    check("deterministic: the same three sides give the same bytes again", out == M.merge(BASE, a, b, KNOWING)[0])
    check("order-agnostic: every merge in this suite gave one result whichever side was ours, byte for byte", not ASYM, ASYM)
    check("lossless: every merge kept each statement either side holds, but what the other side removed", not LOSSY, LOSSY)
    check("no moment of its own: no merge wrote a moment its three sides did not hold", not MOMENTS, MOMENTS)

    # THE DRIVER: refused, ours left as it was
    T = tempfile.mkdtemp(prefix='dmcoremerge-')
    paths = []
    for n, t in (('O', BASE), ('A', BASE.replace('"The pot"', '"One"')), ('B', BASE.replace('"The pot"', '"Two"'))):
        paths.append(os.path.join(T, n))
        with open(paths[-1], 'w', encoding='utf-8', newline='') as fh:
            fh.write(t)
    r = subprocess.run([PY, os.path.join(ROOT, 'core', 'merge.py'), '--file', *paths, 'beans/pot.md'], capture_output=True, text=True, encoding='utf-8', errors='replace')
    check("the driver refuses a true conflict: exit 1, each conflict named with both sides, ours left as it was",
          r.returncode == 1 and 'title: ours One | theirs Two' in r.stderr
          and open(paths[1], encoding='utf-8').read() == BASE.replace('"The pot"', '"One"'), r.stderr)
    with open(paths[2], 'w', encoding='utf-8') as fh:
        fh.write("---\nbean: pot\ngenos: document\ntitle: Two\n---\nToday's words.\n")
    r = subprocess.run([PY, os.path.join(ROOT, 'core', 'merge.py'), '--file', *paths], capture_output=True, text=True, encoding='utf-8', errors='replace')
    check("...and refuses a side that is not a bean in statements, ours left as it was",
          r.returncode == 1 and 'not a bean in statements' in r.stderr, r.stderr)
    shutil.rmtree(T, ignore_errors=True)
except Exception as e:  # noqa: BLE001 — a crash is a failure, named
    import traceback
    traceback.print_exc()
    check(f"part one ran to its end ({type(e).__name__}: {e})", False)


# ---------------------------------------------------------------------------------------------- part two: a garden
T = tempfile.mkdtemp(prefix='dmcoremerge-g-')
G = os.path.join(T, 'g')


def run(*a, cwd=None):
    r = subprocess.run(list(a), capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=cwd or G)
    r.out = r.stdout + r.stderr
    return r


def write(rel, text):
    p = os.path.join(G, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)


def text(rel):
    with open(os.path.join(G, rel), encoding='utf-8') as fh:
        return fh.read()


def commit(what, body):
    """A save without the wait for the minute (bin/dmsave.py waits where a bean holds this minute's moment): the clock's
    heading written by bin/dmjournal.py, its moment in place of each `at: now`, and one commit, through the hook."""
    run(PY, 'bin/dmjournal.py', 'sam', what, '--body', body)
    m = [ln for ln in text('log/journal.md').split('\n') if ln.startswith('## ')][-1][3:].split(' · ', 1)[0]
    for f in os.listdir(os.path.join(G, 'beans')):
        t = text(f'beans/{f}')
        if 'at: now' in t:
            write(f'beans/{f}', t.replace('at: now', f'at: "{m}"'))
    run('git', 'add', '-A')
    return run('git', 'commit', '-q', '-m', what)


SAM = """---
bean: sam
kind: person
title: "Sam — keeps this garden"
summary: "The gardener."
statements:
  - say:    { by: sam, at: now }
  - own:    { by: theone, of: self }
  - answer: { by: self, of: self, as: law }
---
Sam keeps this ledger.
"""
POT = """---
bean: pot
kind: document
title: "The pot"
statements:
  - say: { by: sam, at: now }
  - pay: { id: paid, by: sam, of: { count: "10.00", unit: XTS }, at: 2026-09-20 }
---
What sam put in.
"""


def branch_and_merge(name, theirs, ours, merge=('merge', '--no-edit')):
    """`theirs` on a branch from here, `ours` on master, then the branch merged into master by git: (their commit, our
    commit, the merge)."""
    run('git', 'checkout', '-q', '-b', name)
    t = theirs()
    run('git', 'checkout', '-q', 'master')
    o = ours()
    return t, o, run('git', *merge, name)


try:
    r = run('sh', os.path.join(ROOT, 'seed', 'germinate.sh'), G, cwd=ROOT)
    check("a garden germinates through its gate", r.returncode == 0, r.out[-800:])
    run('git', 'config', 'user.name', 'sam')
    run('git', 'config', 'user.email', 'sam@example.invalid')
    hooks = os.path.join(G, '.git', 'hooks')
    driver = run('git', 'config', '--get', 'merge.daftar.driver').stdout
    attrs = run('git', 'check-attr', 'merge', '--', 'beans/x.md', 'mappings/x.md', 'log/journal.md', 'log/pending.md').stdout
    check("bin/install.py installs the gate at pre-commit and pre-merge-commit, and the driver `daftar` as bin/merge.py",
          all('bin/check.py' in open(os.path.join(hooks, h)).read() for h in ('pre-commit', 'pre-merge-commit'))
          and 'bin/merge.py" --file %O %A %B %P' in driver, driver)
    check("`.gitattributes` sends beans and mappings to the driver `daftar`, and the journal and the queue to git's union",
          attrs.count('merge: daftar') == 2 and attrs.count('merge: union') == 2, attrs)

    # WHILE IT PINS STD-VOCAB, THE GATE IS TODAY'S
    r = run(PY, 'bin/daftar.py', 'check')
    check("while the garden pins std-vocab, `daftar check` is today's gate (bin/dmcheck.py)",
          r.returncode == 0 and 'core check' not in r.out and 'docs, 0 error(s)' in r.out.strip().split('\n')[-1], r.out[-400:])
    r = run(PY, 'bin/check.py', '--merge-commit')
    check("...and a merge git commits itself is judged by nothing, as today's gate never judged one",
          r.returncode == 0 and not r.out.strip(), r.out)
    tw = os.path.join(T, 'today')
    os.makedirs(tw)
    for n, t in (('O', "---\nbean: box\ngenos: device\ntitle: Box\n---\nA box.\n"),
                 ('A', "---\nbean: box\ngenos: device\ntitle: Our box\n---\nA box.\n"),
                 ('B', "---\nbean: box\ngenos: device\ntitle: Box\n---\nA box, theirs.\n")):
        with open(os.path.join(tw, n), 'w', encoding='utf-8') as fh:
            fh.write(t)
    r = run(PY, 'bin/merge.py', '--file', *(os.path.join(tw, n) for n in 'OAB'), 'beans/box.md')
    check("...and the driver hands a bean in today's words to bin/dmmerge.py, today's merge", 'dmmerge' in r.out, r.out[-400:])

    # THE ADOPTION, JUDGED BY THE CORE
    write('GARDEN.md', re.sub(r'(?m)^extends: std-vocab@\S*', 'extends: core@1', text('GARDEN.md'), count=1)
          .replace('\ngardener:', '\ngardener: sam', 1))
    write('beans/sam.md', SAM)
    write('beans/pot.md', POT)
    r = run(PY, 'bin/dmsave.py', 'sam', 'RULE-CHANGE: the core adopted', '--body',
            '- action: RULE-CHANGE, GARDEN.md extends the core, sam keeps the garden: [[sam]] and [[pot]]; ratified by sam')
    check("the commit that moves the pin to the core is judged by the core's gate, through the same hook",
          r.returncode == 0 and 'core check --staged: 2 beans, 5 statements — 0 error(s)' in r.out, r.out[-800:])
    r = run(PY, 'bin/daftar.py', 'check')
    r2 = run(PY, 'bin/dmcheck.py', '--all')
    check("once it pins the core, `daftar check` is the core's gate, and bin/dmcheck.py hands the garden to it",
          r.returncode == 0 and 'core check: g: 2 beans' in r.out and 'core check: g: 2 beans' in r2.out, r.out + r2.out)
    r = run(PY, 'bin/check.py', 'beans/pot.md')
    check("...which judges a whole garden, and says so to a command that names one bean", r.returncode == 2
          and "the core's gate judges a whole garden" in r.out, r.out)
    r = run(PY, 'bin/daftar.py', 'help', 'merge')
    check("`daftar merge` is bin/merge.py, the verb's tool ported", r.returncode == 0 and 'bin/merge.py --file' in r.out, r.out[:300])

    # TWO BRANCHES CHANGE ONE BEAN, AND GIT MERGES THEM
    def theirs():
        write('beans/pot.md', text('beans/pot.md').replace('\n---\nWhat', '\n  - read: { by: sam, at: now }\n  - pay: { id: gift, by: sam, of: '
                                          '{ count: "2.00", unit: XTS } }\n---\nWhat').replace('put in.', 'put in, and gave.'))
        return commit('theirs: a gift', '- action: [[pot]] holds a gift')

    def ours():
        write('beans/pot.md', text('beans/pot.md').replace('\n---\nWhat', '\n  - make: { by: sam, of: [rent], at: now }\n  - pay: { id: rent, by: '
                                          'sam, of: { count: "5.00", unit: XTS } }\n---\nWhat').replace('"The pot"', '"The pot sam keeps"'))
        return commit('ours: rent', '- action: [[pot]] holds rent')
    t, o, m = branch_and_merge('gift', theirs, ours)
    pot = text('beans/pot.md')
    check("(the two branches each commit through the core's gate)", t.returncode == 0 and o.returncode == 0, t.out + o.out)
    check("git merges the bean by its statements: both sides' kept, theirs' act with no `of` given its `of`",
          'merge: pot —' in m.out and 'id: gift' in pot and 'id: rent' in pot and 'The pot sam keeps' in pot
          and 'and gave.' in pot and re.search(r'- read: \{by: sam, of: \[gift\], at: ', pot), m.out + pot)
    check("a merge git commits itself is refused by the gate (pre-merge-commit) until an entry of its own names the bean "
          "it merged", m.returncode != 0 and 'named by no entry of its own' in m.out
          and run('git', 'rev-parse', '-q', '--verify', 'MERGE_HEAD').returncode == 0, m.out[-800:])
    r = run(PY, 'bin/dmsave.py', 'sam', 'merged the gift', '--body', '- action: merged [[pot]]: the gift and the rent both stand')
    parents = run('git', 'log', '-1', '--format=%P').stdout.split()
    check("...and `git merge --no-commit` then bin/dmsave.py commits it, through the core's gate, with two parents",
          r.returncode == 0 and '— 0 error(s)' in r.out and len(parents) == 2, r.out[-800:])
    check("...its subject the merge's own entry, and not the other side's",
          run('git', 'log', '-1', '--format=%s').stdout.strip() == 'merged the gift', run('git', 'log', '-1', '--format=%s').stdout)

    # A BEAN ONLY THE OTHER SIDE CHANGED COMES AS IT WAS COMMITTED
    def theirs():
        write('beans/sam.md', SAM.replace('"The gardener."', '"The gardener, who keeps the pot."'))
        return commit('theirs: sam', '- action: [[sam]] keeps the pot')

    def ours():
        write('beans/pot.md', text('beans/pot.md').replace('"The pot sam keeps"', '"The pot"'))
        return commit('ours: the title', '- action: [[pot]] its title again')
    t, o, m = branch_and_merge('sam-only', theirs, ours)
    check("a merge that merged no bean both sides changed is committed by git itself, through the gate: what the other "
          "side committed comes as it was, judged then", t.returncode == 0 and o.returncode == 0 and m.returncode == 0
          and len(run('git', 'log', '-1', '--format=%P').stdout.split()) == 2, t.out + o.out + m.out)

    # A TRUE CONFLICT, SETTLED BY A PERSON
    def theirs():
        write('beans/pot.md', text('beans/pot.md').replace('title: "The pot"', 'title: "The shared pot"'))
        return commit('theirs: shared', '- action: [[pot]] is shared')

    def ours():
        write('beans/pot.md', text('beans/pot.md').replace('title: "The pot"', 'title: "The kept pot"'))
        return commit('ours: kept', '- action: [[pot]] is kept')
    t, o, m = branch_and_merge('title', theirs, ours)
    ours_text = run('git', 'show', 'HEAD:beans/pot.md').stdout
    check("a true conflict: the driver refuses, names it with both values, and git leaves the bean as ours, unmerged",
          m.returncode != 0 and 'title: ours The kept pot | theirs The shared pot' in m.out and text('beans/pot.md') == ours_text
          and 'beans/pot.md' in run('git', 'ls-files', '--unmerged').stdout, m.out[-800:])
    r = run(PY, 'bin/dmsave.py', 'sam', 'merged', '--body', '- action: merged [[pot]]')
    check("...nothing is saved while it stands unsettled", r.returncode != 0 and 'unmerged' in r.out, r.out[-400:])
    write('beans/pot.md', ours_text.replace('"The kept pot"', '"The shared pot, kept"'))
    run('git', 'add', 'beans/pot.md')
    r = commit('settled the title', '- action: [[pot]] settled by sam: the shared pot, kept (class J)')
    check("...a person writes the bean as it should stand, and the commit that settles it says so, through the gate",
          r.returncode == 0 and len(run('git', 'log', '-1', '--format=%P').stdout.split()) == 2, r.out[-800:])

    # TWO LAWS
    def theirs():
        write('beans/pot.md', "---\nbean: pot\ngenos: document\ntitle: The pot\n---\nIn today's words.\n")
        run('git', 'add', '-A')
        return run('git', 'commit', '-q', '--no-verify', '-m', "a branch in today's words")

    def ours():
        write('beans/pot.md', text('beans/pot.md').replace('kept"', 'kept by sam"'))
        return commit('ours: by sam', '- action: [[pot]] kept by sam')
    t, o, m = branch_and_merge('today', theirs, ours)
    check("sides written in two laws — statements, and today's words — are refused, ours left as it was",
          m.returncode != 0 and 'written in two laws' in m.out and 'kept by sam' in text('beans/pot.md'), m.out[-600:])
    run('git', 'merge', '--abort')

    # REMOVED ON ONE SIDE, CHANGED ON THE OTHER
    def theirs():
        os.remove(os.path.join(G, 'beans', 'pot.md'))
        return commit('theirs: no pot', '- action: [[pot]] taken out')

    def ours():
        write('beans/pot.md', text('beans/pot.md').replace('kept by sam"', 'kept by sam alone"'))
        return commit('ours: alone', '- action: [[pot]] kept by sam alone')
    t, o, m = branch_and_merge('gone', theirs, ours)
    check("a bean one side removed and the other changed is a true conflict, git's own",
          t.returncode == 0 and m.returncode != 0 and 'CONFLICT (modify/delete)' in m.out, t.out + m.out[-600:])
    run('git', 'merge', '--abort')
except Exception as e:  # noqa: BLE001
    import traceback
    traceback.print_exc()
    check(f"part two ran to its end ({type(e).__name__}: {e})", False)
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\ncore_merge: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
