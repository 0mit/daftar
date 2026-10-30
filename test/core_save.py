#!/usr/bin/env python3
"""The core's save: today's bin/save.py commits a garden written in statements, with the core's gate at the commit.

Grows a garden of the core's beans (bin/, core/ and the standards copied from this release), installs the core's
pre-commit gate (bin/install.py), and saves through bin/save.py, which journals, stamps, stages and commits in one
call. Checks that a knowing act's `at: now` is written as the moment of the heading the save wrote; that a moment typed
there is refused, and saved once it is `now`; that a bean the entry does not name is refused; that a statement added
under an old act is refused until an act of this commit knows it; that a change to the law is refused until an entry
says RULE-CHANGE; that the engine's own refusals stop the commit; that a heading typed into the journal by hand is
refused; that what is judged is the index, not the working tree; that a bean saved four times in a row is saved in
seconds, each act at its own moment, to the second, and one saved again in the second it was saved waits for the next;
and that the stamp's moment written finer or coarser than the clock wrote it is refused.
"""
import os, re, shutil, subprocess, sys, tempfile

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.append(os.path.join(ROOT, 'test'))   # last: test/core.py is no package `core`
import machine  # noqa: E402
machine.ensure()      # its time source and standards cache, not the machine's
from core import read  # noqa: E402

FAILS = []
PY = sys.executable


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:1200]))
    if not cond:
        FAILS.append(name)


T = tempfile.mkdtemp(prefix='dmcoresave-')
G = os.path.join(T, 'g')


def run(*a, stdin=None):
    return subprocess.run(list(a), capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=G, input=stdin)


def git(*a):
    return run('git', *a)


