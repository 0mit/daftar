#!/usr/bin/env python3
"""The write tools in a garden of the core (v1 part 5): save, safe, journal, session, cursor, digest, reform, install,
and the upgrade from one release of the core to another, each run as a garden of statements runs it.

Builds what it needs, as test/core_adopt.py does: a release of the core made from this tree (v1.0.0, its
seed/GARDEN.md.template pinning `core@`), and later releases of it — one with a file changed (v1.0.1), one whose core is
a later version (v1.1.0), one whose core refuses the garden (v1.2.0), one whose core is older (v1.3.0) — and a GARDEN
grown from v1.0.0, with its gardener, a laptop and a codebase, saved through the core's gate.

install: the clone's hooks take the law by the pin, and the statement merge is git's driver. save and journal: `at: now`
is written as the heading's moment, in a statement and in `details`, and today's `as_of: now` is not (the core has no
such word); `bin/save.py` and `daftar save` are the same tool. safe: statements counted, added, replaced and removed by
verb and id, each refused where the count is not the one stated; an edit that loses a statement unsaid is refused; one
taken out is named by the entry, or the gate refuses it. session: opened in statements, its first save stamped, closed
with its presence written and merged back through the save, the core's gate passing at every commit. cursor: a file
resolved to the bean whose location holds it, the bean's figures paired as the square pairs them, and what it inherits
along the order's chains. digest: the garden's machines by their beans and their names. reform: a bean in today's words
written in statements in place, its acts made now, a name the law lacks refused. upgrade: to a later release of the
core, the pin moved and the entry a RULE-CHANGE, a refused one put back, an older core refused.

Run: python3 test/core_write.py   (0 = green; about two minutes, since a bean saved twice in one minute waits for the next)
"""
import os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'bin'))
from core import read  # noqa: E402
import grow  # noqa: E402 — a release of the core, and the release in today's words
import importlib
import parse as dmparse
dmpass = importlib.import_module('pass')  # noqa: E402

FAILS = []
PY = sys.executable
VERSION = str(read.data(os.path.join(ROOT, 'core', 'law', 'core.yaml'))['version'])


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:1500]))
    if not cond:
        FAILS.append(name)


class R:
    def __init__(self, p):
        self.returncode, self.out = p.returncode, p.stdout + p.stderr


def run(*a, cwd=None, stdin=None):
    e = dict(os.environ, GIT_AUTHOR_NAME='sam', GIT_AUTHOR_EMAIL='sam@x', GIT_COMMITTER_NAME='sam',
             GIT_COMMITTER_EMAIL='sam@x')
    return R(subprocess.run(a, capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=cwd or G, env=e,
                            input=stdin))


def text(path, root=None):
    with open(os.path.join(root or G, path), encoding='utf-8') as fh:
        return fh.read()


