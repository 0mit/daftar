#!/usr/bin/env python3
"""stamps — the day of writing is the clock's: a provenance `as_of` a commit adds is the day of the entry it adds.

std-vocab 23.0, `provenance_record.as_of: stamped`. A local model with no date in its context typed, for the day it
wrote a fact down, the nearest date in view — the forms' example day, the gardener's stamp read in another bean — and
the gate could not tell that from a day read off the clock. It can tell whether it is the day of a heading the same
commit adds, which bin/dmjournal.py read from the clock. The writer writes `now`, and the tool that stamps the heading
writes the day in its place. Held here, in a freshly grown garden:

  -  a day typed on a new bean is refused, naming the day of the entry and the fix — `as_of: now`, and the one command
     that saves; `now` committed by a plain `git commit`, in a bean written after its entry, is refused as unstamped;
  +  the day of the heading passes: `now` saved with bin/dmsave.py, and `now` journalled with bin/dmjournal.py and then
     committed with `git add` and `git commit`, are committed as the day of the entry;
  -  an anchor's own record and an entry's (`parties.<k>.provenance`) are judged as a bean's is, each named by its path;
  +  a record carrying `garden`, from a garden this one knows, keeps the stamp its own garden gave it; a merge's
     `merged` passes; the entry's day written in the Persian calendar passes against its Gregorian heading, and the
     day before it does not;
  +  a garden's first commit is exempt, and a record left as it was is never re-judged — a bean edited elsewhere, or
     its anchors put in another order, keeps its old day;
  -  ...but a record ADDED with the day of one already there is counted, and judged.

Run: python3 test/stamps.py   (0 = green).  ~15s.
"""
import re
import os, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'bin'))
import dmcal  # noqa: E402 — the day a position names, in whichever calendar it is written: the gate's own reader

results = []


def check(name, ok, detail=''):
    ok = bool(ok)
    results.append(ok)
    print(("PASS " if ok else "*** FAIL *** ") + name + (f"  [{str(detail)[:600]}]" if detail and not ok else ''))


TMP = tempfile.mkdtemp(prefix='dmstamps-')
G = os.path.join(TMP, 'garden-sam')
F = os.path.join(TMP, 'first', 'garden-sam')
# A MACHINE WITH NO IDENTITY OF ITS OWN, as test/save.py sets it: the garden's is the only one there is.
_empty = os.path.join(TMP, 'empty.gitconfig')
open(_empty, 'w').close()
ENV = {k: v for k, v in os.environ.items() if not k.startswith(('GIT_AUTHOR_', 'GIT_COMMITTER_')) and k != 'EMAIL'}
ENV.update(GIT_CONFIG_GLOBAL=_empty, GIT_CONFIG_NOSYSTEM='1')
_py = 'python' if os.name == 'nt' else 'python3'

# THE NEAREST DATE IN VIEW: the forms' example day, which the measured writer typed as the day it wrote its own facts.
OLD = '2026-09-17'
EARLIER = '2026-09-15'
ALI_GARDEN = 'a1b2c3d4e5f6'


def git(*a, root=G):
    return subprocess.run(['git', '-C', root, *a], capture_output=True, text=True, encoding='utf-8', errors='replace',
                          env=ENV)


def run(*a, root=G):
    r = subprocess.run([sys.executable, *a], capture_output=True, cwd=root, env=ENV)
    return r.returncode, r.stdout.decode('utf-8', 'replace'), r.stderr.decode('utf-8', 'replace')


def save(*a, root=G):
    return run(os.path.join(root, 'bin', 'dmsave.py'), *a, root=root)


def journal_tool(who, what, body, root=G):
    return run(os.path.join(root, 'bin', 'dmjournal.py'), who, what, '--body', body, root=root)


def commit(msg, root=G):
    """A plain `git add -A` and `git commit`, judged by the pre-commit gate: (exit, all it printed)."""
    git('add', '-A', root=root)
    r = git('commit', '-q', '-m', msg, root=root)
    return r.returncode, r.stdout + r.stderr


def head(root=G):
    return git('rev-parse', 'HEAD', root=root).stdout.strip()


def blob(bid, root=G):
    return git('show', f'HEAD:beans/{bid}.md', root=root).stdout


def last_day(root=G):
    """The day of the last heading in the journal: the one clock reading its entry was stamped with."""
    return [l for l in open(os.path.join(root, 'log', 'journal.md'), encoding='utf-8').read().split('\n')
            if l.startswith('## ')][-1][3:13]


