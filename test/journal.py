#!/usr/bin/env python3
"""journal — the one tool every journal heading goes through writes what it was given, on every platform.

Since std-vocab 20.0 the gate refuses a heading `bin/dmjournal.py` did not write, so every writer — a person, an
agent, a friend on Windows — writes the journal through it. The journal is append-only: an entry written wrong
cannot be taken back, only answered by another. So the tool is held here to what the page says of it:

  +  a Persian <who>, <what> and body arrive in the journal as UTF-8, byte for byte, when the machine's streams
     speak its code page (PYTHONIOENCODING=cp1252 stands in for Windows without UTF-8 mode, where a piped or
     redirected stream is encoded in the ANSI code page) — through standard input and through --body alike;
  +  the heading is printed after the write, as UTF-8, and a closed pipe does not turn a written entry into a
     failure that invites a second run and a duplicate entry;
  +  a byte-order mark is dropped, CRLF is read as LF, and UTF-16 with its mark (what Windows PowerShell 5.1's `>`
     writes) is read as UTF-16;
  -  bytes that are not UTF-8 are refused, and NOTHING is written or registered — never guessed in a code page;
  -  a body carrying its own `## ` line is refused with the reason (leave it out: the tool writes it);
  -  a character some reader takes for a line break (\\x0b, \\x0c, \\x1c-\\x1e, NEL, U+2028, U+2029) is refused, and
     a line break in <who> or <what>: one written line must stay one line to every reader.

And every tool that prints imports dmparse, which is where the UTF-8 streams are set for all of them.

Run: python3 test/journal.py   (0 = green).  ~2s.
"""
import codecs, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
results = []


def check(name, ok, detail=''):
    ok = bool(ok)
    results.append(ok)
    print(("PASS " if ok else "*** FAIL *** ") + name + (f"  [{str(detail)[:500]}]" if detail and not ok else ''))


TMP = tempfile.mkdtemp(prefix='dmjournal-')
G = os.path.join(TMP, 'garden-a')
shutil.copytree(os.path.join(ROOT, 'bin'), os.path.join(G, 'bin'), ignore=shutil.ignore_patterns('__pycache__'))
os.makedirs(os.path.join(G, 'log'))
JP = os.path.join(G, 'log', 'journal.md')
with open(JP, 'w', encoding='utf-8', newline='\n') as fh:
    fh.write('# garden-a — journal\n\nAppend-only.\n')
subprocess.run(['git', 'init', '-q', G], check=True)
TOOL = os.path.join(G, 'bin', 'dmjournal.py')

# A MACHINE WHOSE STREAMS ARE NOT UTF-8. PYTHONUTF8 would hide exactly what is tested, so it is taken out.
ENV = {k: v for k, v in os.environ.items() if k not in ('PYTHONUTF8', 'PYTHONIOENCODING')}
ENV['PYTHONIOENCODING'] = 'cp1252'

WHO, WHAT = 'سام', 'هدیه برای علی'
BODY = '- action: added [[gift]] — a gift for علی.\n- why: سام asked for it.'


def journal():
    return open(JP, 'rb').read()


def stamps():
    sys.path.insert(0, os.path.join(G, 'bin'))
    import dmjournal
    p = dmjournal.stamps_path(G)
    return open(p, 'rb').read() if os.path.exists(p) else b''


def tool(*args, stdin=None, stdout=subprocess.PIPE):
    return subprocess.run([sys.executable, TOOL] + list(args), input=stdin, stdout=stdout, stderr=subprocess.PIPE,
                          env=ENV, cwd=G)


def headings(b):
    return [l for l in b.decode('utf-8').split('\n') if l.startswith('## ')]


# ---- + through standard input, a Persian entry on a cp1252 machine --------------------------------------------------
before = journal()
r = tool(WHO, WHAT, stdin=(BODY + '\n').encode('utf-8'))
after = journal()
added = after[len(before):]
check("standard input on a cp1252 machine: a Persian entry is written, exit 0", r.returncode == 0,
      r.stderr.decode('utf-8', 'replace'))
check("...the body is in the journal as UTF-8, byte for byte — no mojibake",
      after.startswith(before) and added.endswith(('\n' + BODY + '\n').encode('utf-8')), added[-200:])
_h = headings(added)
check("...under one heading naming <who> and <what> as given", len(_h) == 1 and _h[0].endswith(f' · {WHO} · {WHAT}'), _h)
check("...the heading is registered as written, so the gate knows the tool wrote it",
      _h and (_h[0] + '\n').encode('utf-8') in stamps(), stamps()[-200:])
check("...and it is printed after the write, in UTF-8", _h and r.stdout.decode('utf-8', 'replace').strip() == _h[0],
      r.stdout[:200])

# ---- + through --body, as PowerShell passes it -------------------------------------------------------------------
before = journal()
r = tool(WHO, WHAT, '--body', BODY)
added = journal()[len(before):]
check("--body on a cp1252 machine, its output read through a pipe: written, exit 0, no traceback",
      r.returncode == 0 and b'Traceback' not in r.stderr, r.stderr.decode('utf-8', 'replace')[-300:])