def write(path, t, root=None):
    p = os.path.join(root or G, path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(t)


def bean(path):
    return read.document(os.path.join(G, path))[0]


def statements(path):
    return [next(iter(s.items())) for s in bean(path).get('statements') or []]


def clean():
    return run('git', 'status', '--porcelain').out.strip() == ''


def head():
    return run('git', 'rev-parse', 'HEAD').out.strip()


def last_heading():
    return [ln for ln in text('log/journal.md').split('\n') if ln.startswith('## ')][-1]


def moment():
    return last_heading()[3:].split(' · ', 1)[0]


def save(what, body, *who):
    return run(PY, 'bin/save.py', *(who or ('sam',)), what, '--body', body)


T = tempfile.mkdtemp(prefix='core-write-')
REL, G = os.path.join(T, 'release'), os.path.join(T, 'garden')

LAPTOP = """---
bean: laptop
kind: host
title: "laptop — Sam's ThinkPad"
statements:
  - say: { by: sam, at: now }
  - own: { id: own, by: sam, of: self }
  - name: { id: hostname, by: dns, of: self, as: laptop.example.org }
  - can: { id: sends-mail, by: self, of: smtp }
  - forbidden: { of: sends-mail, through: sam, why: "the provider blocks port 25" }
  - possible: { of: sends-mail }
details:
  safety:
    - "unplug before opening"
---
The laptop.
"""

APP = """---
bean: app
kind: codebase
title: "app — the shop's code"
statements:
  - say: { by: sam, at: now }
  - own: { id: own, by: sam, of: self }
  - be: { id: tree, by: self, at: "unix-filesystem:%s", as: location }
  - be: { id: runs-on, by: self, at: laptop, as: habitat }
  - need: { id: needs-db, by: self, of: [laptop] }
  - impossible: { of: needs-db, why: "the laptop holds no database server" }
details:
  located_at:
    tree: { role: own-source, scan_policy: index }
  moves:
    - { to: laptop, at: now }
  provenance: { as_of: now }
---
The shop's code.
"""

OLD = """---
bean: printer
genos: host
title: "printer — the office printer"
status: active
summary: "The office printer."
nature: soma
provenance: { src: observed, by: "sam", as_of: 2026-09-01 }
owned_by: { owner: { bean: sam } }
---
The printer.
"""

try:
    # ---- THE RELEASES: v1.0.0, a release of the core made from this tree, and four after it
    law = dmparse.loads(dmparse.split_front_matter(text('seed/std-vocab.md', ROOT))[0])
    os.makedirs(REL)
    for f in dmpass.kept([f for f in dmpass.tracked(ROOT) if os.path.isfile(os.path.join(ROOT, f))],
                         dmpass.language(text('seed/LANGUAGE', ROOT)), dmpass.offered(law)):
        os.makedirs(os.path.join(REL, os.path.dirname(f)), exist_ok=True)
        shutil.copy2(os.path.join(ROOT, f), os.path.join(REL, f))
    for f in ('GARDEN.md.template', 'VOCAB.md.template'):
        shutil.copy2(os.path.join(ROOT, 'core', 'guide', f), os.path.join(REL, 'seed', f))

    def tag(t, msg):
        run('git', 'add', '-A', cwd=REL)
        run('git', 'commit', '-qm', msg, cwd=REL)
        run('git', 'tag', t, cwd=REL)

    def core_yaml(version, drop=None):
        y = re.sub(r'(?m)^version: "[^"]*"', f'version: "{version}"', text('core/law/core.yaml', ROOT), count=1)
        write('core/law/core.yaml', y, REL)
        k = text('core/law/kinds.yaml', ROOT)
        write('core/law/kinds.yaml', re.sub(rf'(?m)^  - {{ kind: {drop},[^\n]*\n', '', k) if drop else k, REL)
    run('git', 'init', '-q', cwd=REL)
    tag('v1.0.0', 'the core')
    write('seed/README.md', text('seed/README.md', REL) + '\nA line v1.0.1 adds.\n', REL)
    tag('v1.0.1', 'a file changed')
    core_yaml(f"{VERSION.split('.')[0]}.{int(VERSION.split('.')[1]) + 1}")
    tag('v1.1.0', 'a later core')
    core_yaml(f"{VERSION.split('.')[0]}.{int(VERSION.split('.')[1]) + 2}", drop='host')
    tag('v1.2.0', 'a core that has no hosts')
    core_yaml('0.9')
    tag('v1.3.0', 'an older core')
    run('git', 'checkout', '-q', 'v1.0.0', cwd=REL)

    # ---- THE GARDEN, grown from v1.0.0
    r = run(PY, os.path.join(REL, 'seed', 'germinate.py'), G, '--gardener', 'sam', '--gardener-name', 'Sam', cwd=T)
    check(f"a garden grows from v1.0.0 in the core (core@{VERSION})",
          r.returncode == 0 and f'core@{VERSION}' in text('GARDEN.md'), r.out[-800:])

    # ---- INSTALL: one installer, the hooks taking the law by the pin, the statement merge as git's driver
    r = run(PY, 'bin/install.py')
    hook = text('.git/hooks/pre-commit')
    check("install: bin/install.py installs the hooks that take the law by the pin, and the statement merge",
          r.returncode == 0 and 'bin/check.py' in hook and 'bin/check.py' in text('.git/hooks/pre-merge-commit')
          and 'bin/merge.py' in run('git', 'config', '--get', 'merge.daftar.driver').out, r.out + hook[-300:])

    # ---- SAVE AND JOURNAL: the moment at `at`, in a statement and in details; today's `as_of: now` is not the core's
    write('beans/laptop.md', LAPTOP)
    write('beans/app.md', APP % os.path.join(T, 'src', 'app'))
    r = save('the laptop and the app', '- action: wrote [[laptop]] and [[app]]')
    m = moment()
    app = bean('beans/app.md')
    check(f"save: `at: now` is written as the heading's moment ({m}), in a statement and in what `details` keeps",
          r.returncode == 0 and statements('beans/laptop.md')[0][1].get('at') == m
          and app['details']['moves'][0]['at'] == m, r.out[-1200:])
    check("journal: in a garden of the core, today's `as_of: now` is not stamped — the core's `now` fills `at` alone",
          app['details']['provenance']['as_of'] == 'now', app['details'])
    write('beans/laptop.md', text('beans/laptop.md').replace('The laptop.', 'The laptop, on the desk.'))
    r = run(PY, 'bin/save.py', 'sam', 'the laptop on the desk', '--body', '- action: [[laptop]] is on the desk')
    check("save: today's name, bin/save.py, runs the same tool", r.returncode == 0 and clean(), r.out[-600:])
    write('beans/laptop.md', text('beans/laptop.md').replace('on the desk.', 'on the desk, by the window.'))
    r = run(PY, 'bin/daftar.py', 'save', 'sam', 'the laptop by the window', '--body', '- action: [[laptop]] by the window')
    check("save: `daftar save` runs it too", r.returncode == 0 and clean(), r.out[-600:])

    # ---- SAFE: statements by verb and id, the count stated, nothing lost unsaid
    L = os.path.join(G, 'beans', 'laptop.md')
    r1, r2, r3 = (run(PY, 'bin/safe.py', 'count', L, x) for x in ('can', '#sends-mail', 'details.safety'))
    check("safe: `count` measures statements by verb and by id in a bean in statements, and a header key as before",
          r1.out.strip() == '1 statement' and r2.out.strip() == '1 statement' and r3.out.strip() == '1 block',
          (r1.out, r2.out, r3.out))
    r = run(PY, 'bin/safe.py', 'add', L, stdin='- use: { id: uses-app, by: self, of: app }\n'
                                               '- say: { id: knew-app, by: sam, of: [uses-app], at: now }\n')
    sts = statements('beans/laptop.md')
    check("safe: `add` puts statements after the last, one to a line, at the list's indent",
          r.returncode == 0 and [v for v, _r in sts[-2:]] == ['use', 'say']
          and '\n  - use: { id: uses-app, by: self, of: app }\n' in text('beans/laptop.md'), r.out)
    write('blk.yaml', '- use: { id: uses-app, by: self, of: app, note: "the shop runs on it" }\n', T)
    r = run(PY, 'bin/safe.py', 'replace', L, 'use', '--expect', '2', '--block', os.path.join(T, 'blk.yaml'))
    check("safe: `replace` is refused where the count is not the one stated, nothing written",
          r.returncode != 0 and "names 1 statement(s), expected 2" in r.out, r.out)
    r = run(PY, 'bin/safe.py', 'replace', L, 'use#uses-app', '--expect', '1', '--block', os.path.join(T, 'blk.yaml'))
    check("safe: `replace` puts the block in place of the statement it names",
          r.returncode == 0 and 'statements.use#uses-app.note' in r.out
          and any(v == 'use' and rr.get('note') == 'the shop runs on it' for v, rr in statements('beans/laptop.md')),
          r.out)
    r = save('the laptop runs the app', '- action: [[laptop]] runs [[app]]')
    check("...and saved, the core's gate passing it", r.returncode == 0 and clean(), r.out[-800:])
    import safe  # noqa: E402
    try:
        safe.edit(L, lambda t: re.sub(r'(?m)^  - possible: [^\n]*\n', '', t))
        lost = None
    except safe.UnsafeEdit as e:
        lost = str(e)
    check("safe: an edit that loses a statement it did not declare is refused, the statement named",
          lost and 'statements.possible@0' in lost and '- possible:' in text('beans/laptop.md'), lost)
    r = run(PY, 'bin/safe.py', 'remove', L, '#knew-app', '--expect', '1')
    r = run(PY, 'bin/safe.py', 'remove', L, 'use#uses-app', '--expect', '1') if r.returncode == 0 else r
    check("safe: `remove` takes out the statement it names, and says the entry names it (the rule `kept`)",
          r.returncode == 0 and 'uses-app' not in text('beans/laptop.md') and 'kept' in r.out, r.out)
    r = save('the laptop', '- action: [[laptop]] changed')
    check("...and a save whose entry does not name what was taken out is refused by `kept`",
          r.returncode == 1 and 'kept' in r.out, r.out[-800:])
    run(PY, 'bin/journal.py', 'sam', 'the app off the laptop', '--body', '- removed: uses-app, and knew-app, which knew it')
    r = run(PY, 'bin/save.py', '--again')
    check("...and saved once an entry names it", r.returncode == 0 and clean(), r.out[-800:])

    # ---- SESSION: opened in statements, saved, closed with its presence, merged back through the save
    run('git', 'config', 'daftar.host', 'laptop')
    run('git', 'config', 'daftar.owner', 'sam')
    r = run(PY, 'bin/session.py', 'open', 'tidy-the-laptop', '--purpose', 'tidy the laptop')
    W = os.path.join(T, 'daftar-sessions', 'tidy-the-laptop')
    SB = os.path.join(W, 'beans', 'session-tidy-the-laptop.md')
    sb = read.document(SB)[0] if os.path.isfile(SB) else {}
    verbs = [next(iter(s)) for s in sb.get('statements') or []]
    check("session: `open` writes the session bean in statements — made now, opened at the clock's reading, owned, on "
          "its machine — its copy in `details`",
          r.returncode == 0 and sb.get('kind') == 'session' and verbs == ['make', 'open', 'own', 'be']
          and re.match(r'^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d[+-]\d\d:\d\d$', str(sb['statements'][1]['open']['at']))
          and sb['details']['workspace']['branch'] == 'session/tidy-the-laptop', r.out + str(sb)[:600])
    write('beans/laptop.md', text('beans/laptop.md', W).replace('by the window.', 'by the window, tidied.'), W)
    r = run(PY, 'bin/save.py', 'session-tidy-the-laptop', 'the laptop tidied', '--body',
            '- action: [[session-tidy-the-laptop]] opened; [[laptop]] tidied', cwd=W)
    made = read.document(SB)[0]['statements'][0]['make']
    check("session: its first save writes the moment its bean was made, the core's gate passing",
          r.returncode == 0 and re.match(r'^\d{4}-\d\d-\d\d \d\d:\d\d[+-]\d\d:\d\d$', str(made.get('at'))),
          r.out[-800:] + str(made))
    write('beans/note.md', '---\nbean: note\nkind: document\ntitle: "a note"\nstatements:\n'
                           '  - say: { by: sam, at: now }\n---\nA note written on the main copy meanwhile.\n')
    r = save('a note', '- action: wrote [[note]]')
    r = run(PY, 'bin/session.py', 'close', 'tidy-the-laptop', cwd=G)
    sb = read.document(os.path.join(G, 'beans', 'session-tidy-the-laptop.md'))[0] \
        if os.path.isfile(os.path.join(G, 'beans', 'session-tidy-the-laptop.md')) else {}
    pres = [s['be'] for s in sb.get('statements') or [] if 'be' in s and s['be'].get('as') == 'presence']
    opened = next((s['open']['at'] for s in sb.get('statements') or [] if 'open' in s), '')
    log = run('git', 'log', '--format=%s', '-3').out.split('\n')
    check("session: `close` writes when it was present, from its opening to the clock's reading, derived and saved in "
          "its copy", r.returncode == 0 and pres and str(pres[0]['at']).startswith(str(opened) + '/'), r.out[-1500:])
    check("session: ...and merges it back through the save, the merge's entry naming the beans it brings, the core's "
          "gate passing", r.returncode == 0 and log[0] == 'close session tidy-the-laptop' and clean()
          and '[[session-tidy-the-laptop]]' in text('log/journal.md').split('\n## ')[-1]
          and 'tidied' in text('beans/laptop.md') and not os.path.isdir(W)
          and len(run('git', 'rev-list', '--parents', '-n', '1', 'HEAD').out.split()) == 3, r.out[-1500:] + str(log))

    # ---- CURSOR: a file to its bean, the figures paired, what it inherits along the order's chains
    os.makedirs(os.path.join(T, 'src', 'app', 'models'))
    r = run(PY, 'bin/cursor.py', os.path.join(T, 'src', 'app', 'models', 'invoice.py'))
    check("cursor: a file resolves to the bean whose `be`, as location, holds it, with its role and scan policy",
          r.returncode == 0 and 'cursor -> app' in r.out and 'covered by `be` tree' in r.out
          and 'scan_policy index' in r.out and 'WALK IT' in r.out, r.out)
    check("cursor: what it needs that cannot be is attention", 'IMPOSSIBLE need laptop' in r.out and 'database' in r.out, r.out)
    check("cursor: it inherits along the order's chains — the laptop it is at: forbidden and possible, a live risk",
          'via be (is at): app -> laptop' in r.out and 'FORBIDDEN  can smtp <-- LIVE RISK' in r.out
          and 'through sam' in r.out, r.out)
    r = run(PY, 'bin/cursor.py', 'laptop')
    check("cursor: a bean by its id: its own figures and the notes `details.safety` keeps",
          r.returncode == 0 and 'host · body' in r.out and 'unplug before opening' in r.out
          and 'FORBIDDEN  can smtp' in r.out, r.out)

    # ---- DIGEST: the machines this garden records, by their beans and their names
    r = run(PY, '-c', "import sys; sys.path.insert(0, 'bin'); import digest; print(sorted(digest._host_names()))")
    check("digest: the garden's machines are its host beans and the first label of their DNS names",
          r.out.strip() == "['laptop', 'localhost']", r.out)

    # ---- REFORM: a bean in today's words, in statements in place
    write('beans/printer.md', OLD)
    r = run(PY, 'bin/reform.py', '--check', 'beans/printer.md', 'beans/laptop.md')
    check("reform: --check names a bean still in today's words, and passes one in statements",
          r.returncode == 1 and "beans/printer.md: in today's words" in r.out and 'beans/laptop.md: in statements already'
          in r.out, r.out)
    write('beans/odd.md', OLD.replace('bean: printer', 'bean: odd').replace(
        'provenance:', 'identity:\n  status: confirmed\n  anchors:\n'
        '    - { key: asset-tag, value: "A-7", class: hardware, establishing: true }\nprovenance:'))
    r = run(PY, 'bin/reform.py', 'beans/odd.md')
    check("reform: a name in a namespace the garden's law has no row for is refused, naming the row, nothing written",
          r.returncode == 1 and 'anchor-asset-tag' in r.out and 'genos: host' in text('beans/odd.md'), r.out)
    os.remove(os.path.join(G, 'beans', 'odd.md'))
    r = run(PY, 'bin/reform.py', 'beans/printer.md')
    pr = bean('beans/printer.md') if r.returncode == 0 else {}
    acts = [rr for v, rr in statements('beans/printer.md') if v in ('say', 'read', 'derive', 'make')] if pr else []
    check("reform: the bean is written in statements in place, every value placed, its acts made now",
          r.returncode == 0 and pr.get('kind') == 'host' and 'genos' not in pr and acts
          and all(a.get('at') == 'now' for a in acts) and pr['details']['provenance']['as_of'] == '2026-09-01', r.out)
    r = save('the printer', '- action: wrote [[printer]], reformed into statements')
    check("...and saved through the core's gate", r.returncode == 0 and clean(), r.out[-1200:])

    # ---- UPGRADE: from one release of the core to another
    was = head()

    def upgrade(t, *extra):
        return run(PY, 'bin/dmupgrade.py', t, '--from', REL, *extra)
    r = upgrade('v1.3.0')
    check("upgrade: a release whose core is older than the garden's is refused, nothing touched",
          r.returncode != 0 and 'older than the core' in r.out and clean() and head() == was, r.out[-600:])
    r = upgrade('v1.2.0')
    check("upgrade: a release whose core refuses the garden puts every file back",
          r.returncode == 1 and 'NOT UPGRADED' in r.out and clean() and head() == was
          and f'core@{VERSION}' in text('GARDEN.md'), r.out[-1200:])
    r = upgrade('v1.0.1')
    entry = text('log/journal.md').split('\n## ')[-1]
    check("upgrade: a release of the same core brings its files and records the release, the pin as it was, the entry "
          "a RULE-CHANGE for a person to complete",
          r.returncode == 0 and 'A line v1.0.1 adds.' in text('seed/README.md') and 'daftar_release: "v1.0.1"'
          in text('GARDEN.md') and f'core@{VERSION}' in text('GARDEN.md') and 'RULE-CHANGE' in entry
          and entry.count('(fill in') == 2 and head() == was, r.out[-1200:])
    write('log/journal.md', text('log/journal.md').replace(
        "- ratified_by: (fill in who ratified — the gardener's word, given here)", '- ratified_by: sam, here').replace(
        '- why: (fill in — what this release brings the garden)', '- why: its readme'))
    run('git', 'add', '-A')
    r = run('git', 'commit', '-qm', 'RULE-CHANGE: v1.0.1')
    check("...committed through the core's gate once a person has filled it", r.returncode == 0 and clean(), r.out[-800:])
    r = upgrade('v1.1.0')
    later = f"core@{VERSION.split('.')[0]}.{int(VERSION.split('.')[1]) + 1}"
    check(f"upgrade: a release whose core is later moves the pin to it ({later})",
          r.returncode == 0 and re.search(rf'(?m)^extends: {re.escape(later)}\s', text('GARDEN.md'))
          and 'daftar_release: "v1.1.0"' in text('GARDEN.md'), r.out[-1200:])
    write('log/journal.md', text('log/journal.md').replace(
        "- ratified_by: (fill in who ratified — the gardener's word, given here)", '- ratified_by: sam, here').replace(
        '- why: (fill in — what this release brings the garden)', '- why: the later core'))
    run('git', 'add', '-A')
    r = run('git', 'commit', '-qm', 'RULE-CHANGE: v1.1.0')
    check("...committed through the gate of the later core", r.returncode == 0 and clean(), r.out[-800:])
    r = upgrade('v1.1.0')
    check("...and the same release again is nothing to do", r.returncode == 0 and 'nothing to do' in r.out, r.out[-400:])
except Exception as e:
    import traceback
    traceback.print_exc()
    FAILS.append(f"the suite raised {type(e).__name__}: {e}")
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\ncore_write: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
