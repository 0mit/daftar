#!/usr/bin/env python3
"""save — one call saves a change: its journal entry, everything staged, and the commit the gate judges (v1 part 12:
in a garden of the core, grown by test/grow.py, judged by the core's gate).

An agent saved a bean in three calls — `bin/dmjournal.py`, `git add -A`, `git commit` — and a refused one in two more,
and each call's words stay in its context for the rest of its session. `bin/dmsave.py` is the one call, held here in a
freshly grown garden to what its first lines say:

  +  a bean and its entry are saved in one call: ONE commit, its message <what>, holding the bean and an entry whose
     heading the clock wrote and the register holds; nothing is left unstaged, and three lines are printed — the gate's
     verdict, the fast suite's count, and the commit saved;
  +  the body may come on standard input, read as bin/dmjournal.py reads it: Persian on a cp1252 machine, byte for byte;
  -  a refused save commits nothing: the gate's reason is printed, the entry is written once and the files are staged,
     and the one command to run after the fix is named — `dmsave.py --again`; the same call run again finishes it too;
  +  the same call run again finishes the waiting save and writes no second entry; another entry commits with it;
  +  after the fix, `--again` commits what the working tree holds now — the fix, never the refused copy — under the
     entry's <what>, and an entry the gate asked for goes with it; an entry written with bin/dmjournal.py alone is
     committed the same way;
  -  refused before a word is written or staged: nothing to save; `--again` with no entry waiting; an entry the journal
     tool refuses; no --body and a terminal on standard input, which would wait for nobody; no pre-commit gate
     installed, or one git would skip; no git identity set; an index with unmerged paths; an option it does not know;
  -  it never passes --no-verify.

  +  one save at a time: a save waits for the clone's lock, and past its bound is refused (N34).

Run: python3 test/save.py   (0 = green).  ~10s.
"""
import datetime
import ast, re, os, shutil, stat, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
results = []


def check(name, ok, detail=''):
    ok = bool(ok)
    results.append(ok)
    print(("PASS " if ok else "*** FAIL *** ") + name + (f"  [{str(detail)[:600]}]" if detail and not ok else ''))


TMP = tempfile.mkdtemp(prefix='dmsave-')
G = os.path.join(TMP, 'garden-sam')
# A MACHINE WITH NO IDENTITY OF ITS OWN: no global or system configuration, and none in the environment, so the one the
# garden sets is the only one there is — and taking it away takes it away.
_empty = os.path.join(TMP, 'empty.gitconfig')
open(_empty, 'w').close()
ENV = {k: v for k, v in os.environ.items() if not k.startswith(('GIT_AUTHOR_', 'GIT_COMMITTER_')) and k != 'EMAIL'}
ENV.update(GIT_CONFIG_GLOBAL=_empty, GIT_CONFIG_NOSYSTEM='1')


def git(*a):
    return subprocess.run(['git', '-C', G, *a], capture_output=True, text=True, encoding='utf-8', errors='replace',
                          env=ENV)


sys.path.insert(0, os.path.join(ROOT, 'test'))
import grow  # noqa: E402
_g = grow.garden(grow.release(os.path.join(TMP, 'release')), G, 'sam', '--gardener-name', 'Sam')
check("(setup) a garden of the core is grown (test/grow.py), with its gardener", _g.returncode == 0, _g.out[-500:])
git('config', 'user.name', 'agent (test)')
git('config', 'user.email', 'agent@localhost')
TOOL = os.path.join(G, 'bin', 'dmsave.py')
JP = os.path.join(G, 'log', 'journal.md')
_py = 'python' if os.name == 'nt' else 'python3'

# A bean the gardener keeps that is not a person: what is saved here is how a save works, and a person who is not the
# gardener is kept by name only on their consent (24.0, F2) — which is test/privacy.py's to show, not this suite's.
PERSON = """---
bean: {id}
kind: {kind}
title: "{title}"
summary: "A program the gardener keeps."
statements:
  - say: {{ by: sam, at: now }}
  - own: {{ by: sam, of: self }}
---
A program.
"""