def write(bid, text, root=G):
    with open(os.path.join(root, 'beans', bid + '.md'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)


PERSON = """---
bean: {id}
genos: person
title: "{title}"
status: active
summary: "{summary}"
nature: empsychon
identity:
  status: confirmed
  anchors:
    - {{ key: person_id, value: "{pid}", class: logical, establishing: true }}
provenance: {{ src: asserted-by-human, by: "{by}", as_of: {as_of}{extra} }}
owned_by: {{ legal: {{ crown: agape }} }}
responsibility: {{ legal: {{ self: true }} }}
---
{title}.
"""


def person(bid, as_of, by='sam', extra='', pid=None, summary="A friend of the gardener.", root=G):
    write(bid, PERSON.format(id=bid, title=bid.capitalize(), summary=summary, pid=pid or f'person:{bid}', by=by,
                             as_of=as_of, extra=extra), root=root)


_g = subprocess.run([sys.executable, os.path.join(ROOT, 'seed', 'germinate.py'), G, '--gardener', 'sam',
                     '--gardener-name', 'Sam'], capture_output=True, text=True, encoding='utf-8', errors='replace',
                    env=ENV)
check("(setup) a garden is grown, with its gardener", _g.returncode == 0, (_g.stdout + _g.stderr)[-500:])
git('config', 'user.name', 'agent (test)')
git('config', 'user.email', 'agent@localhost')
# THE SAME LANGUAGE, NOT YET A GARDEN: a copy of the tree as germination left it, with no git history, for the first
# commit of a garden below — the one commit with nothing before it to compare a stamp against.
shutil.copytree(G, F, ignore=shutil.ignore_patterns('.git'))

# ---- - a day typed is refused, and the refusal names the fix ---------------------------------------------------------
person('bea', OLD)
_h = head()
rc, out, err = save('sam', 'added bea', '--body', '- action: added [[bea]], a friend of the gardener.')
_day = last_day()
check("a day the writer typed, on a new bean: refused (exit 1), nothing committed — it is not the day of the entry "
      "the commit adds, and the refusal says which day that is",
      rc == 1 and head() == _h and f'beans/bea.md: provenance.as_of is {OLD}' in err and f'({_day})' in err,
      (rc, err[-600:]))
check("...and it names the fix: write `as_of: now`, and the one command that finishes the save its entry waits in",
      'Write `as_of: now`' in err and f'{_py} bin/dmsave.py --again' in err, err[-600:])
person('bea', 'now')
rc, out, err = save('--again')
check("...and with `now` written, `--again` commits the bean with the day of the entry waiting in its place",
      rc == 0 and f'as_of: {_day}' in blob('bea') and OLD not in blob('bea') and 'as_of: now' not in blob('bea'),
      (rc, err[-400:], blob('bea')))

# ---- - `now` nobody stamped is refused -------------------------------------------------------------------------------
_h = head()
# THE ENTRY FIRST, AND THE BEAN AFTER IT: the journal tool stamps what the working tree holds when it writes the entry,
# so a bean written later reaches the commit with the word, and a plain `git commit` stamps nothing.
journal_tool('sam', 'added cyrus', '- action: added [[cyrus]].')
person('cyrus', 'now')
rc, said = commit('added cyrus')
check("`as_of: now` in a bean written after its entry, committed by a plain `git commit`: refused — nothing wrote the "
      "day in its place — naming the command that does",
      rc != 0 and head() == _h and 'beans/cyrus.md: provenance.as_of is `now`' in said and 'bin/dmsave.py' in said,
      (rc, said[-600:]))
rc, out, err = save('--again')
check("...and saved with bin/dmsave.py `--again`, it is committed as the day of the entry waiting",
      rc == 0 and f'as_of: {last_day()}' in blob('cyrus') and 'as_of: now' not in blob('cyrus'), (rc, err[-400:]))

# ---- + the day of the heading passes, by either road -----------------------------------------------------------------
person('dara', 'now')
rc, out, err = save('sam', 'added dara', '--body', '- action: added [[dara]].')
check("`as_of: now` saved with bin/dmsave.py: committed (exit 0) as the day of the entry the save wrote",
      rc == 0 and f'as_of: {last_day()}' in blob('dara') and 'as_of: now' not in blob('dara'), (rc, err[-400:]))
person('ella', 'now')
journal_tool('sam', 'added ella', '- action: added [[ella]].')
rc, said = commit('added ella')
check("`as_of: now` journalled with bin/dmjournal.py after the bean is written, then `git add` and `git commit`: "
      "committed with 0 errors, as the day of the entry",
      rc == 0 and ' 0 error(s)' in said and f'as_of: {last_day()}' in blob('ella') and 'as_of: now' not in blob('ella'),
      (rc, said[-400:]))

# ---- - an anchor's record and an entry's are judged as a bean's is ---------------------------------------------------
write('garden-ali', f"""---
bean: garden-ali
genos: garden
title: "garden-ali — the garden Ali keeps"
status: active
summary: "Ali's own daftar garden. She keeps it; what passes between it and this one is proposed, never written."
nature: lekton
identity:
  status: confirmed
  anchors:
    - {{ key: garden_id, value: "{ALI_GARDEN}", class: logical, establishing: true }}
provenance: {{ src: asserted-by-human, by: "sam", as_of: now }}
owned_by: {{ legal: {{ owner: {{ bean: ali }} }} }}
responsibility: {{ legal: {{ holder: {{ bean: ali }} }} }}
---
Ali's garden.
""")
person('ali', 'now', pid=f'{ALI_GARDEN}/person:ali', summary="Ali, who keeps a garden of her own.")
rc, out, err = save('sam', 'recorded ali and garden-ali', '--body',
                    '- action: added [[ali]] and [[garden-ali]], the garden she keeps.')
check("(setup) Ali and the garden she keeps are recorded, in one commit", rc == 0, (rc, err[-600:]))

CONTRACT = """---
bean: shared-camera
genos: contract
title: "shared-camera — Sam and Ali bought a camera together"
status: active
summary: "Sam and Ali share a camera."
nature: lekton
identity:
  status: confirmed
  anchors:
    - {{ key: contract_id, value: "contract:shared-camera", class: logical, establishing: true, provenance: {{ src: asserted-by-human, by: "ali", as_of: {anchor} }} }}
provenance: {{ src: asserted-by-human, by: "sam", as_of: now }}
owned_by: {{ legal: {{ crown: logos }} }}
responsibility: {{ legal: {{ parties: true }} }}
parties:
  sam: {{ who: {{ bean: sam }}, accepted: 2026-09-10 }}
  ali: {{ who: {{ bean: ali }}, accepted: 2026-09-10, provenance: {{ src: asserted-by-human, by: "ali", as_of: {party} }} }}
over:
  - {{ what: "a camera the two of them use" }}
words: {{ form: spoken, agreed: 2026-09-10 }}
---
Sam and Ali share a camera.
"""
write('shared-camera', CONTRACT.format(anchor=OLD, party=OLD))
_h = head()
rc, out, err = save('sam', 'added shared-camera', '--body', '- action: added [[shared-camera]], agreed with [[ali]].')
check("a day typed on an anchor's own record and on an entry's (`parties.ali.provenance`): refused (exit 1), each named "
      "by its path — and the bean's own `now`, which the save stamped, is not",
      rc == 1 and head() == _h
      and f'beans/shared-camera.md: identity.anchors.provenance.as_of is {OLD}' in err
      and f'beans/shared-camera.md: parties.ali.provenance.as_of is {OLD}' in err
      and 'beans/shared-camera.md: provenance.as_of is' not in err, (rc, err[-800:]))
write('shared-camera', CONTRACT.format(anchor='now', party='now'))
rc, out, err = save('--again')
_b = blob('shared-camera')
check("...and with `now` in each, `--again` commits all three as the day of the entry",
      rc == 0 and 'as_of: now' not in _b and _b.count(f'as_of: {last_day()}') == 3, (rc, err[-600:], _b))

# ---- + a stamp from another garden, and a merge's --------------------------------------------------------------------
person('bahar', OLD, by='ali', extra=f', garden: {ALI_GARDEN}', summary="A friend of Ali's, as her garden records her.")
rc, out, err = save('sam', 'took in bahar from garden-ali', '--body',
                    '- action: added [[bahar]], as [[garden-ali]] recorded her.')
check("a record carrying `garden`, made in a garden this one knows, keeps the stamp its own garden gave it: saved "
      "(exit 0), its day as it came", rc == 0 and f'as_of: {OLD}, garden: {ALI_GARDEN}' in blob('bahar'),
      (rc, err[-600:]))
person('farid', 'merged')
rc, out, err = save('sam', 'added farid', '--body', '- action: added [[farid]].')
check("`as_of: merged` typed on a person's record is refused: only the merge's own record says it",
      rc != 0 and 'as_of is merged' in err, (rc, err[-600:]))
_f = os.path.join(G, 'beans', 'farid.md')
_t = open(_f, encoding='utf-8').read()          # read, THEN open for writing: opening truncates
open(_f, 'w', encoding='utf-8', newline='\n').write(_t.replace('src: asserted-by-human, by: "sam", as_of: merged',
                                                             'src: generated-by-tool, by: dmmerge, as_of: merged'))
rc, out, err = save('--again')
check("...and the merge's own record — `src: generated-by-tool, by: dmmerge` — passes, left as written: when a merge "
      "happened is git's to say", rc == 0 and 'as_of: merged' in blob('farid'), (rc, err[-600:]))

# ---- + a day is a day, in whichever calendar it is written -----------------------------------------------------------
_h = head()
journal_tool('sam', 'added golnar', '- action: added [[golnar]], the day she was written down in the Persian calendar.')
_n = dmcal.to_day(last_day())
_fa, _fa_before = dmcal.from_day(_n, 'persian'), dmcal.from_day(_n - 1, 'persian')
# THE BEAN AFTER THE ENTRY, AND ITS DAY TYPED: the journal tool writes `now` in the Gregorian form, so a day in another
# calendar is read from the heading once it is written, and then written — the one place this suite types a day meant
# to pass, because the point is that the gate reads it as the heading's day.
person('golnar', _fa_before)
rc, said = commit('added golnar')
check(f"a day in the Persian calendar that is not the entry's — {_fa_before}, the day before it — is refused",
      rc != 0 and head() == _h and f'beans/golnar.md: provenance.as_of is {_fa_before}' in said, (rc, said[-600:]))
person('golnar', _fa)
rc, said = commit('added golnar')
check(f"...and the entry's own day in the Persian calendar, {_fa}, passes against its Gregorian heading "
      f"({last_day()})", rc == 0 and f'as_of: {_fa}' in blob('golnar'), (rc, said[-600:]))

# ---- + a garden's first commit, and a record left as it was ----------------------------------------------------------
git('init', '-q', root=F)
git('config', 'user.name', 'agent (test)', root=F)
git('config', 'user.email', 'agent@localhost', root=F)
_i = run(os.path.join(F, 'bin', 'install.py'), root=F)
check("(setup) a second garden's tree, no commit yet, with its gate installed", _i[0] == 0, _i)
# A NAME THIS GARDEN GAVE, UNQUALIFIED: the gardener's qualified name is the first garden's id, which this one's first
# commit is not — the day is what is held here, not the name.
person('sam', OLD, by='sam (gardener)', summary="The gardener.", root=F)
NAS = """---
bean: nas
genos: host
title: "nas — Sam's home NAS"
status: active
summary: "{summary}"
nature: soma
identity:
  status: confirmed
  anchors:
{anchors}provenance: {{ src: asserted-by-human, by: "sam", as_of: {old} }}
owned_by: {{ legal: {{ owner: {{ bean: sam }} }}, technical: {{ owner: {{ bean: sam }} }} }}
responsibility: {{ legal: {{ holder: {{ bean: sam }} }}, technical: {{ holder: {{ bean: sam }} }} }}
---
Sam's NAS.
"""
# TWO DAYS, NOT ONE: anchors of one day, swapped, would read the same were their places counted, and prove nothing.
_prov = 'provenance: {{ src: observed, by: "sam", as_of: {} }}'.format
SERIAL = f'    - {{ key: serial, value: "NAS-0042", class: hardware, establishing: true, {_prov(OLD)} }}\n'
HOSTNAME = f'    - {{ key: hostname, value: "nas", class: network, establishing: false, {_prov(EARLIER)} }}\n'
MAC = f'    - {{ key: mac, value: "a0:b1:c2:d3:e4:f5", class: hardware, establishing: true, {_prov(OLD)} }}\n'


def nas(anchors, summary="A NAS at home."):
    write('nas', NAS.format(summary=summary, anchors=''.join(anchors), old=OLD), root=F)


nas([SERIAL, HOSTNAME])
rc, said = commit('the first commit', root=F)
check("a garden's first commit is exempt — nothing in it was decided by anyone yet: days typed on its beans and their "
      "anchors commit with 0 errors",
      rc == 0 and ' 0 error(s)' in said and git('rev-list', '--count', 'HEAD', root=F).stdout.strip() == '1'
      and f'as_of: {OLD}' in blob('sam', root=F), (rc, said[-800:]))
person('sam', OLD, by='sam (gardener)', summary="The gardener: the person who keeps this garden.", root=F)
rc, out, err = save('sam', 'said who sam is', '--body', '- action: [[sam]] says what Sam is here; its day is as it was.',
                    root=F)
check("a record left as it was is never re-judged: a bean edited elsewhere keeps its old day, and saves (exit 0)",
      rc == 0 and f'as_of: {OLD}' in blob('sam', root=F) and 'who keeps this garden' in blob('sam', root=F),
      (rc, err[-600:]))
nas([HOSTNAME, SERIAL])
rc, out, err = save('sam', 'put the anchors of nas in order', '--body', '- action: [[nas]] names its hostname first.',
                    root=F)
_b = blob('nas', root=F)
check("...nor is a list put in another order: records are counted, not their places — the anchors swapped keep their "
      "days, and save (exit 0)", rc == 0 and 0 < _b.find('key: hostname') < _b.find('key: serial'), (rc, err[-600:]))
_h = head(root=F)
nas([HOSTNAME, SERIAL, MAC])
rc, out, err = save('sam', 'added the mac of nas', '--body', '- action: [[nas]] gains its network card.', root=F)
check("...but a record ADDED with the day of one already there is counted, and judged: refused (exit 1), named by its "
      "path", rc == 1 and head(root=F) == _h and f'beans/nas.md: identity.anchors.provenance.as_of is {OLD}' in err,
      (rc, err[-600:]))

# ---- + what the review of 23.0 found, each held: a move is no stamp, and no stamp escapes by what a writer can type ----
subprocess.run(['git', '-C', F, 'reset', '-q', '--hard', 'HEAD'], capture_output=True)   # the refused save above, undone
subprocess.run(['git', '-C', F, 'mv', 'beans/nas.md', 'beans/nas-two.md'], capture_output=True)
_nf = os.path.join(F, 'beans', 'nas-two.md')
_t = open(_nf, encoding='utf-8').read()          # read, THEN open for writing: opening truncates
open(_nf, 'w', encoding='utf-8', newline='\n').write(_t.replace('bean: nas\n', 'bean: nas-two\n', 1))
_h = head(root=F)
rc, out, err = save('sam', 'renamed nas', '--body', '- action: [[nas]] is [[nas-two]] now; its records as they were.', root=F)
check("A BEAN RENAMED is not a stamp added: its records are matched by what they are, not where they sit — saved, the "
      "old day kept", rc == 0 and head(root=F) != _h and f'as_of: {OLD}' in open(_nf, encoding='utf-8').read(), (rc, err[-600:]))
_own = re.search(r'\b[0-9a-f]{12}\b', run(os.path.join(F, 'bin', 'dmpropose.py'), 'id', root=F)[1] or '')
person('nima', OLD, extra=f', garden: {_own.group(0) if _own else "x"}', root=F)
rc, out, err = save('sam', 'added nima', '--body', '- action: added [[nima]].', root=F)
check("...and THIS garden's own id in `garden` exempts nothing: a typed day under it is refused",
      bool(_own) and rc == 1 and f'as_of is {OLD}' in err, (rc, err[-600:]))
subprocess.run(['git', '-C', F, 'reset', '-q', '--hard', 'HEAD'], capture_output=True)
person('nora', 'now', root=F)
_nn = os.path.join(F, 'beans', 'nora.md')
_t = open(_nn, encoding='utf-8').read()
open(_nn, 'w', encoding='utf-8', newline='\n').write(_t.replace(', as_of: now', '', 1))
rc, out, err = save('sam', 'added nora', '--body', '- action: added [[nora]].', root=F)
check("...and a record added with NO `as_of` is refused, and told to write `as_of: now` — leaving the day out is no escape",
      rc == 1 and 'has no `as_of`' in err and 'as_of: now' in err, (rc, err[-600:]))

shutil.rmtree(TMP, ignore_errors=True)
print(f"\nstamps: {sum(results)}/{len(results)} checks passed"
      + ('' if all(results) else f", {results.count(False)} FAILED"))
sys.exit(0 if all(results) else 1)
