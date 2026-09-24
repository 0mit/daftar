#!/usr/bin/env python3
"""dmjournal — append a journal entry whose heading is read from the clock, never typed.

    python3 bin/dmjournal.py "<who>" "<what>" --body "- action: …"    # works in every shell
    python3 bin/dmjournal.py "<who>" "<what>" < entry.md               # the body on standard input

(`python` on Windows. PowerShell has no `<`: pass the body with `--body`, a line break inside its quotes kept as
typed.) Give the body only: no `## ` line, because the heading is this tool's to write.

The heading is `## <when> · <who> · <what>`, and <when> is the position in time the gate accepts — to the
minute, with its offset — read from this machine's clock at the moment of writing. A heading typed by hand
is a moment remembered rather than measured, and twice in one evening a writer typed the time before reading
it. The gate checks the FORM of a heading; only the clock can supply its truth, so the clock supplies it.

The body is appended as given. It is not checked here: the gate checks that it names each bean the commit
changes, that it says RULE-CHANGE where the law moved, and that no `(fill in` is left. Nothing is committed.

UTF-8 ON EVERY PLATFORM. The journal is append-only, so a garbled entry cannot be taken back: the body read from
standard input is read as BYTES and decoded as UTF-8 (a byte-order mark is dropped; UTF-16 with its mark, which
Windows PowerShell 5.1 writes with `>`, is read as UTF-16), and bytes that are not UTF-8 are refused before
anything is written, never guessed at in the machine's code page. UTF-16 WITHOUT its mark is valid UTF-8 with a
NUL after every letter, so it is refused by the NUL (below), saying what it looks like. The output goes through
dmparse's UTF-8 streams. The heading is printed only AFTER the entry is written, and a failure to print it — a
closed pipe, or no standard output at all — is not a failure of the write: a run that reported an error after
writing would be run again, and append the entry twice.

ONE LINE IS ONE LINE, AND TEXT IS TEXT. The journal is read line by line, by the gate and by anything else, and a
character that some readers take for a line break (a vertical tab, a form feed, the separators \\x1c-\\x1e, NEL,
U+2028, U+2029) would let one line carry a heading nobody stamped. Such a character, and a line break in <who> or
<what>, is refused before anything is written; line ends arriving as CRLF are read as LF. So is every other
control character but a tab, and DEL: an escape clears a terminal's screen for whoever reads the journal there,
and a NUL makes git read the whole journal as binary.

HOW THIS IS ENFORCED (std-vocab 20.0, `journal.heading: stamped`). Every heading this tool writes is also
recorded in the clone's git directory (`.git/daftar/journal-stamps`), and the gate refuses a heading a commit
adds that is not recorded there. The gate cannot tell a measured moment from a remembered one by looking at
it; it can tell whether the clock-reading tool wrote it. The register is per clone and never versioned: it
proves only that THIS clone's tool stamped the heading, which is all a pre-commit hook can honestly check.

THE SAME READING DATES THE BEANS (23.0). A bean written with `as_of: now` (or `observed: now`), the form
seed/FORMS.md shows, has the day of this entry's heading written in its place, in every bean the working tree
changes and the entry names — so the day of writing is the clock's, read once, never a day typed or copied. A day the
writer typed is left as typed. `bin/dmsave.py` calls this tool, and on `--again` stamps with the entry waiting.
"""
import codecs
import datetime
import os
import re
import subprocess
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dmparse  # noqa: F401,E402 — its import sets UTF-8 on stdout and stderr, whatever the machine's code page
import dmsafe   # noqa: E402 — a stamp written into a bean is written through the edit that loses nothing

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOURNAL = os.path.join(ROOT, 'log', 'journal.md')

# Characters that str.splitlines() — and so some reader of the journal — takes for a line break, besides the line
# end itself. '\r' is not here: a CRLF or a lone CR is read as a line end, as a text-mode read reads it.
OTHER_BREAKS = {'\x0b': 'a vertical tab', '\x0c': 'a form feed', '\x1c': 'a file separator (\\x1c)',
                '\x1d': 'a group separator (\\x1d)', '\x1e': 'a record separator (\\x1e)', '\x85': 'NEL (U+0085)',
                '\u2028': 'a line separator (U+2028)', '\u2029': 'a paragraph separator (U+2029)'}
# Every other C0 control character, and DEL: none is text. An escape moves a terminal's cursor or clears its screen for
# whoever reads the journal there, and a NUL makes git read the whole journal as binary — it is what UTF-16 without
# its byte-order mark looks like once read as UTF-8, a NUL after every letter. A tab is text; a line feed separates
# the body's lines (and a CR has been read as one by then).
CONTROL_NAMES = {'\x00': 'NUL', '\x07': 'BEL', '\x08': 'a backspace', '\x1b': 'ESC', '\x7f': 'DEL'}