def bean(bid, status='active', title=None):
    """A program the gardener keeps; `status` other than `active` writes it of a kind the law has not, which the gate
    refuses (today's suite wrote a status the law does not list)."""
    with open(os.path.join(G, 'beans', bid + '.md'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(PERSON.format(id=bid, kind='product' if status == 'active' else status, title=title or bid.capitalize()))


def save(*a, stdin=b'', env=None):
    r = subprocess.run([sys.executable, TOOL, *a], input=stdin, capture_output=True, cwd=G, env=env or ENV)
    return r.returncode, r.stdout.decode('utf-8', 'replace'), r.stderr.decode('utf-8', 'replace')


def head():
    return git('rev-parse', 'HEAD').stdout.strip()


def journal():
    return open(JP, 'rb').read()


def stamps():
    p = git('rev-parse', '--git-path', 'daftar/journal-stamps').stdout.strip()
    p = p if os.path.isabs(p) else os.path.join(G, p)
    return open(p, 'rb').read() if os.path.exists(p) else b''


def headings(b, who_what=''):
    return [l for l in b.decode('utf-8').split('\n') if l.startswith('## ') and l.endswith(who_what)]


def untouched(before):
    """The journal, the register, HEAD and the index are as they were."""
    j, s, h = before
    return (journal() == j and stamps() == s and head() == h
            and not git('diff', '--cached', '--name-only').stdout.strip())


def state():
    return journal(), stamps(), head()


# ---- - nothing to save -----------------------------------------------------------------------------------------------
_s = state()
rc, out, err = save('sam', 'nothing', '--body', '- action: nothing.')
check("nothing in the garden differs from its last commit: refused (exit 2), and nothing is written or registered",
      rc == 2 and 'nothing to save' in err and untouched(_s), (rc, out, err))
rc, out, err = save('sam', 'added the camera', '--body', '- action: added [[shared-camera]], kept by [[sam]].')
check("...and a save run before the bean is written names the file its own entry names and lacks — not the gardener's, "
      "which is written", rc == 2 and 'beans/shared-camera.md is not written' in err and 'beans/sam.md' not in err
      and os.path.exists(os.path.join(G, 'beans', 'sam.md')) and untouched(_s), (rc, out, err))

# ---- + one bean, saved in one call -----------------------------------------------------------------------------------
bean('ali')
_s = state()
rc, out, err = save('sam', 'added ali', '--body', '- action: added [[ali]], a friend of the gardener.')
_added = journal()[len(_s[0]):]
_h = headings(_added)
check("a bean and its entry are saved in ONE call (exit 0): one commit on the last, its message the entry's <what>",
      rc == 0 and git('rev-parse', 'HEAD~1').stdout.strip() == _s[2]
      and git('log', '-1', '--format=%B').stdout.strip() == 'added ali', (rc, out, err))
check("...holding the bean and the journal, and nothing is left unstaged or untracked",
      set(git('show', '--name-only', '--format=', 'HEAD').stdout.split()) == {'beans/ali.md', 'log/journal.md'}
      and not git('status', '--porcelain').stdout.strip(), git('status', '--porcelain').stdout)
check("...the entry appended as given, under ONE heading the clock wrote and the register holds",
      _added.decode('utf-8').endswith('\n- action: added [[ali]], a friend of the gardener.\n') and len(_h) == 1
      and _h[0].endswith(' · sam · added ali') and (_h[0] + '\n').encode('utf-8') in stamps(), _added[-300:])
_lines = [l for l in (out + err).splitlines() if l.strip()]
check("...and it prints two lines: the core's gate's verdict, and the commit it saved (today's fast suite is today's gate's)",
      len(_lines) == 2 and any('0 error(s)' in l for l in _lines)
      and out.strip() == f"saved {git('rev-parse', '--short', 'HEAD').stdout.strip()}: added ali", _lines)

# ---- - a refused save leaves everything where it stands --------------------------------------------------------------
bean('friend-b', status='bogus')
_s = state()
rc, out, err = save('sam', 'added friend-b', '--body', '- action: added [[friend-b]].')
check("a bean the gate refuses: exit 1, nothing committed, and the gate's reason printed",
      rc == 1 and head() == _s[2] and "`kind: bogus` is no kind of the law" in err, (rc, out, err[-600:]))
check("...the entry is written ONCE, and the bean and the journal stay staged, for the fix",
      len(headings(journal()[len(_s[0]):], ' · sam · added friend-b')) == 1
      and {'beans/friend-b.md', 'log/journal.md'} <= set(git('diff', '--cached', '--name-only').stdout.split()),
      git('status', '--porcelain').stdout)
_close = err[err.find('dmsave: NOT SAVED'):]
check("...and it names the one command to run after the fix, `dmsave.py --again`, and nothing else to run",
      f"\n  {_py} bin/dmsave.py --again" in _close and 'git add' not in _close and len(_close) < 300, _close)

_j = journal()
rc, out, err = save('sam', 'added friend-b', '--body', '- action: added [[friend-b]].')
check("the same call run again before the fix finishes the waiting save: refused by the gate again (exit 1), and no "
      "second entry written", rc == 1 and journal() == _j and head() == _s[2] and 'written already' in err, (rc, err))

# ---- + after the fix, --again commits what the working tree holds now ------------------------------------------------
bean('friend-b')                                       # fixed in the working tree, and not staged: --again stages it
rc, out, err = save('--again')
check("after the fix, `--again` saves (exit 0): one commit, its message the entry's <what>",
      rc == 0 and git('rev-parse', 'HEAD~1').stdout.strip() == _s[2]
      and git('log', '-1', '--format=%B').stdout.strip() == 'added friend-b', (rc, out, err))
check("...holding the FIX, never the refused copy, and the entry once, with nothing left unstaged",
      'kind: product' in git('show', 'HEAD:beans/friend-b.md').stdout
      and len(headings(git('show', 'HEAD:log/journal.md').stdout.encode('utf-8'), ' · sam · added friend-b')) == 1
      and not git('status', '--porcelain').stdout.strip(), git('show', 'HEAD:beans/friend-b.md').stdout[:300])
_s = state()
rc, out, err = save('--again')
check("`--again` with no entry waiting is refused (exit 2), naming the full call", rc == 2 and untouched(_s)
      and 'every entry in the journal is committed' in err and 'bin/dmsave.py "<who>"' in err, (rc, err))

# ---- + the same call again, after the fix, saves; a call with another entry commits both ---------------------------------
bean('friend-e', status='bogus')
_s = state()
rc, out, err = save('sam', 'added friend-e', '--body', '- action: added [[friend-e]].')
bean('friend-e')                                       # fixed, and the same call run again
rc, out, err = save('sam', 'added friend-e', '--body', '- action: added [[friend-e]].')
check("after the fix, the same call again saves (exit 0), the entry committed once, the fix and not the refused copy",
      rc == 0 and git('log', '-1', '--format=%B').stdout.strip() == 'added friend-e'
      and len(headings(git('show', 'HEAD:log/journal.md').stdout.encode('utf-8'), ' · sam · added friend-e')) == 1
      and 'kind: product' in git('show', 'HEAD:beans/friend-e.md').stdout, (rc, out, err[-400:]))
bean('friend-g', status='bogus')
rc, out, err = save('sam', 'added friend-g', '--body', '- action: added [[friend-g]].')
bean('friend-g')
bean('friend-h')
rc, out, err = save('sam', 'added friend-h', '--body', '- action: added [[friend-h]].')
check("a call with another entry while one waits writes its own and commits both, each entry once",
      rc == 0 and git('log', '-1', '--format=%B').stdout.strip() == 'added friend-g; added friend-h'
      and len(headings(git('show', 'HEAD:log/journal.md').stdout.encode('utf-8'), ' · sam · added friend-g')) == 1,
      (rc, out, err[-400:]))

# ---- + a body given as one quoted line per item is one body -----------------------------------------------------------
bean('friend-i')
bean('friend-j')
rc, out, err = save('sam', 'added friend-i and friend-j', '--body', '- action: added [[friend-i]].', '- action: added [[friend-j]].')
_e = git('show', 'HEAD:log/journal.md').stdout
check("a body given as one quoted line per item is taken as one body, its lines in order, and saved (exit 0)",
      rc == 0 and '- action: added [[friend-i]].\n- action: added [[friend-j]].' in _e, (rc, out, err[-400:]))

# ---- + an entry the gate asks for goes with the first ----------------------------------------------------------------
bean('friend-c')
bean('friend-d')
_s = state()
rc, out, err = save('sam', 'added friend-c', '--body', '- action: added [[friend-c]].')
check("a save whose entry names one of two beans is refused, the gate asking for an entry that names the other",
      rc == 1 and head() == _s[2] and 'beans/friend-d.md: changed by this commit, and named by no journal entry it adds' in err,
      (rc, err[-600:]))
subprocess.run([sys.executable, os.path.join(G, 'bin', 'dmjournal.py'), 'sam', 'added friend-d', '--body',
                '- action: added [[friend-d]].'], capture_output=True, cwd=G, env=ENV)
rc, out, err = save('--again')
check("...the journal tool writes it, and `--again` commits both entries, its message each <what>",
      rc == 0 and git('log', '-1', '--format=%B').stdout.strip() == 'added friend-c; added friend-d'
      and {'beans/friend-c.md', 'beans/friend-d.md'}
      <= set(git('show', '--name-only', '--format=', 'HEAD').stdout.split()),
      (rc, out, err[-600:]))
subprocess.run([sys.executable, os.path.join(G, 'bin', 'dmjournal.py'), 'sam', 'decided to wait', '--body',
                '- decision: nothing is written until Ali says.'], capture_output=True, cwd=G, env=ENV)
rc, out, err = save('--again')
check("an entry written with the journal tool alone, no file changed, is committed by `--again`",
      rc == 0 and git('log', '-1', '--format=%B').stdout.strip() == 'decided to wait'
      and git('show', '--name-only', '--format=', 'HEAD').stdout.split() == ['log/journal.md'], (rc, out, err))

# ---- + the body on standard input, as the journal tool reads it ------------------------------------------------------
bean('friend-e', title='A friend — دوست سام')
_cp = {k: v for k, v in ENV.items() if k not in ('PYTHONUTF8', 'PYTHONIOENCODING')}
_cp['PYTHONIOENCODING'] = 'cp1252'
_body = '- action: added [[friend-e]] — دوست سام.\n- why: سام گفت.'
_s = state()
rc, out, err = save('سام', 'دوستی را افزود', stdin=(_body + '\n').encode('utf-8'), env=_cp)
check("the body on standard input, Persian on a cp1252 machine: saved (exit 0), the entry byte for byte, the message "
      "too",
      rc == 0 and journal()[len(_s[0]):].endswith(('\n' + _body + '\n').encode('utf-8'))
      and git('log', '-1', '--format=%B').stdout.strip() == 'دوستی را افزود', (rc, out, err))

# ---- - refused before anything is written ----------------------------------------------------------------------------
bean('friend-f')
_s = state()
for _why, _args, _said in (
        ("an entry the journal tool refuses (an escape in its body)",
         ('sam', 'added friend-f', '--body', '- \x1b[2J x'),
         'control character'),
        ("an entry with no body", ('sam', 'added friend-f', '--body', '  '), 'has no body'),
        ("an option it does not know", ('sam', 'added friend-f', '--bdy', 'x'), "'--bdy' is no option of dmsave"),
        ("--again beside anything else", ('--again', 'sam'), '--again takes nothing else'),
        ("--body with nothing after it", ('sam', 'added friend-f', '--body'), '--body takes')):
    rc, out, err = save(*_args)
    check(f"{_why}: refused (exit 2), nothing written, registered or staged", rc == 2 and _said in err
          and untouched(_s), (rc, err))

if os.name != 'nt':                               # A TERMINAL IS NOT A BODY: read, it waits for a person who may not be there
    _m, _t = os.openpty()
    try:
        _r = subprocess.run([sys.executable, TOOL, 'sam', 'added friend-f'], stdin=_t, capture_output=True, cwd=G,
                            env=ENV, timeout=60)
    finally:
        os.close(_m)
        os.close(_t)
    check("no --body, and a terminal on standard input: refused at once (exit 2), naming --body; nothing written",
          _r.returncode == 2 and b'--body' in _r.stderr and untouched(_s), _r.stderr)
_hook = git('rev-parse', '--git-path', 'hooks/pre-commit').stdout.strip()
_hook = _hook if os.path.isabs(_hook) else os.path.join(G, _hook)
os.rename(_hook, _hook + '.away')
rc, out, err = save('sam', 'added friend-f', '--body', '- action: added [[friend-f]].')
os.rename(_hook + '.away', _hook)
check("no pre-commit gate installed: refused (exit 2) — a commit would not be judged — naming bin/install.py; "
      "nothing written", rc == 2 and 'no pre-commit gate is installed' in err and 'bin/install.py' in err
      and untouched(_s), (rc, err))
if os.name != 'nt':
    _mode = os.stat(_hook).st_mode
    os.chmod(_hook, _mode & ~(stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))
    rc, out, err = save('sam', 'added friend-f', '--body', '- action: added [[friend-f]].')
    os.chmod(_hook, _mode)
    check("a gate git would skip, not executable: refused (exit 2), nothing written",
          rc == 2 and 'not executable' in err and untouched(_s), (rc, err))

git('config', '--unset', 'user.name')
rc, out, err = save('sam', 'added friend-f', '--body', '- action: added [[friend-f]].')
git('config', 'user.name', 'agent (test)')
check("no git identity set: refused (exit 2) with the two lines that set one; nothing written",
      rc == 2 and 'no git identity is set' in err and 'git config user.name' in err and untouched(_s), (rc, err))

_blob = subprocess.run(['git', '-C', G, 'hash-object', '-w', '--stdin'], input='x\n', capture_output=True, text=True,
                       encoding='utf-8', env=ENV).stdout.strip()
subprocess.run(['git', '-C', G, 'update-index', '--index-info'], env=ENV, capture_output=True, text=True,
               encoding='utf-8', input=''.join(f"100644 {_blob} {n}\tnotes.txt\n" for n in (1, 2, 3)))
rc, out, err = save('sam', 'added friend-f', '--body', '- action: added [[friend-f]].')
_unmerged = git('ls-files', '--unmerged').stdout
git('update-index', '--force-remove', 'notes.txt')
check("an index holding unmerged paths: refused (exit 2) — `git add -A` would mark them resolved — nothing written, "
      "and the conflict left as it was", rc == 2 and 'unmerged paths (notes.txt)' in err and _unmerged.strip()
      and journal() == _s[0] and head() == _s[2], (rc, err))

rc, out, err = save('sam', 'added friend-f', '--body', '- action: added [[friend-f]].')
check("...and with each put right, the same bean saves", rc == 0 and not git('status', '--porcelain').stdout.strip(),
      (rc, out, err))

# ---- + the moment of writing is the clock's: `at: now` becomes the moment of the entry (the core's save) -----------------
def now_bean(bid, extra=''):
    bean(bid)
    f = os.path.join(G, 'beans', bid + '.md')
    t = open(f, encoding='utf-8').read()          # PERSON writes `at: now` already: the save stamps it
    open(f, 'w', encoding='utf-8', newline='\n').write(t.replace('\n---\nA program', '\n' + extra + '---\nA program', 1)
                                                      if extra else t)


def blob(bid):
    return git('show', f'HEAD:beans/{bid}.md').stdout


def moment_of_last_entry():
    return [l for l in journal().decode('utf-8').split('\n') if l.startswith('## ')][-1][3:].split(' · ', 1)[0]


now_bean('noor')
rc, out, err = save('sam', 'added noor', '--body', '- action: added [[noor]].')
check("a bean saved with `at: now` is committed with the moment of its journal entry, the one clock reading of the "
      "save — never the word `now`, and never a moment the writer typed",
      rc == 0 and f'at: "{moment_of_last_entry()}"' in blob('noor') and 'at: now' not in blob('noor'), (rc, err, blob('noor')))
now_bean('omar', '  - run: { by: self, of: nobody-here }\n')
rc, out, err = save('sam', 'added omar', '--body', '- action: added [[omar]].')
_f = os.path.join(G, 'beans', 'omar.md')
_t = open(_f, encoding='utf-8').read()          # read, THEN open for writing: opening truncates (dmsafe's incident 4)
open(_f, 'w', encoding='utf-8', newline='\n').write(
    re.sub(r'at: "[^"]*"', 'at: now', _t.replace('  - run: { by: self, of: nobody-here }\n', '')))
rc2, out2, err2 = save('--again')
check("...and on `--again`, a `now` written again while fixing the refusal takes the moment of the entry waiting",
      rc != 0 and rc2 == 0 and f'at: "{moment_of_last_entry()}"' in blob('omar'), (rc, rc2, err2, blob('omar')))
# A MOMENT THE WRITER TYPED IS NEVER REWRITTEN BY THE TOOL — judged by the gate instead: refused, and left as typed.
def typed_bean(bid, at):
    bean(bid)
    f = os.path.join(G, 'beans', bid + '.md')
    t = open(f, encoding='utf-8').read()          # read, THEN open for writing: opening truncates
    open(f, 'w', encoding='utf-8', newline='\n').write(t.replace('at: now', f'at: "{at}"'))
typed_bean('pia', '2001-01-02 10:00+03:00')
rc, out, err = save('sam', 'added pia', '--body', '- action: added [[pia]].')
check("a moment the writer typed is refused by the gate, and the tool leaves it as the writer typed it",
      rc != 0 and 'at: "2001-01-02 10:00+03:00"' in open(os.path.join(G, 'beans', 'pia.md'), encoding='utf-8').read(),
      (rc, err[-400:]))
os.remove(os.path.join(G, 'beans', 'pia.md'))
git('reset', '-q')
git('checkout', '--', 'log/journal.md')

# ---- + one save at a time: a save waits for the clone's lock, and past its bound is refused (24.0, N34) ----------------
_lp = os.path.join(G, git('rev-parse', '--git-dir').stdout.strip(), 'daftar-save.lock')
_lf = open(_lp, 'a+')
if os.name == 'nt':
    import msvcrt
    _lf.seek(0)
    msvcrt.locking(_lf.fileno(), msvcrt.LK_NBLCK, 1)
else:
    import fcntl
    fcntl.flock(_lf.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
_s = (journal(), None, head())
bean('quinn')
rc, out, err = save('sam', 'added quinn', '--body', '- action: added [[quinn]].', env={**ENV, 'DAFTAR_SAVE_WAIT': '1'})
check("a save while another holds the clone's lock waits its bound, then is refused (exit 2), nothing written: two "
      "writers in one clone queue, and neither journals over the other's staged files",
      rc == 2 and 'another save is in progress' in err and journal() == _s[0] and head() == _s[2], (rc, err))
_lf.close()                                       # the other save ends: its lock goes with it
os.remove(os.path.join(G, 'beans', 'quinn.md'))

# ---- - it never passes --no-verify -----------------------------------------------------------------------------------
_src = ast.parse(open(os.path.join(ROOT, 'bin', 'save.py'), encoding='utf-8').read())
_doc = _src.body[0].value.value                      # the docstring may say it never does; the code may not do it
_strs = [n.value for n in ast.walk(_src)
         if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value != _doc]
check("bin/save.py (bin/dmsave.py its alias) never passes --no-verify, nor its short form: no string it holds is either",
      not any(s in ('--no-verify', '-n') or 'no-verify' in s for s in _strs), [s for s in _strs if 'verify' in s])

shutil.rmtree(TMP, ignore_errors=True)
print(f"\nsave: {sum(results)}/{len(results)} checks passed"
      + ('' if all(results) else f", {results.count(False)} FAILED"))
sys.exit(0 if all(results) else 1)