check("...exactly one entry, the body byte for byte", len(headings(added)) == 1
      and added.endswith(('\n' + BODY + '\n').encode('utf-8')), added[-200:])

# ---- + a closed pipe after the write is not a failure --------------------------------------------------------------
_rd, _wr = os.pipe()
os.close(_rd)
before = journal()
try:
    r = tool(WHO, 'a closed pipe', '--body', '- action: written whatever becomes of the heading line.', stdout=_wr)
finally:
    os.close(_wr)
added = journal()[len(before):]
check("the heading's line cannot be printed (a closed pipe): the entry is written once and the exit is 0",
      r.returncode == 0 and len(headings(added)) == 1 and b'Traceback' not in r.stderr,
      (r.returncode, r.stderr.decode('utf-8', 'replace')[-300:]))

# ---- + a byte-order mark, CRLF, UTF-16 ----------------------------------------------------------------------------
before = journal()
r = tool('sam', 'a BOM and CRLF', stdin=codecs.BOM_UTF8 + '- action: one.\r\n- why: two — دو.\r\n'.encode('utf-8'))
added = journal()[len(before):]
check("a UTF-8 byte-order mark is dropped and CRLF is read as LF",
      r.returncode == 0 and codecs.BOM_UTF8 not in added and b'\r' not in added
      and added.endswith('\n- action: one.\n- why: two — دو.\n'.encode('utf-8')), added[-120:])
before = journal()
r = tool('sam', 'UTF-16', stdin='- action: written by PowerShell 5.1 with `>` — علی.\r\n'.encode('utf-16'))
added = journal()[len(before):]
check("UTF-16 with its mark (Windows PowerShell 5.1's `>`) is read as UTF-16",
      r.returncode == 0 and added.endswith('\n- action: written by PowerShell 5.1 with `>` — علی.\n'.encode('utf-8')),
      (r.stderr.decode('utf-8', 'replace'), added[-120:]))


# ---- - refused, and nothing written ------------------------------------------------------------------------------
def refused(name, args, stdin=None, says=''):
    j0, s0 = journal(), stamps()
    r = tool(*args, stdin=stdin)
    err = r.stderr.decode('utf-8', 'replace')
    check(name, r.returncode != 0 and journal() == j0 and stamps() == s0 and says in err and 'Traceback' not in err,
          (r.returncode, err[-300:]))


refused("bytes that are not UTF-8 (a cp1252 dash) are refused, and nothing is written or registered",
        ['sam', 'code page'], stdin='- action: added [[x]] – in cp1252.\n'.encode('cp1252'), says='not UTF-8')
refused("a body with its own `## ` line is refused, saying to leave the heading out",
        ['sam', 'x'], stdin=b'## 2026-09-17 09:30+03:00 \xc2\xb7 sam \xc2\xb7 x\n- action: x\n', says='leave the heading out')
for _ch in ('\x0b', '\x0c', '\x1c', '\x1d', '\x1e', '\x85', '\u2028', '\u2029'):
    refused(f"a body holding {_ch!r}, which splitlines() reads as a line break, is refused",
            ['sam', 'x', '--body', f'- action: a note.{_ch}## 2026-09-17 09:30+03:00 · ada · typed'], says='line break')
refused("a line break in <what> is refused: it is one line of the heading",
        ['sam', 'x\n## 2026-09-17 09:30+03:00 · ada · typed', '--body', '- action: x'], says='line break')
refused("--body with nothing after it is a usage error", ['sam', 'x', '--body'], says='--body')

# ---- every tool that prints speaks UTF-8 ---------------------------------------------------------------------------
# dmparse sets the streams once, for every tool that imports it; a tool that prints and never imports it writes in
# the code page, and its first `—` or Persian letter ends the run in a traceback (dmgeo did, with a Persian argument).
_silent = []
for _f in sorted(os.listdir(os.path.join(ROOT, 'bin'))):
    if not re.match(r'^dm[a-z]*\.py$', _f) or _f == 'dmparse.py':
        continue
    _src = open(os.path.join(ROOT, 'bin', _f), encoding='utf-8').read()
    if re.search(r'\bprint\(', _src) and not re.search(r'(?m)^\s*import [^\n]*\bdmparse\b|^\s*from dmparse import', _src):
        _silent.append(_f)
check("every tool that prints imports dmparse, so its output is UTF-8 on every platform", not _silent, _silent)
r = subprocess.run([sys.executable, os.path.join(G, 'bin', 'dmgeo.py'), 'مکان'], capture_output=True, env=ENV)
check("...dmgeo, given a Persian position on a cp1252 machine, refuses it in words, not a traceback",
      r.returncode == 1 and 'مکان' in r.stdout.decode('utf-8', 'replace') and b'Traceback' not in r.stderr,
      r.stderr.decode('utf-8', 'replace')[-300:])

shutil.rmtree(TMP, ignore_errors=True)
print(f"\njournal: {sum(results)}/{len(results)} checks passed")
sys.exit(0 if all(results) else 1)