def stamps_path(root=ROOT):
    """The register, in the git directory every worktree of this clone shares."""
    r = subprocess.run(['git', '-C', root, 'rev-parse', '--git-common-dir'], capture_output=True, text=True,
                       encoding='utf-8')
    gd = r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else '.git'
    if not os.path.isabs(gd):
        gd = os.path.join(root, gd)
    return os.path.join(gd, 'daftar', 'journal-stamps')


def register(h, root=ROOT):
    p = stamps_path(root)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'a', encoding='utf-8', newline='\n') as fh:
        fh.write(h + '\n')


def registered(root=ROOT):
    p = stamps_path(root)
    if not os.path.exists(p):
        return set()
    return {l.rstrip('\n') for l in open(p, encoding='utf-8')}


def heading(who, what, when=None):
    """The heading form (std-vocab 10.0): `## YYYY-MM-DD HH:MM+HH:MM · who · what`."""
    when = when or datetime.datetime.now().astimezone()
    return f"## {when.isoformat(timespec='minutes').replace('T', ' ')} · {who} · {what}"


def stamp(who, what, root=ROOT):
    """A heading read from the clock and registered, for a tool that appends its own body (dmupgrade)."""
    h = heading(who, what)
    register(h, root)
    return h


def decode_body(raw):
    """Standard input's bytes as text: UTF-8 (its byte-order mark dropped), or UTF-16 where its mark says so.
    Anything else is refused — a guess in the machine's code page would write mojibake into an append-only file."""
    if raw.startswith(codecs.BOM_UTF8):
        raw = raw[len(codecs.BOM_UTF8):]
    elif raw.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        try:
            return raw.decode('utf-16')
        except UnicodeDecodeError as e:
            raise SystemExit(f"dmjournal: standard input begins as UTF-16 and is not ({e.reason}); nothing written")
    try:
        return raw.decode('utf-8')
    except UnicodeDecodeError as e:
        raise SystemExit(f"dmjournal: standard input is not UTF-8 (byte {e.start}: {raw[e.start:e.start + 1]!r}) — "
                         f"nothing written. Save the entry as UTF-8, or pass it with --body \"…\"")


def refuse_breaks(label, text, line_ends_too=False):
    """Refuse a character that would make one written line read as two to some reader, and every other control
    character but a tab (and, in the body, the line feed between its lines)."""
    for ch, name in OTHER_BREAKS.items():
        if ch in text:
            raise SystemExit(f"dmjournal: {label} holds {name}, which some readers take for a line break — "
                             f"nothing written. Write it as an ordinary line end, or leave it out")
    if line_ends_too and ('\n' in text or '\r' in text):
        raise SystemExit(f"dmjournal: {label} holds a line break — it is one line of the heading; nothing written")
    # every character Unicode calls a control (Cc: C0, DEL and C1 — U+009B is a terminal's 8-bit CSI), but a tab and
    # the body's line feed
    bad = next((ch for ch in text if unicodedata.category(ch) == 'Cc' and ch not in '\t\n'), None)
    if bad == '\x00':
        raise SystemExit(f"dmjournal: {label} holds NUL (\\x00), a control character — it looks like UTF-16 without "
                         f"its byte-order mark, a NUL after every letter; nothing written. Save the entry as UTF-8, "
                         f"or pass it with --body \"…\"")
    if bad is not None:
        raise SystemExit(f"dmjournal: {label} holds {CONTROL_NAMES.get(bad, 'U+%04X' % ord(bad))}, a control character "
                         f"and not text — a terminal acts on it (a bell, a cursor moved, a screen cleared) for whoever "
                         f"reads the journal there; nothing written. Leave it out")
    try:
        text.encode('utf-8')
    except UnicodeEncodeError:
        raise SystemExit(f"dmjournal: {label} holds a character that is not text (an undecodable byte) — "
                         f"nothing written")


def append(who, what, body):
    # A heading is read back as a line with its ends trimmed; a <who> or <what> ending in a space would be registered
    # as one heading and read as another, and refused as unstamped.
    who, what = who.strip(), what.strip()
    if not who or not what:
        raise SystemExit("dmjournal: <who> and <what> are both needed — who wrote the entry, and one line saying what")
    body = body.replace('\r\n', '\n').replace('\r', '\n').rstrip('\n')
    if not body.strip():
        raise SystemExit("dmjournal: the entry has no body — what was done, and why, is the point of it")
    if '\n## ' in '\n' + body:
        raise SystemExit("dmjournal: the body contains a `## ` line — leave the heading out: this tool writes it, "
                         "from the clock, above the body (one entry per call)")
    refuse_breaks('<who>', who, line_ends_too=True)
    refuse_breaks('<what>', what, line_ends_too=True)
    refuse_breaks('the body', body)
    text = open(JOURNAL, encoding='utf-8').read()
    h = stamp(who, what)
    # STAMPED BEFORE THE ENTRY IS WRITTEN: a document that cannot be stamped is reported, and the entry is still written
    # once — a run that failed after appending would be run again, and append it twice
    for p in stamp_now(h, f"{what}\n{body}"):
        print(dmparse.said(f"dmjournal: {p}: `now` written as {h[3:13]}, the day of this entry"), file=sys.stderr)
    entry = ('' if text.endswith('\n\n') else ('\n' if text.endswith('\n') else '\n\n')) + h + '\n' + body + '\n'
    with open(JOURNAL, 'a', encoding='utf-8', newline='\n') as fh:
        fh.write(entry)
    return h


