#!/usr/bin/env python3
"""dmsave — save one change in one call: its journal entry, everything staged, and the commit the gate judges.

    python3 bin/dmsave.py "<who>" "<one line: what changed>" --body "- action: …"    # works in every shell
    python3 bin/dmsave.py "<who>" "<what>" --body "- action: …" "- detail: …"      # one quoted line each, as well
    python3 bin/dmsave.py "<who>" "<one line: what changed>" < entry.md               # the body on standard input
    python3 bin/dmsave.py --again     # after a refused save is fixed: commit the entry already written

(`python` on Windows. PowerShell has no `<`: pass the body with `--body`.) It does what took three calls —
`bin/dmjournal.py`, `git add -A`, `git commit` — in one: the entry is appended by dmjournal's own code, its heading read
from the clock and registered, never typed; everything in the garden is staged with `git add -A`; and the commit's
message is <what>. The pre-commit hook judges the index, so the gate judges exactly what is committed. This never
passes --no-verify. Exit 0 = saved; 1 = the commit was refused, the entry written and the files staged; 2 = refused
before anything was written.

A REFUSED SAVE IS LEFT AS IT STANDS. The gate's messages are printed, and the journal entry and the staged files stay as
they are, for the fix. After the fix, `dmsave.py --again` stages everything again and commits the entry already
written, under the <what> of its heading. THE SAME CALL AGAIN DOES THE SAME: an agent that runs its save a second time
is finishing it, so when the entry waiting has this call's <who> and <what>, it is committed and never written a second
time (measured: a small model re-ran the full call after every refusal, and a refusal of that looped it). A call with
another entry while one waits writes its own and commits both. When the gate asks for another entry (one that names a
bean), `bin/dmjournal.py` writes it, and `--again` commits both. An entry written with `bin/dmjournal.py` alone, a
decision with no file changed, is committed the same way.

REFUSED BEFORE ANYTHING IS WRITTEN, because each would leave an entry no commit can carry: nothing in the garden differs
from its last commit (nothing to save); the index holds unmerged paths (`git add -A` would mark them resolved, markers
and all); no pre-commit gate is installed in this clone (the commit would not be judged: `bin/install.py` installs
it); no git identity is set (git would guess an author from the machine, and the log's "who" would be nobody's).

It reaches a garden as every tool does, by `seed/LANGUAGE`'s `bin/dm*.py`, with no list to remember it in; nothing
installs it. It is called "save" because that is the whole act — journal, stage, commit — where "commit" names its last
step.
"""
import collections
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dmparse  # noqa: F401,E402 — its import sets UTF-8 on stdout and stderr, whatever the machine's code page
import dmjournal  # noqa: E402 — the entry is written by the journal tool's own code, and nowhere else

ROOT = dmjournal.ROOT
PY = 'python' if os.name == 'nt' else 'python3'
AGAIN = f"{PY} bin/dmsave.py --again"


def git(*args):
    return subprocess.run(['git', '-C', ROOT, *args], capture_output=True, text=True, encoding='utf-8',
                          errors='replace')


def refuse(msg):
    """Refused before anything was written: exit 2, saying so."""
    msg = msg if 'nothing written' in msg.lower() else msg + ' — nothing written'
    print(dmparse.said(f"dmsave: {msg}"), file=sys.stderr)
    sys.exit(2)


def waiting():
    """The journal's headings that its last commit does not hold: entries written and not yet committed, oldest first.
    Counted, not merely compared, so one heading written twice is seen twice."""
    head = git('show', 'HEAD:./log/journal.md')
    held = collections.Counter(l.rstrip() for l in head.stdout.split('\n') if l.startswith('## ')) \
        if head.returncode == 0 else collections.Counter()
    out = []
    for l in open(dmjournal.JOURNAL, encoding='utf-8').read().split('\n'):
        if l.startswith('## '):
            l = l.rstrip()
            if held[l]:
                held[l] -= 1
            else:
                out.append(l)
    return out


def what_of(heading):
    """The <what> of `## <when> · <who> · <what>`."""
    parts = heading[3:].split(' · ', 2)
    return parts[2] if len(parts) == 3 else heading[3:]