def write(rel, head, body='\nWords.\n'):
    p = os.path.join(G, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as fh:
        fh.write('---\n' + yaml.safe_dump(head, allow_unicode=True, sort_keys=False, width=200) + '---\n' + body)


def text(rel):
    with open(os.path.join(G, rel), encoding='utf-8') as fh:
        return fh.read()


BEN_AGREES = {'agree': {'by': 'ben', 'of': 'to be kept in this garden by name', 'through': 'spoken'}}   # his word (consent)


def bean(bid, kind, statements):
    write(f"beans/{bid}.md", {'bean': bid, 'kind': kind, 'title': bid, 'statements': statements})


def save(who, what, body):
    r = run(PY, 'bin/save.py', who, what, '--body', body)
    r.out = r.stdout + r.stderr          # git hands a hook's output to stderr
    return r


def head_bean(bid):
    show = git('show', f"HEAD:beans/{bid}.md").stdout
    return read.loads(show.split('---\n')[1]) if show.startswith('---') else {}


def last_heading():
    return [l for l in text('log/journal.md').split('\n') if l.startswith('## ')][-1]


def reset():
    git('reset', '-q', '--hard', 'HEAD')
    git('clean', '-qfd')


try:
    os.makedirs(G)
    git('init', '-q')
    git('config', 'user.name', 'sam')
    git('config', 'user.email', 'sam@example.invalid')
    ignore = shutil.ignore_patterns('__pycache__')
    shutil.copytree(os.path.join(ROOT, 'bin'), os.path.join(G, 'bin'), ignore=ignore)
    shutil.copytree(os.path.join(ROOT, 'core'), os.path.join(G, 'core'), ignore=ignore)
    os.makedirs(os.path.join(G, 'seed'))
    for f in ('LANGUAGE',):
        shutil.copy(os.path.join(ROOT, 'seed', f), os.path.join(G, 'seed', f))
    shutil.copytree(os.path.join(ROOT, 'seed', 'knowledge'), os.path.join(G, 'seed', 'knowledge'))
    CASES = read.data(os.path.join(ROOT, 'test', 'core-cases.yaml'))
    write('GARDEN.md', {'garden': 'core-save', 'extends': 'core@' + str(read.data(os.path.join(ROOT, 'core', 'law', 'core.yaml'))['version']), 'gardener': 'sam',
                         'zone': 'Asia/Tehran'}, '')
    vocab = {k: [dict(r, vacant=r.get('vacant') or "the cases' row, beside this suite's own garden")
                 if k in ('kinds', 'levels', 'namespaces', 'verbs', 'units') and isinstance(r, dict) else r
                 for r in v] if isinstance(v, list) else v for k, v in CASES['vocab'].items()}
    write('VOCAB.md', vocab, '')
    os.makedirs(os.path.join(G, 'log'))
    with open(os.path.join(G, 'log', 'journal.md'), 'w', encoding='utf-8') as fh:
        fh.write('# Journal\n')
    git('add', '-A')
    git('commit', '-q', '--no-verify', '-m', 'the garden, before its first bean')
    r = run(PY, 'bin/install.py')
    check("bin/install.py installs the core's gate as this clone's pre-commit",
          r.returncode == 0 and 'bin/check.py" --staged' in open(os.path.join(G, '.git', 'hooks', 'pre-commit')).read(),
          r.stdout + r.stderr)

    # A FIRST BEAN: `at: now` becomes the moment of the heading the save wrote
    bean('sam', 'person', [{'say': {'by': 'sam', 'at': 'now'}}, {'own': {'by': 'theone', 'of': 'self'}}])
    r = save('sam', "sam's own record", '- action: wrote [[sam]], the gardener')
    h = last_heading()
    moment = h[3:].split(' · ', 1)[0]
    at = (head_bean('sam').get('statements') or [{}])[0].get('say', {}).get('at')
    check(f"a save commits a bean of statements, its `at: now` written as the heading's moment ({moment})",
          r.returncode == 0 and at == moment, (r.returncode, at, moment, r.stdout + r.stderr))

    # THE CLOCK (the method `stamp`): one that cannot be shown within half a minute of its sources stamps nothing
    import socket
    head0, journal0 = git('rev-parse', 'HEAD').stdout, text('log/journal.md')
    bean('cem', 'document', [{'say': {'by': 'sam', 'at': 'now'}}])
    for label, src in (("60 s behind its source", machine.time_source(60)), ("45 s ahead of it", machine.time_source(-45)),
                       ("whose source does not answer", machine.time_source(0, answer=False))):
        r = subprocess.run([PY, 'bin/save.py', 'sam', 'a note', '--body', '- action: wrote [[cem]]'], cwd=G,
                           capture_output=True, text=True, encoding='utf-8', errors='replace',
                           env=dict(os.environ, DAFTAR_TIME_SOURCES=src))
        out = r.stdout + r.stderr
        check(f"a save on a clock {label} is refused before anything is written, naming this machine, its keeper "
              f"and what sets it right",
              r.returncode == 2 and 'NOT STAMPED' in out and socket.gethostname() in out
              and 'sam keeps this machine' in out and 'bin/clock.py' in out
              and git('rev-parse', 'HEAD').stdout == head0 and text('log/journal.md') == journal0, out[-900:])
    r = subprocess.run([PY, 'bin/clock.py'], cwd=G, capture_output=True, text=True, encoding='utf-8', errors='replace',
                       env=dict(os.environ, DAFTAR_TIME_SOURCES=machine.time_source(60)))
    check("bin/clock.py says what its source shows — beyond — and exits 1", r.returncode == 1 and 'beyond' in r.stdout
          and '60.0' in r.stdout and 'may NOT stamp' in r.stdout, r.stdout + r.stderr)
    r = save('sam', 'a note', '- action: wrote [[cem]]')
    check("...and on a clock its source shows within, the same save is saved", r.returncode == 0, r.out[-600:])

    # A MOMENT TYPED IS REFUSED, AND SAVED ONCE IT IS `now`
    bean('ben', 'person', [{'say': {'by': 'ben', 'at': '2026-10-01 10:00+03:30'}}, {'own': {'by': 'theone', 'of': 'self'}}, BEN_AGREES])
    r = save('sam', "ben's record", '- action: wrote [[ben]]')
    check("a knowing act's moment typed by hand is refused: the moment is the save's",
          r.returncode == 1 and 'knowing' in r.out and 'is no moment' in r.out, r.stdout + r.stderr)
    bean('ben', 'person', [{'say': {'by': 'ben', 'at': 'now'}}, {'own': {'by': 'theone', 'of': 'self'}}, BEN_AGREES])
    r = run(PY, 'bin/save.py', '--again')
    at = (head_bean('ben').get('statements') or [{}])[0].get('say', {}).get('at')
    check("...and once it says `now`, --again saves it at the waiting entry's moment",
          r.returncode == 0 and at == last_heading()[3:].split(' · ', 1)[0], (r.returncode, at, r.stdout + r.stderr))

    # A MOMENT HISTORY HOLDS IS STILL NOT THIS COMMIT'S: only the adoption carries history's moments
    past = git('log', '-1', '--format=%cI', 'HEAD').stdout.strip()      # a commit's own moment, which history holds
    bean('cy', 'person', [{'say': {'by': 'cy', 'at': past}}, {'own': {'by': 'theone', 'of': 'self'}}])
    r = save('sam', "cy's record", '- action: wrote [[cy]]')
    check(f"a knowing act given a moment history holds (the last commit's, {past}) is refused outside the adoption",
          r.returncode == 1 and 'Only the commit that adopts the core' in r.out, r.out)
    reset()

    # A BEAN NO ENTRY NAMES
    bean('ada', 'person', [{'say': {'by': 'ada', 'at': 'now'}}, {'own': {'by': 'theone', 'of': 'self'}}])
    r = save('sam', 'a record', '- action: wrote a record')
    check("a bean the entry does not name is refused", r.returncode == 1 and 'named by no journal entry' in r.out,
          r.stdout + r.stderr)
    reset()

    # A STATEMENT ADDED UNDER AN OLD ACT
    bean('sam', 'person', [{'say': {'by': 'sam', 'at': moment}}, {'own': {'by': 'theone', 'of': 'self'}},
                           {'do': {'by': 'self', 'as': 'workstation'}}])
    r = save('sam', 'what sam does', '- action: [[sam]] does a job')
    check("a statement added under an old act is refused: its act's moment is older than it",
          r.returncode == 1 and 'known by no act it adds' in r.out, r.stdout + r.stderr)
    bean('sam', 'person', [{'say': {'by': 'sam', 'at': moment}}, {'own': {'by': 'theone', 'of': 'self'}},
                           {'say': {'by': 'sam', 'of': ['job'], 'at': 'now'}}, {'do': {'id': 'job', 'by': 'self', 'as': 'workstation'}}])
    r = run(PY, 'bin/save.py', '--again')
    check("...and saved once an act of this commit knows it", r.returncode == 0, r.stdout + r.stderr)

    # THE LAW: a RULE-CHANGE
    with open(os.path.join(G, 'VOCAB.md'), encoding='utf-8') as fh:
        v = fh.read()
    with open(os.path.join(G, 'VOCAB.md'), 'w', encoding='utf-8') as fh:
        fh.write(v.replace('kinds:\n', 'kinds:\n- {kind: boat, nature: body, organisation: device, vacant: "no boat is recorded yet"}\n', 1))
    r = save('sam', 'a boat is a kind', '- action: the kind boat, for the garden')
    check("a change to the law with no RULE-CHANGE said is refused by `ratify`",
          r.returncode == 1 and 'ratify' in r.out, r.stdout + r.stderr)
    r = run(PY, 'bin/journal.py', 'sam', 'RULE-CHANGE ratified', '--body', '- action: RULE-CHANGE, the kind boat; ratified by sam')
    r = run(PY, 'bin/save.py', '--again')
    check("...and saved once an entry says RULE-CHANGE", r.returncode == 0, r.stdout + r.stderr)

    # THE ENGINE'S OWN REFUSALS STOP THE COMMIT
    bean('x', 'document', [{'say': {'by': 'sam', 'at': 'now'}}, {'pay': {'by': 'nobody', 'of': {'count': '1', 'unit': 'XTS'}}}])
    r = save('sam', 'a payment', '- action: [[x]] records a payment')
    check("a bean the engine refuses (a being that is no bean) is not committed",
          r.returncode == 1 and 'valency' in r.out and "'nobody' is no bean" in r.out, r.stdout + r.stderr)
    reset()

    # A HEADING TYPED BY HAND
    with open(os.path.join(G, 'log', 'journal.md'), 'a', encoding='utf-8') as fh:
        fh.write('\n## 2026-10-01 10:00+03:30 · sam · typed\n- action: a heading typed by hand\n')
    git('add', '-A')
    r = git('commit', '-q', '-m', 'typed')
    check("a heading typed into the journal by hand is refused: the clock writes it",
          r.returncode != 0 and 'not written by the clock' in r.stdout + r.stderr, r.stdout + r.stderr)
    reset()

    # WHAT TODAY'S GATE HELD AT THE COMMIT, NOW THE CORE'S (v1): `kept`, `harm`, `consent`, and `form` on disk. Each case
    # is written, journalled by the clock (bin/journal.py), staged, and judged as the commit would be; then undone.
    def staged_case(files, entry, setup=None):
        if setup:
            for rel, text in setup.items():
                os.makedirs(os.path.dirname(os.path.join(G, rel)) or G, exist_ok=True)
                with open(os.path.join(G, rel), 'w', encoding='utf-8', newline='') as fh:
                    fh.write(text)
            git('add', '-A')
            git('commit', '-q', '--no-verify', '-m', 'the case, before it')
        for rel, text in files.items():
            os.makedirs(os.path.dirname(os.path.join(G, rel)) or G, exist_ok=True)
            if text is None:
                os.remove(os.path.join(G, rel))
                continue
            with open(os.path.join(G, rel), 'w', encoding='utf-8', newline='') as fh:
                fh.write(text)
        run(PY, 'bin/journal.py', 'sam', 'a case', '--body', entry)
        git('add', '-A')
        r = run(PY, 'core/check.py', '--staged')
        reset()
        if setup:
            git('reset', '-q', '--hard', 'HEAD~1')
        return r.stdout + r.stderr

    def doc(bid, kind, statements, body='\nWords.\n', title=None):
        return '---\n' + yaml.safe_dump({'bean': bid, 'kind': kind, 'title': title or bid, 'statements': statements},
                                        allow_unicode=True, sort_keys=False, width=200) + '---\n' + body

    say = {'say': {'by': 'sam', 'at': 'now'}}
    out = staged_case({'notes.txt': 'kept here\n-----BEGIN ' + 'OPENSSH PRIVATE KEY-----\nb3BlbnNzaA==\n'}, '- action: a note')
    check("harm: a private-key block in any file a commit stages is refused, the whole file read",
          'harm' in out and 'private-key block' in out, out)
    out = staged_case({'beans/k1.md': doc('k1', 'document', [say], body='')}, '- action: [[k1]]')
    check("kept: a bean with no body is refused — a bean reads on paper", 'kept' in out and 'no body' in out, out)
    out = staged_case({'beans/k2.md': doc('k2', 'document', [say, {'do': {'by': 'sam', 'as': 'workstation'}}])},
                      '- action: [[k2]] tidied', setup={'beans/k2.md': doc('k2', 'document', [
                          {'say': {'by': 'sam', 'at': '2026-10-01 10:00+03:30'}},
                          {'do': {'id': 'job', 'by': 'sam', 'as': 'workstation'}},
                          {'do': {'by': 'sam', 'as': 'web'}}])})
    check("kept: a statement taken out of a bean, its id named nowhere in the entry, is refused",
          "the statement `job` is taken out" in out, out)
    j = open(os.path.join(G, 'log', 'journal.md'), encoding='utf-8').read()
    out = staged_case({'log/journal.md': j.replace('# Journal', '# The Journal', 1)}, '- action: the title')
    check("kept: a line the journal held, rewritten, is refused: a journal is appended", 'kept' in out and
          'never rewritten' in out, out)
    out = staged_case({'log/journal.md': j + '- action: a line\x0bwith a vertical tab\n- detail: (fill in what was done)\n'},
                      '- action: written by hand above, not by the clock')
    check("kept: a line the commit adds to the journal holding a character some reader takes for a line break, or a "
          "template's `(fill in`, is refused", 'some readers take' in out and '(fill in' in out, out)
    out = staged_case({'series/rain/sept/0001.tsv': 'rain\n1\n'}, '- action: the part again',
                      setup={'series/rain/sept/0001.tsv': 'rain\n0\n'})
    check("kept: a series' part, once written, is refused changed", "series' part" in out, out)
    out = staged_case({'beans/h1.md': doc('h1', 'document', [say, {'measure': {
        'id': 'w', 'held': 'root:vault/0123456789abcdef0123456789abcdef'}}])}, '- action: [[h1]]')
    check("harm: a statement sealed in a commit whose entry has no `- held: <bean> <id> added` line is refused",
          '- held: h1 w added' in out, out)
    vt = open(os.path.join(G, 'VOCAB.md'), encoding='utf-8').read().replace(
        '\n---', '\nregistry_additions:\n  knowledge_schemes:\n  - { scheme: ailments, classifies: "what ails a person", '
        'holding: extract, sensitive: special-category, publisher: sam, url: "extracts/ailments.tsv", levels: [ { level: '
        'ailment } ], neighbours: none, sources: extracts/ailments.tsv }\nregistry_files:\n- { registry: ailments, file: '
        'extracts/ailments.tsv, key: code }\n---', 1)
    out = staged_case({'VOCAB.md': vt, 'extracts/ailments.tsv': 'code\tparent\tname\nasthma\t\tasthma\n',
                       'beans/h2.md': doc('h2', 'document', [say, {'classify': {'of': 'ben', 'as': 'ailments:asthma'}}])},
                      '- action: RULE-CHANGE, a scheme of the garden; [[h2]]')
    check("harm: a code of a scheme the garden marks special-category, written unsealed, is refused",
          'special-category' in out and 'harm' in out, out)
    out = staged_case({'beans/e1.md': doc('e1', 'event', [say, {'be': {'by': 'self', 'at': '2099-06-01 18:00+03:30/2099-06-01 22:00+03:30'}},
                                                           {'be': {'by': 'self', 'at': '192.0.2.40', 'as': 'location'}},
                                                           {'attend': {'by': 'ben', 'of': 'self'}}])}, '- action: [[e1]]')
    check("consent: a commit placing a person who is not the gardener somewhere in the future, in git, is refused",
          'consent' in out and 'in the future' in out, out)
    out = staged_case({'beans/t1.md': doc('t1', 'document', [say], title='a \x1b[2Jtitle')}, '- action: [[t1]]')
    check("form: text holding a control character is refused, the character named and never echoed",
          'U+001B' in out and '\x1b' not in out, out)

    # THE INDEX IS JUDGED, NOT THE WORKING TREE
    bean('ben', 'person', [{'say': {'by': 'ben', 'at': 'now'}}, {'own': {'by': 'theone', 'of': 'self'}}, BEN_AGREES,
                           {'pay': {'by': 'ghost', 'of': '1'}}])
    git('add', 'beans/ben.md')
    bean('ben', 'person', [{'say': {'by': 'ben', 'at': 'now'}}, {'own': {'by': 'theone', 'of': 'self'}}, BEN_AGREES])
    r = run(PY, 'core/check.py', '--staged')
    check("core/check.py --staged judges what is staged, not what the working tree holds",
          r.returncode == 1 and "'ghost' is no bean" in r.stdout, r.stdout)
    reset()
    r = run(PY, 'core/check.py')
    check("the garden as saved passes the core's check", r.returncode == 0, r.stdout)

    # THE PIN IS READ AS THE GATE READS IT (bin/check.py `pin`), quoted as YAML may write it
    g = text('GARDEN.md')
    pinned = re.search(r'(?m)^extends: (core@\S+)$', g).group(1)
    with open(os.path.join(G, 'GARDEN.md'), 'w', encoding='utf-8') as fh:
        fh.write(g.replace(f'extends: {pinned}\n', f'extends: "{pinned}"\n', 1))
    r = save('sam', 'RULE-CHANGE: the pin quoted', '- action: RULE-CHANGE, GARDEN.md writes its pin quoted; ratified by sam')
    check(f'a pin written quoted (`extends: "{pinned}"`) is the same pin: the gate saves it', r.returncode == 0, r.out[-600:])

    # A BEAN SAVED AGAIN IN THE MINUTE IT WAS SAVED (the method `stamp`: the clock's reading, to the second). Its act that
    # knows what no other act knows, said `now` each time, would hold the moment the last commit gave it already were the
    # moment the minute's — an act no commit adds — and a save waited for the minute to turn. To the second, four saves of
    # one bean in a row are four acts at four moments, saved in seconds, not minutes.
    import time

    def sam_now(job, does):
        st = read.loads(git('show', 'HEAD:beans/sam.md').stdout.split('---\n')[1])['statements']
        st[0] = {'say': {'by': 'sam', 'at': 'now'}}                  # the act that knows what no other act knows
        bean('sam', 'person', st + [{'do': {'id': job, 'by': 'self', 'as': does}}])
    t0, outs, heads, ats = time.time(), [], [], []
    for job, does in (('desk', 'web'), ('lab', 'app-host'), ('shed', 'workstation'), ('loft', 'web')):
        sam_now(job, does)
        r = save('sam', f'a {job}', f'- action: [[sam]] keeps a {job}')
        outs.append(r)
        heads.append(last_heading()[3:].split(' · ', 1)[0])
        ats.append((head_bean('sam').get('statements') or [{}])[0].get('say', {}).get('at'))
    took = time.time() - t0
    check(f"a bean saved four times in a row, its act re-said `now` each time, is saved four times in "
          f"{took:.0f} s, not minutes: each act at its own heading's moment, to the second ({', '.join(heads)})",
          all(r.returncode == 0 for r in outs) and took < 30 and len(set(heads)) == 4 and ats == heads
          and all(re.fullmatch(r'\d{4}-\d\d-\d\d \d\d:\d\d:\d\d[+-]\d\d:\d\d', h) for h in heads)
          and not any('waiting for the next minute' in r.out for r in outs),
          (took, heads, ats, [r.out[-300:] for r in outs]))

    # ...AND TWO IN ONE SECOND STILL WAIT, FOR THE SECOND: a save of a bean the last commit holds at this second's moment
    # waits for the next, the pin read quoted as the gate reads it — the clock held at that second for a few readings
    sam_now('attic', 'web')
    r = run(PY, '-c', "import datetime, sys\nsys.path.insert(0, 'bin')\nimport save\n"
                      "h = [l for l in open('log/journal.md', encoding='utf-8').read().split('\\n') if l.startswith('## ')][-1]\n"
                      "held = datetime.datetime.fromisoformat(h[3:].split(' · ', 1)[0])\nn = []\n"
                      "class Clock(datetime.datetime):\n"
                      "    @classmethod\n"
                      "    def now(cls, tz=None):\n"
                      "        n.append(1)\n"
                      "        return held if len(n) < 6 else held + datetime.timedelta(seconds=1)\n"
                      "save.datetime = type('clock', (), {'datetime': Clock})\nsave.the_second_turns()\n"
                      "print('read', len(n))\n")
    check("...and a bean saved again in the second it was saved waits for the next second, and says so",
          r.returncode == 0 and 'was saved in this second already' in r.stderr and 'beans/sam.md' in r.stderr
          and re.search(r'read ([6-9]|\d\d)', r.stdout) is not None, r.stdout + r.stderr)
    git('checkout', '-q', '--', 'beans/sam.md')

    # A FALSE PRECISION, AND A COARSE ONE: the moment the clock wrote for this entry, written finer than it was read (a
    # millisecond the clock never gave) or coarser (its minute alone), is no moment the entry was written at
    bean('memo', 'document', [{'say': {'by': 'sam', 'at': 'now'}}])
    run(PY, 'bin/journal.py', 'sam', 'a memo', '--body', '- action: wrote [[memo]]')
    m = last_heading()[3:].split(' · ', 1)[0]
    clock = re.match(r'^(.* \d\d:\d\d)(:\d\d)?([+-]\d\d:\d\d|Z)$', m)
    finer = clock.group(1) + (clock.group(2) or ':00') + '.000' + clock.group(3)
    coarser = clock.group(1) + clock.group(3)
    said = []
    for written in (finer, coarser):
        if written == m:
            continue
        bean('memo', 'document', [{'say': {'by': 'sam', 'at': written}}])
        git('add', '-A')
        r = git('commit', '-q', '-m', 'a memo')
        said.append((written, r.returncode, r.stdout + r.stderr))
    check(f"the stamp's own moment written finer ({finer}) or coarser ({coarser}) than the clock wrote it ({m}) is "
          f"refused: a knowing act's moment is the entry's, as stamped",
          len(said) == 2 and all(rc != 0 and 'is no moment this commit' in out and '— 1 error(s)' in out
                                 for _w, rc, out in said), said)
    bean('memo', 'document', [{'say': {'by': 'sam', 'at': 'now'}}])
    r = run(PY, 'bin/save.py', '--again')
    check("...and saved once it says `now`", r.returncode == 0
          and (head_bean('memo').get('statements') or [{}])[0].get('say', {}).get('at') == m, r.stdout + r.stderr)

    # A MOVE'S REWRITES KNOWN (T1 of the second build run): the release's translator rewrites a bean at a move between
    # two releases of the core, and the gate judges that commit as any commit's — refused until an act of it knows the
    # rewrite and its entry names what was taken out; bin/dmupgrade.py `known_rewrites` writes both
    reset()
    bean('note', 'document', [{'say': {'by': 'sam', 'at': 'now'}}, {'about': {'of': ['memo']}}])
    r = save('sam', 'a note of the memo', '- action: wrote [[note]], about the memo')
    said = head_bean('note')['statements'][0]
    rewrite = lambda: bean('note', 'document', [said, {'concern': {'of': ['sam']}}])
    act = ("- action: RULE-CHANGE: the release's translator rewrote 1 bean(s) for the later core (core/translate.py "
           "`between`): beans/note.md.")
    rewrite()
    r = save('sam', 'the note rewritten by a move', act)
    check("a move's rewrite with no act that knows it, and its taken-out verb unnamed, is refused (rules knowing, kept)",
          r.returncode == 1 and 'knowing' in r.out and 'about' in r.out, r.out[-900:])
    reset()
    rewrite()
    k = run(PY, '-c', "import sys; sys.path.insert(0, 'bin'); import dmupgrade as d; "
                      "print(d.known_rewrites('.', ['beans/note.md'], 'sam', 'v9.9.9'))")
    line = k.stdout.strip()
    sts = read.loads(text('beans/note.md').split('---\n')[1])['statements']
    check("known_rewrites adds one `make` by the gardener at `now`, with no `of`, and returns the entry's line naming "
          "what was taken out", k.returncode == 0 and len(sts) == 3 and sts[:2] == [said, {'concern': {'of': ['sam']}}]
          and sts[2]['make'].get('by') == 'sam' and sts[2]['make'].get('at') == 'now' and 'of' not in sts[2]['make']
          and line.startswith('- translated:') and 'verb `about`' in line and 'note' in line, (k.stdout + k.stderr)[-900:])
    r = run(PY, 'bin/save.py', 'sam', 'the note rewritten by a move', '--body', act, line)
    r.out = r.stdout + r.stderr
    m = last_heading()[3:].split(' · ', 1)[0]
    check("...and the move's commit, with them, passes the gate, the act stamped at the entry's moment",
          r.returncode == 0 and (head_bean('note').get('statements') or [{}, {}, {}])[2].get('make', {}).get('at') == m,
          r.out[-900:])
    k = run(PY, '-c', "import sys; sys.path.insert(0, 'bin'); import dmupgrade as d; "
                      "print(repr(d.known_rewrites('.', [], 'sam', 'v9.9.9')))")
    check("...and a move that rewrote nothing adds no line", k.stdout.strip() == "''", k.stdout + k.stderr)
    vocab = text('VOCAB.md')
    k = run(PY, '-c', "import sys; sys.path.insert(0, 'bin'); import dmupgrade as d; "
                      "print(repr(d.known_rewrites('.', ['VOCAB.md'], 'sam', 'v9.9.9')))")
    check("...and VOCAB.md rewritten (the step of core 4.7 takes a garden's own row of a kind the law holds) is no bean: "
          "it is left as the translator wrote it, and adds no line", k.returncode == 0 and k.stdout.strip() == "''"
          and text('VOCAB.md') == vocab, k.stdout + k.stderr)
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\ncore_save: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