# THE DAY OF WRITING IS THE CLOCK'S (23.0, `provenance_record.as_of: stamped`). The forms show `as_of: now`: the writer
# never types the day of writing, because measured writers typed the nearest date in view instead — the example's, or
# one read in another bean. This tool reads the clock once, for the heading; the same reading is the day every `now`
# in a stamp position becomes. Only a bare `now` (or a quoted one) that is the whole value of `as_of` or `observed`.
NOW = re.compile(r'(?<![\w-])((?:as_of|observed):[ \t]*)(["\']?)now\2(?=[ \t]*(?:[,}\]#\r\n]|$))', re.M)
STAMPED = ('beans/', 'mappings/')


def stamp_now(h, text=None, root=None):
    """Write the day of heading `h` in place of every `now` in a stamp position of the front matter of each document
    under beans/ or mappings/ that the working tree changes — and, given the entry's `text`, that the entry names (the
    gate asks an entry to name every bean it commits; one still being written, named by no entry yet, is left for its
    own). Returns the paths stamped. A document it cannot stamp is reported and left as it is: the entry is not written
    yet when this runs, so nothing is half done, and the gate names what is still `now`."""
    root = root or ROOT
    day = h[3:13]
    out = subprocess.run(['git', '-C', root, 'status', '--porcelain', '-z', '--untracked-files=all'], capture_output=True)
    done = []
    for rec in out.stdout.decode('utf-8', 'replace').split('\0'):
        p = rec[3:] if len(rec) > 3 else ''
        f = os.path.join(root, p)
        if not (p.startswith(STAMPED) and p.endswith('.md') and os.path.isfile(f)):
            continue
        bid = os.path.basename(p)[:-3]
        if text is not None and not re.search(r'(?<![\w-])' + re.escape(bid) + r'(?![\w-])', text):
            continue
        try:
            fm, _ = dmparse.split_front_matter(open(f, encoding='utf-8').read())
            if fm is None or not NOW.search(fm):
                continue

            def fix(t):
                front, _b = dmparse.split_front_matter(t)
                at = t.index(front)
                return t[:at] + NOW.sub(lambda m: m.group(1) + day, front) + t[at + len(front):]
            dmsafe.edit(f, fix)
            done.append(p)
        except Exception as e:                  # never a traceback after the heading is registered
            print(dmparse.said(f"dmjournal: {p}: its `now` left as it is — {e}"), file=sys.stderr)
    return done


def say(line):
    """Print after the write, and never fail because of it: a closed or broken pipe loses the line, not the entry.
    With no standard output at all — descriptor 1 closed before Python started, or pythonw on Windows — sys.stdout is
    None and there is nowhere to say it. Nothing here may fail: a run that reported an error after writing would be
    run again, and append the entry twice."""
    if sys.stdout is None:
        return
    try:
        print(line)
        sys.stdout.flush()
    except Exception:
        try:                                   # nothing more can reach that stream; keep the exit from trying again
            devnull = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull, sys.stdout.fileno())
        except Exception:
            pass


def main(argv):
    if len(argv) < 2 or argv[0] in ('-h', '--help'):
        print(__doc__)
        return 0 if argv and argv[0] in ('-h', '--help') else 2
    who, what = argv[0], argv[1]
    if '--body' in argv:
        i = argv.index('--body')
        # EVERY WORD AFTER --body IS A LINE OF THE BODY, up to the next option: only the first was read, and the rest
        # of a body an agent passed as one quoted line per item was dropped without a word (measured).
        j = i + 1
        while j < len(argv) and not argv[j].startswith('--'):
            j += 1
        if j == i + 1:
            print("dmjournal: --body takes the entry's body, in quotes", file=sys.stderr)
            return 2
        body = '\n'.join(argv[i + 1:j])
    else:
        stream = getattr(sys.stdin, 'buffer', None)
        if stream is None:
            print("dmjournal: there is no standard input to read the body from — pass it with --body", file=sys.stderr)
            return 2
        body = decode_body(stream.read())
    if not os.path.exists(JOURNAL):
        raise SystemExit(f"dmjournal: no {os.path.relpath(JOURNAL, ROOT)} — is this a garden?")
    say(append(who, what, body))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