def who_of(heading):
    """The <who> of `## <when> · <who> · <what>`."""
    parts = heading[3:].split(' · ', 2)
    return parts[1] if len(parts) == 3 else ''


def ready(again, body=''):
    """Every refusal that must come before a word is written, in the order a writer can act on them: the garden, what
    there is to save, and then the clone — its gate and its identity. Returns the entries already waiting."""
    if not os.path.exists(dmjournal.JOURNAL):
        refuse(f"no {os.path.relpath(dmjournal.JOURNAL, ROOT)} — is this a garden? Nothing written")
    top = git('rev-parse', '--show-toplevel')
    if top.returncode != 0:
        refuse(f"{ROOT} is not a git working copy, and a save is a commit — nothing written")
    unmerged = sorted({l.split('\t', 1)[-1] for l in git('ls-files', '--unmerged').stdout.splitlines() if l})
    if unmerged:
        refuse(f"the index holds unmerged paths ({', '.join(unmerged[:4])}{', …' if len(unmerged) > 4 else ''}) — "
               f"`git add -A` would mark them resolved as they stand, conflict markers and all. Settle each first; "
               f"nothing written")
    pending = waiting()
    if again and not pending:
        refuse(f"--again commits a journal entry already written, and every entry in the journal is committed. "
               f"Nothing written. Save a change with: {PY} bin/dmsave.py \"<who>\" \"<what>\" --body \"- action: …\"")
    if not again and not git('status', '--porcelain').stdout.strip():
        # A SAVE CALLED BEFORE THE WRITE: measured, a small model took the save for the act of recording and ran it with
        # the bean unwritten. Its own entry names the bean, so the refusal says which file is missing.
        missing = [b for b in dict.fromkeys(re.findall(r'\[\[([^\]|#\s]+)', body or ''))
                   if not os.path.exists(os.path.join(ROOT, 'beans', b + '.md'))]
        if missing:
            refuse(f"nothing to save — your entry names {', '.join(f'[[{b}]]' for b in missing)}, and "
                   f"{', '.join(f'beans/{b}.md' for b in missing)} {'is' if len(missing) == 1 else 'are'} not written. A "
                   f"save records a file already written: write {'it' if len(missing) == 1 else 'them'} first, whole, "
                   f"then run this same command again; nothing written")
        refuse("nothing to save — no file in the garden differs from its last commit. Write the bean first; nothing "
               "written")
    hook = git('rev-parse', '--git-path', 'hooks/pre-commit').stdout.strip()
    hook_at = hook if os.path.isabs(hook) else os.path.join(ROOT, hook)
    if not os.path.isfile(hook_at):
        refuse(f"no pre-commit gate is installed in this clone ({hook} is missing), so a commit here would not be "
               f"judged — nothing written. Install it: {PY} bin/install.py")
    if not (os.name == 'nt' or os.access(hook_at, os.X_OK)):
        refuse(f"the pre-commit gate {hook} is not executable, so git would skip it and the commit would not be "
               f"judged — nothing written. Install it again: {PY} bin/install.py")
    # STRICTLY SET, as seed/germinate.py asks: a configuration or the environment, never a name guessed from the machine
    if any(git('-c', 'user.useConfigOnly=true', 'var', v).returncode != 0 for v in ('GIT_AUTHOR_IDENT',
                                                                                     'GIT_COMMITTER_IDENT')):
        refuse("no git identity is set here, so the commit's author would be guessed from the machine — nothing "
               "written. Set the one you commit under (an agent: its own name, e.g. \"agent (model, session)\"):\n"
               "  git config user.name \"Your Name\"\n  git config user.email \"you@example.org\"")
    return pending


def commit(message, again):
    """Stage everything and commit, the hook judging the index. 0 when saved; 1, with the way on, when not."""
    def not_saved(why):
        # SHORT, because it stays in the reader's context: the entry is theirs already, so it is not shown again.
        print(dmparse.said(f"dmsave: NOT SAVED — {why}. The journal entry is written and the files are staged; leave "
                           f"both, fix what it names, then run:\n  {AGAIN}"), file=sys.stderr)
        return 1
    # EVERY BEAN ANY WAITING ENTRY NAMES is stamped with the day of the last one — the commit carries them all, and the
    # gate grants the day of any heading it adds. A bean fixed after a refusal, or named only by an entry written before
    # this call, may still say `now`. Silent when it succeeds.
    pend = waiting()
    _text = open(dmjournal.JOURNAL, encoding='utf-8').read()
    _held = git('show', 'HEAD:./log/journal.md').stdout
    _text = _text[len(_held):] if _held and _text.startswith(_held) else _text
    if pend:
        dmjournal.stamp_now(pend[-1], _text)
    add = git('add', '-A')
    if add.returncode != 0:
        print(add.stderr.rstrip(), file=sys.stderr)
        return not_saved("`git add -A` failed (above)")
    if git('diff', '--cached', '--quiet').returncode == 0:
        return not_saved("nothing is staged to commit")
    sys.stdout.flush()
    sys.stderr.flush()
    # The hook's lines are the gate's own, and are passed through as it prints them; `-q` leaves out git's summary.
    if subprocess.run(['git', '-C', ROOT, 'commit', '-q', '-m', message]).returncode != 0:
        return not_saved("the commit was refused (above)")
    print(dmparse.said(f"saved {git('rev-parse', '--short', 'HEAD').stdout.strip()}: {message}"))
    return 0


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__)
        return 0 if argv else 2
    if '--again' in argv:
        if argv != ['--again']:
            refuse("--again takes nothing else: it commits the entry already written, under its own <what>")
        entries = ready(again=True)
        return commit('; '.join(what_of(h) for h in entries), again=True)
    rest, body = list(argv), None
    if '--body' in rest:
        i = rest.index('--body')
        # EVERY WORD AFTER --body IS A LINE OF THE BODY, up to the next option: an agent passes a list as one quoted
        # argument per item as often as one string with line breaks (measured), and both mean the same body.
        j = i + 1
        while j < len(rest) and not rest[j].startswith('--'):
            j += 1
        if j == i + 1:
            refuse("--body takes the entry's body, in quotes")
        body = '\n'.join(rest[i + 1:j])
        del rest[i:j]
    flags = [a for a in rest if a.startswith('--')]
    if flags or len(rest) != 2:
        refuse((f"{flags[0]!r} is no option of dmsave. " if flags else "") + f"It takes \"<who>\" \"<what>\" and the "
               f"body — {PY} bin/dmsave.py \"<who>\" \"<what>\" --body \"- action: …\" — or --again alone")
    who, what = rest
    if body is None:
        stream = getattr(sys.stdin, 'buffer', None)
        if stream is None:
            refuse("there is no standard input to read the body from — pass it with --body")
        # A TERMINAL IS NOT A BODY: reading one waits, with no prompt, for a person who may not be there.
        if sys.stdin.isatty():
            refuse(f"no body, and nothing written. Pass it with --body: {PY} bin/dmsave.py \"{who}\" \"{what}\" --body "
                   f"\"- action: …\"")
        try:
            body = dmjournal.decode_body(stream.read())
        except SystemExit as e:
            refuse(str(e.code).replace('dmjournal: ', '', 1))
    pending = ready(again=False, body=body)
    if pending and who_of(pending[-1]).strip() == who.strip() and what_of(pending[-1]).strip() == what.strip():
        # THE SAME CALL AGAIN: its entry is written already — finish that save, and write the entry no second time
        print(dmparse.said(f"dmsave: this entry is written already, and waiting — committing it, as --again does"),
              file=sys.stderr)
        return commit('; '.join(what_of(h) for h in pending), again=True)
    try:
        dmjournal.append(who, what, body)
    except SystemExit as e:                       # the journal tool refused the entry, and wrote nothing
        refuse(str(e.code).replace('dmjournal: ', '', 1))
    return commit('; '.join([what_of(h) for h in pending] + [what.strip()]), again=False)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
