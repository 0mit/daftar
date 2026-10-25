"""guards — what an agent's own door checks before the agent acts: the law's closed table of guards (core/law/guards.yaml),
one function a row, each held to the row's vectors.

    from core import guards
    guards.refusal(law, 'one-text-one-parser', {}, command='bash -c ...')      # None, or a Refusal
    guards.refusal(law, 'shell-is', {'shell': 'bash', 'floor': '5.0'}, shell=('zsh', '5.9', '/bin/zsh'))
    guards.refusal(law, 'no-memory-write', {}, path='/home/u/.claude/projects/x/memory/a.md',
                   memory=['/home/u/.claude/projects/*/memory'])
    guards.problems(law)                    # the table closed: a function a row, a row a function, every vector holds
    guards.operand_problems(law, row, x)    # an instruction's operand, as its guard takes it (rule `measured`)
    guards.holding(law, instructions)       # {guard: [Instruction]}: the guards an instruction holds, lifted or not
    guards.acts(command, host, cwd, home)   # [Act]: each simple command, the host it runs on, the folder it runs in
    guards.written(command, cwd, home)      # the paths a command's redirections write, where they can be placed

A guard reads one thing of the act, as its row says (`reads`): `command`, the text a shell is given; `shell`, the
shell the agent's harness runs its commands in — (name, version, path), found by the harness's own rule, which is the
harness's and is read by the door that runs in it (bin/hook.py); or `path`, the path a write targets — a write tool's
file, or a shell redirection's target. Beside what it reads, the door gives what only it can know (`ctx`): the machine
it runs on (`host`), and for a path the garden's working copies (`copies`), the worktree of the agent's own session
(`worktree`) and the harness's memory folders (`memory`). What a guard finds is a Refusal: what was found, and what to
do instead, in plain words.

A PATH is compared as text, the same on every system: its separators written `/`, `.` and `..` taken as written, and a
Windows drive's path compared without case. The door makes it whole first (bin/hook.py), as the system resolves it.

ONE TEXT, ONE PARSER. A command is read here as the shell the garden declares reads it (bash's grammar, which sh, zsh and
Git for Windows' bash share for everything the guard looks at): its simple commands, each a list of words, each word its
parts as they were quoted; what a substitution holds, `$( … )` or backquotes, read as a command line of its own; a
heredoc's body taken whole, never read for quotes. A command whose quotes, substitutions or heredocs do not close is
refused: the shell would read it otherwise than it was written, and a door that cannot read an act fails closed."""
import collections
import fnmatch
import posixpath
import re

Refusal = collections.namedtuple('Refusal', 'found instead')

# THE INTERPRETERS the meaning of one-text-one-parser names, by how each is given its text: a shell by `-c` (fish by
# `--command` too), pwsh and powershell by `-Command`, cmd by `/c` or `/k`, python by `-c`, perl by `-e`, node by `-e` or
# `-p`, and a command for another host, ssh's, by every word after the host.
SHELLS = ('bash', 'sh', 'zsh', 'dash', 'ksh', 'fish')
PYTHON = re.compile(r'^(?:python[0-9.]*|py)$')
SSH_TAKES = set('BbcDEeFIiJLlmOopQRSWw')         # ssh's options that take an argument (ssh(1))
HEREDOC = re.compile(r"<<(?!<)-?\s*['\"\\]?[A-Za-z_]")

# WHAT TO DO INSTEAD, by what the text was meant for: the file the agent writes with its file tools, and how it is passed
INSTEAD = {
    'shell': "write the script with the file tools and run it: `bash script.sh`",
    'python': "write the code with the file tools and run it: `python3 script.py`, or `python3 - < script.py`",
    'perl': "write the script with the file tools and run it: `perl script.pl`",
    'node': "write the script with the file tools and run it: `node script.js`",
    'powershell': "write the script with the file tools and run it: `powershell -File script.ps1` (or -EncodedCommand)",
    'cmd': "write the batch file with the file tools and run it: `cmd /c script.cmd`",
    'ssh': "write the script with the file tools and give it to the host's bash on standard input: "
           "`ssh <host> bash -s < script.sh`",
    'body': "write the entry with the file tools and give it on standard input: "
            "`python3 bin/save.py \"<who>\" \"<what>\" < entry.md`",
    'text': "write the text with the file tools and pass the file; a value a command prints goes into a variable first "
            "(`v=$(cmd)`), then `\"$v\"`",
    'unclosed': "write the command with the file tools as a script, and run the script: `bash script.sh`",
    'cmdline': "count or name the processes: `pgrep -c <name>`, `pgrep -l <name>`, or `ps` with its columns named "
               "and none the command line (`ps -o pid,etime,comm`)",
    'column': "count it, and select it never: `SELECT COUNT(*) FROM <table> WHERE <column> LIKE '<prefix>%'`; name "
              "the other columns one by one, never `*`",
    'credential': "describe its shape alone — `ls -l`, `stat`, `wc -l`, `file`, a checksum, or a search's count "
                  "(`grep -c`) — and where its words must be seen, give the gardener the command that shows them, unrun",
    'worktree': "write it in this session's worktree, <worktree>: closing the session brings it into the main copy "
                "(`python3 bin/session.py close <slug>`)",
    'memory': "write it into the garden, where every agent after you reads it: a fact as a statement on the bean it is "
              "about (seed/FORMS.md), saved with its entry (`python3 bin/save.py`); a standing instruction as a clause "
              "of agents-work, which the gardener says; and where the work stands is read, never stored "
              "(`python3 bin/now.py`)",
}


class Unclosed(ValueError):
    """A quote, a substitution or a heredoc that does not close; `partial`, the commands read before it."""
    partial = ()


class Word:
    """One word of a simple command: its parts as they were quoted, each (quoting, text) — quoting '' (none), "'", '"',
    or "$'" (its text as the shell gives it); and whether a double-quoted part holds a backquote or `$(` the shell runs."""

    def __init__(self):
        self.parts, self.runs_in_quotes = [], False

    def add(self, q, text):
        if self.parts and self.parts[-1][0] == q == '':
            self.parts[-1] = ('', self.parts[-1][1] + text)
        else:
            self.parts.append((q, text))

    @property
    def plain(self):
        """The word's text where no part of it is quoted (a command's name, an option), else None."""
        return self.parts[0][1] if len(self.parts) == 1 and self.parts[0][0] == '' else None


class Command:
    """A simple command: its words, and among them each redirection's target with its operator (`>`, `>>`, `<` …)."""

    def __init__(self):
        self.words, self.redirs = [], []


_ANSI = {'n': '\n', 't': '\t', 'r': '\r', "'": "'", '"': '"', '\\': '\\', 'a': '\a', 'b': '\b', 'e': '\x1b',
         'E': '\x1b', 'f': '\f', 'v': '\v'}


class _Scan:
    def __init__(self, s):
        self.s, self.i, self.out = s, 0, []

    def peek(self, k=0):
        j = self.i + k
        return self.s[j] if j < len(self.s) else ''

    def run(self):
        """[Command]: every simple command of the line, those a substitution holds among them; Unclosed, holding the
        commands read before it, where the line does not close."""
        self.cmd, self.word, self.redir = Command(), None, None
        try:
            self.line()
        except Unclosed as e:
            self.end_cmd()
            e.partial = list(self.out)
            raise
        self.end_cmd()
        return self.out

    def end_word(self):
        if self.word is not None:
            self.cmd.words.append(self.word)
            if self.redir:                               # the word a redirection names: a word too, as it always was
                self.cmd.redirs.append((self.redir, self.word))
                self.redir = None
            self.word = None

    def end_cmd(self):
        self.end_word()
        if self.cmd.words:
            self.out.append(self.cmd)
        self.cmd, self.redir = Command(), None

    def line(self):
        s, heredocs = self.s, []
        while self.i < len(s):
            c = s[self.i]
            if c in ' \t':
                self.end_word()
                self.i += 1
            elif c == '\n':
                self.end_cmd()
                self.i += 1
                for strip, delim in heredocs:
                    self.body(strip, delim)
                heredocs = []
            elif c == '#' and self.word is None:
                while self.i < len(s) and s[self.i] != '\n':
                    self.i += 1
            elif c in ';&|()':
                self.end_cmd()
                self.i += 1
            elif c in '<>':
                self.end_word()
                if s.startswith('<<<', self.i):
                    self.i += 3
                elif s.startswith('<<', self.i):
                    self.i += 2
                    strip = self.peek() == '-'
                    if strip:
                        self.i += 1
                    while self.peek() in (' ', '\t'):
                        self.i += 1
                    d = self.word_alone()
                    if not d:
                        raise Unclosed("a heredoc names no word that ends it")
                    heredocs.append((strip, d))
                else:
                    j = self.i
                    self.i += 1
                    while self.peek() and self.peek() in '<>&':
                        self.i += 1
                    self.redir = s[j:self.i]
            else:
                if self.word is None:
                    self.word = Word()
                self.part(self.word)
        if heredocs:
            raise Unclosed("a heredoc is given no body")      # its body would be the lines after the command's own

    def word_alone(self):
        """The text of a heredoc's delimiter, its quotes taken off."""
        w = Word()
        while self.i < len(self.s) and self.s[self.i] not in ' \t\n;&|()<>':
            self.part(w)
        return ''.join(t for _q, t in w.parts)

    def body(self, strip, delim):
        """A heredoc's body, taken whole up to the line that ends it."""
        s = self.s
        while self.i < len(s):
            j = s.find('\n', self.i)
            line = s[self.i:] if j < 0 else s[self.i:j]
            self.i = len(s) if j < 0 else j + 1
            if (line.lstrip('\t') if strip else line) == delim:
                return
        raise Unclosed(f"the heredoc ended by `{delim}` does not end")

    def part(self, w):
        """One part of a word at the cursor, added to `w`."""
        s, c = self.s, self.s[self.i]
        if c == '\\':
            if self.peek(1) == '\n':
                self.i += 2
            else:
                w.add('', s[self.i + 1:self.i + 2])
                self.i += 2
        elif c == "'":
            j = s.find("'", self.i + 1)
            if j < 0:
                raise Unclosed("a single quote does not close")
            w.add("'", s[self.i + 1:j])
            self.i = j + 1
        elif c == '$' and self.peek(1) == "'":
            self.i += 2
            text = []
            while True:
                if self.i >= len(s):
                    raise Unclosed("a `$'` quote does not close")
                ch = s[self.i]
                if ch == "'":
                    self.i += 1
                    break
                if ch == '\\' and self.i + 1 < len(s):
                    text.append(_ANSI.get(s[self.i + 1], '\\' + s[self.i + 1]))
                    self.i += 2
                else:
                    text.append(ch)
                    self.i += 1
            w.add("$'", ''.join(text))
        elif c == '"':
            self.i += 1
            start = self.i
            while True:
                if self.i >= len(s):
                    raise Unclosed("a double quote does not close")
                ch = s[self.i]
                if ch == '"':
                    break
                if ch == '\\':
                    self.i += 2
                elif ch == '`':
                    w.runs_in_quotes = True
                    self.i = self.ticks(self.i + 1)
                elif ch == '$' and self.peek(1) == '(':
                    w.runs_in_quotes = True
                    self.i = self.closing(self.i + 2)
                elif ch == '$' and self.peek(1) == '{':
                    self.i = self.brace(self.i + 2)
                else:
                    self.i += 1
            w.add('"', s[start:self.i])
            self.i += 1
        elif c == '$' and self.peek(1) == '(':
            start = self.i
            end = self.closing(self.i + 2)
            if not s.startswith('$((', start):         # arithmetic is no command
                self.out += _Scan(s[start + 2:end - 1]).run()
            w.add('', s[start:end])
            self.i = end
        elif c == '$' and self.peek(1) == '{':
            start = self.i
            self.i = self.brace(self.i + 2)
            w.add('', s[start:self.i])
        elif c == '`':
            start = self.i
            end = self.ticks(self.i + 1)
            self.out += _Scan(s[start + 1:end - 1].replace('\\`', '`')).run()
            w.add('', s[start:end])
            self.i = end
        else:
            j = self.i
            while j < len(s) and s[j] not in ' \t\n;&|()<>\\\'"$`':
                j += 1
            if j == self.i:                              # a `$` alone
                j += 1
            w.add('', s[self.i:j])
            self.i = j

    def ticks(self, i):
        """The index after the backquote that closes one opened before `i`."""
        s = self.s
        while i < len(s):
            if s[i] == '\\':
                i += 2
            elif s[i] == '`':
                return i + 1
            else:
                i += 1
        raise Unclosed("a backquote does not close")

    def brace(self, i):
        depth, s = 1, self.s
        while i < len(s):
            if s[i] == '\\':
                i += 2
                continue
            if s[i] == '{':
                depth += 1
            elif s[i] == '}':
                depth -= 1
                if depth == 0:
                    return i + 1
            i += 1
        raise Unclosed("a `${` does not close")

    def closing(self, i):
        """The index after the `)` that closes a `$(` opened before `i`, its quotes and nested parentheses skipped."""
        depth, s = 1, self.s
        while i < len(s):
            ch = s[i]
            if ch == '\\':
                i += 2
                continue
            if ch == "'":
                j = s.find("'", i + 1)
                if j < 0:
                    raise Unclosed("a single quote does not close")
                i = j + 1
                continue
            if ch == '"':
                i += 1
                while i < len(s) and s[i] != '"':
                    i += 2 if s[i] == '\\' else 1
                if i >= len(s):
                    raise Unclosed("a double quote does not close")
                i += 1
                continue
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
                if depth == 0:
                    return i + 1
            i += 1
        raise Unclosed("a `$(` does not close")


def scan(command):
    """[Command] of a command line, as the garden's shell reads it; Unclosed where it does not close."""
    return _Scan(str(command)).run()


def _name(w):
    t = w.plain
    if t is None:
        return None
    t = re.split(r'[\\/]', t)[-1].lower()
    return t[:-4] if t.endswith('.exe') else t


def _kind(name):
    if name in SHELLS:
        return 'shell'
    if PYTHON.match(name or ''):
        return 'python'
    return {'perl': 'perl', 'node': 'node', 'pwsh': 'powershell', 'powershell': 'powershell', 'cmd': 'cmd',
            'ssh': 'ssh'}.get(name)


# PowerShell's parameters that take a value (about_Pwsh, about_PowerShell_exe), each matched by a prefix of its name
PS_VALUED = ('-executionpolicy', '-ep', '-windowstyle', '-outputformat', '-inputformat', '-configurationname',
             '-workingdirectory', '-wd', '-version', '-psconsolefile', '-custompipename', '-settingsfile')
SHELL_VALUED = ('-o', '+o', '-O', '+O')                 # a shell's options that take a value (`-o pipefail`)


def _texts(kind, name, rest):
    """The words of `rest` an interpreter of `kind` reads as its text: none where it is given a file to run."""
    n = 0
    while n < len(rest):
        w = rest[n]
        t = w.plain
        first = w.parts[0][1] if w.parts and w.parts[0][0] == '' else ''
        if kind == 'ssh':
            if t is not None and t.startswith('-') and len(t) > 1:
                n += 2 if t[-1] in SSH_TAKES and all(ch not in SSH_TAKES for ch in t[1:-1]) else 1
                continue
            return rest[n + 1:]                            # past the host: the other host's shell's text
        if kind == 'cmd':
            if t is not None and t.lower() in ('/c', '/k'):
                return rest[n + 1:]
            n += 1
            continue
        if kind == 'powershell':
            lt = (t or '').lower()
            if len(lt) > 1 and lt.startswith('-') and '-command'.startswith(lt):
                return rest[n + 1:]
            if len(lt) > 2 and any(p.startswith(lt) for p in PS_VALUED):
                n += 2
                continue
            if lt.startswith('-f') or lt.startswith('-e'):
                return []                                  # a file to run, or the text encoded: no quotes to read
            if lt.startswith('-'):
                n += 1
                continue
            return rest[n:] if name == 'powershell' else []   # powershell's first word is a command, pwsh's a file
        if t == '--':
            return []
        if t is not None and kind in ('node', 'shell') and t.split('=', 1)[0] in (
                ('--eval', '--print') if kind == 'node' else ('--command',) if name == 'fish' else ()):
            return [w] if '=' in t else rest[n + 1:n + 2]
        if kind == 'shell' and t in SHELL_VALUED:
            n += 2
            continue
        if first[:1] in ('-', '+') and not first.startswith('--') and len(first) > 1:
            flag = {'shell': 'c', 'python': 'c', 'perl': 'eE', 'node': 'ep'}[kind]
            k = next((j for j, ch in enumerate(first[1:], 1) if ch in flag), None)
            if k is not None:
                if k < len(first) - 1 or len(w.parts) > 1:
                    return [w]                             # the text written on to its option
                if kind != 'perl':
                    return rest[n + 1:n + 2]
                return [rest[j + 1] for j in range(n, len(rest) - 1) if (rest[j].plain or '')[:1] == '-'
                        and any(ch in flag for ch in (rest[j].plain or '')[1:])]   # each -e one line of the program
            if kind == 'python' and first == '-m':
                return []                                  # a module: what follows is its arguments
            n += 2 if kind == 'python' and first in ('-W', '-X') else 1
            continue
        if t is not None and t.startswith('--'):
            n += 1
            continue
        return []                                          # a script's name: what follows is its arguments
    return []


def _found_in(q, text):
    """What a quoted part holds that another interpreter would read: a line break, a heredoc, a backquote, `$(` or the
    other quote; or None."""
    if '\n' in text:
        return "a line break"
    if HEREDOC.search(text):
        return "a heredoc"
    if '`' in text:
        return "a backquote"
    if '$(' in text:
        return "`$(`"
    if (q in ("'", "$'") and '"' in text) or (q == '"' and "'" in text):
        return "the other quote"
    return None


QUOTING = {"'": 'single-quoted', '"': 'double-quoted', "$'": "`$'`-quoted"}


def one_text_one_parser(operand, command):
    """Refusal or None: text meant for another interpreter, carried inside a command's quotes."""
    unclosed = None
    try:
        cmds = scan(command)
    except Unclosed as e:
        cmds, unclosed = e.partial, e
    for c in cmds:
        names = [_name(w) for w in c.words]
        at = next((n for n, nm in enumerate(names) if _kind(nm)), None)
        if at is not None:
            kind, name = _kind(names[at]), names[at]
            for w in _texts(kind, name, c.words[at + 1:]):
                for q, text in w.parts:
                    what = _found_in(q, text) if q else None
                    if what:
                        to = "the other host's shell" if kind == 'ssh' else f"`{name}`"
                        return Refusal(f"{to} is given its text as a {QUOTING[q]} argument that holds {what}",
                                       INSTEAD[kind])
        for w in c.words:
            if w.runs_in_quotes:
                body = any((x.plain or '').endswith('save.py') for x in c.words) and \
                    any(x.plain == '--body' for x in c.words)
                return Refusal("a double-quoted argument holds a backquote or `$(`, which the shell runs before the "
                               "command sees the text", INSTEAD['body' if body else 'text'])
    if unclosed is not None:
        return Refusal(f"the command does not close ({unclosed}), so the shell would read it otherwise than it is "
                       f"written", INSTEAD['unclosed'])
    return None


def version_of(text):
    """(int, …) of the first version written in `text`, or None."""
    m = re.search(r'([0-9]+(?:\.[0-9]+)*)', str(text or ''))
    return tuple(int(x) for x in m.group(1).split('.')) if m else None


def shell_is(operand, shell):
    """Refusal or None: the shell the harness runs commands in, (name, version, path), against the instruction's."""
    want, floor = str(operand.get('shell') or ''), operand.get('floor')
    name, version, path = (list(shell or ()) + ['', '', ''])[:3]
    if not name:
        return Refusal("no shell this harness would run its commands in was found", None)
    runs = ' '.join(x for x in (name, version, f"({path})" if path else '') if x)
    if name != want:
        return Refusal(f"this harness runs its commands in {runs}, not {want}", None)
    if floor is not None:
        have, low = version_of(version), version_of(floor)
        if have is None or (low is not None and _padded(have, low) < _padded(low, have)):
            return Refusal(f"this harness runs its commands in {runs}, below the floor {floor}", None)
    return None


def _padded(a, b):
    return tuple(a) + (0,) * max(0, len(b) - len(a))


# ------------------------------------------------------------------------ each command, where it runs, and what it writes
def text(w):
    """A word's text as the command it is given to receives it, its quotes taken off (a substitution as written)."""
    return ''.join(t for _q, t in w.parts)


def _listed(x):
    return x if isinstance(x, list) else [] if x is None else [x]


# THE COMMANDS THAT RUN ANOTHER, each with its options that take a value — as letters (`sudo -u web`) and as words —
# and how many words it takes before the command it runs (`timeout 10`): the command a line runs is read past them
WRAPPERS = {'sudo': ('ugpCDrthUT', ('--user', '--group', '--host', '--prompt', '--chdir', '--role', '--type'), 0),
            'doas': ('uC', (), 0), 'env': ('uCS', ('--unset', '--chdir', '--split-string'), 0),
            'nice': ('n', ('--adjustment',), 0), 'ionice': ('cnp', ('--class', '--classdata', '--pid'), 0),
            'nohup': ('', (), 0), 'time': ('fo', ('--format', '--output'), 0), 'command': ('', (), 0),
            'exec': ('a', (), 0), 'timeout': ('sk', ('--signal', '--kill-after'), 1),
            'stdbuf': ('ioe', ('--input', '--output', '--error'), 0),
            'xargs': ('nIdLPsEa', ('--max-args', '--replace', '--delimiter', '--max-lines', '--max-procs', '--max-chars',
                                   '--eof', '--arg-file'), 0),
            'watch': ('nd', ('--interval', '--differences'), 0)}
ASSIGNMENT = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*=')


def head(c):
    """The index of the word a simple command runs — past its assignments (`LANG=C`) and the commands that run another
    (`sudo`, `env`, `nice`, `timeout`, `xargs`, `watch` …) — or None where it runs none."""
    ws, n = c.words, 0
    while n < len(ws):
        t = ws[n].plain
        if t is not None and ASSIGNMENT.match(t):
            n += 1
            continue
        name = _name(ws[n])
        if name not in WRAPPERS:
            return n
        letters, longs, positional = WRAPPERS[name]
        n += 1
        while n < len(ws):
            t = ws[n].plain or ''
            if t == '--':
                n += 1
                break
            if t.startswith('--'):
                n += 2 if t in longs else 1
            elif t.startswith('-') and len(t) > 1:
                n += 2 if t[-1] in letters and all(ch not in letters for ch in t[1:-1]) else 1
            elif name == 'env' and ASSIGNMENT.match(t):
                n += 1
            else:
                break
        n += positional
    return None


def ssh_parts(words):
    """(host, [Word]) of the words after `ssh`: the host it is given, its user and port aside, and the words of the
    command it gives that host's shell; (None, []) where it names no host."""
    n = 0
    while n < len(words):
        t = words[n].plain
        if t is not None and t.startswith('-') and len(t) > 1:
            n += 2 if t[-1] in SSH_TAKES and all(ch not in SSH_TAKES for ch in t[1:-1]) else 1
            continue
        dest = text(words[n])
        m = re.match(r'^(?:ssh://)?(?:[^@/]*@)?(\[[^\]]*\]|[^:/]+)', dest)
        return (m.group(1).strip('[]') if m else dest), words[n + 1:]
    return None, []


# AN ACT OF A LINE: a simple command, the host it runs on (the door's own, or the one an `ssh` gives it to), the folder
# it runs in where the line lets it be placed, and whether it runs on another host
Act = collections.namedtuple('Act', 'cmd host cwd remote')


def acts(command, host=None, cwd=None, home=None, remote=False, depth=0):
    """[Act]: every simple command of a line, those a substitution holds among them, each with the host it runs on —
    the door's own (`host`), or the host an `ssh` gives its text to, that text read again as the other host's shell
    reads it — and the folder it runs in where a `cd` before it on the line lets it be placed, else None."""
    try:
        cmds = scan(command)
    except Unclosed as e:
        cmds = e.partial
    out = []
    for c in cmds:
        out.append(Act(c, host, cwd, remote))
        h = head(c)
        if h is None:
            continue
        name, rest = _name(c.words[h]), c.words[h + 1:]
        if name in ('cd', 'pushd'):
            args = [w for w in rest if (w.plain or '') not in ('-L', '-P', '-e', '-@', '--')]
            cwd = place(text(args[0]), cwd, home) if args else home
        elif name == 'ssh' and depth < 8:
            to, words = ssh_parts(rest)
            if to and words:
                out += acts(' '.join(text(w) for w in words), to, None, None, True, depth + 1)
    return out


def _absolute(p):
    return str(p).startswith(('/', '\\')) or bool(re.match(r'^[A-Za-z]:[\\/]', str(p)))


def norm(p):
    """A path as text: `/` its separator, `.` and `..` taken as written, a Windows drive's path without case."""
    s = str(p).replace('\\', '/')
    if not s:
        return s
    drive = re.match(r'^([A-Za-z]):(/.*)?$', s)
    if drive:
        return (drive.group(1) + ':' + posixpath.normpath(drive.group(2) or '/')).lower()
    return posixpath.normpath(s)


def under(p, folder):
    """True where the path `p` is the folder or lies under it (both as `norm` writes them)."""
    return p == folder or p.startswith(folder.rstrip('/') + '/')


def place(t, cwd, home):
    """A path as a line writes it, made whole: `~` and `$HOME` read as the home folder, a relative path against `cwd`;
    None where that cannot be done without running the shell (a variable, `cd -`, another user's `~`)."""
    for h in ('~', '$HOME', '${HOME}'):
        if t == h or t.startswith(h + '/'):
            if not home:
                return None
            t = str(home) + t[len(h):]
            break
    if not t or '$' in t or '`' in t or t == '-' or t.startswith('~'):
        return None
    if not _absolute(t):
        if not cwd:
            return None
        t = str(cwd).rstrip('/\\') + '/' + t
    return norm(t)


def written(command, cwd=None, home=None):
    """[path]: what a command line's redirections write on this machine (`>`, `>>`, `&>`, `<>`), each made whole; a
    target that cannot be placed without running the shell is not among them."""
    out = []
    for a in acts(command, None, cwd, home):
        if a.remote:
            continue
        for op, w in a.cmd.redirs:
            t = text(w)
            if '>' not in op or (op.endswith('&') and (t.isdigit() or t == '-')):
                continue
            p = place(t, a.cwd, home)
            if p:
                out.append(p)
    return out


def _flags(t, valued=''):
    """The option letters of a short cluster (`-af`), up to the first that takes a value."""
    out = ''
    for ch in t[1:]:
        out += ch
        if ch in valued:
            break
    return out


# ------------------------------------------------------------------------------------- process-command-line
PGREP_VALUED = 'dgGPstuUFr'
COMMAND_LINE = ('args', 'cmd', 'command', 'cmdline')     # ps's columns that print a process's command line


def _ps_named(rest):
    """True where a `ps` names every column it prints (`-o`, `o`, `--format`) and none is the command line."""
    fmts, adds, n = [], False, 0
    while n < len(rest):
        t = rest[n]
        nxt = rest[n + 1] if n + 1 < len(rest) else ''
        if t in ('-o', 'o', '--format'):
            fmts.append(nxt)
            n += 2
            continue
        if t.startswith('--format='):
            fmts.append(t[len('--format='):])
        elif t.startswith('-o') and len(t) > 2:
            fmts.append(t[2:])
        elif t in ('-O', 'O') or t.startswith('-O'):
            adds = True                                  # columns added to those it prints by default
        elif re.fullmatch(r'-?[A-Za-z]*[oO]', t):         # a cluster ending at its format: `-eo`, `axo`
            fmts.append(nxt)
            adds = adds or t.endswith('O')
            n += 2
            continue
        n += 1
    cols = [c.split('=')[0].split(':')[0].lower() for f in fmts for c in re.split(r'[,\s]+', f) if c]
    return bool(cols) and not adds and not any(c in COMMAND_LINE for c in cols)


def _prints_cmdline(c):
    """What in a simple command prints another process's command line, said, or None."""
    h = head(c)
    if h is not None and _name(c.words[h]) == 'ssh':
        return None                                  # its words are the other host's command, an act of their own
    for w in c.words:
        t = text(w).replace('\\', '/')
        if t.endswith('/cmdline'):
            parent = t[:-len('/cmdline')].rstrip('/').split('/')[-1]
            if parent not in ('proc', 'self', 'thread-self'):      # the kernel's own, and a reader's own
                return f"a read of `{t}`"
    if h is None:
        return None
    name, rest = _name(c.words[h]), [text(w) for w in c.words[h + 1:]]
    if name == 'pgrep':
        flags = ''.join(_flags(t, PGREP_VALUED) for t in rest if t.startswith('-') and not t.startswith('--'))
        full = 'a' in flags or '--list-full' in rest
        bsd = ('l' in flags or '--list-name' in rest) and ('f' in flags or '--full' in rest)
        if full or bsd:
            return f"`pgrep {' '.join(rest)}`"
    if name == 'ps' and not _ps_named(rest):
        return f"`{' '.join(['ps'] + rest)}`"
    return None


def _on(host, hosts):
    """True where `host` is one of `hosts`, by its whole name or its first label (`db1.example.com`, `db1`)."""
    if not host:
        return False
    h = str(host).lower()
    names = {str(x).lower() for x in hosts}
    return h in names or h.split('.')[0] in {x.split('.')[0] for x in names}


def process_command_line(operand, command, ctx):
    """Refusal or None: a command that prints another process's command line on a host the operand names."""
    hosts = _listed(operand.get('hosts'))
    for a in acts(command, ctx.get('host'), ctx.get('cwd'), ctx.get('home')):
        if _on(a.host, hosts):
            what = _prints_cmdline(a.cmd)
            if what:
                return Refusal(f"{what} prints another process's command line on {a.host}, a host the instruction "
                               f"names", INSTEAD['cmdline'])
    return None


# ------------------------------------------------------------------------------------------------ secret-column
SELECT = re.compile(r'\bselect\b', re.I)
FROM = re.compile(r'\bfrom\b', re.I)
COUNT = re.compile(r'\bcount\s*\(', re.I)
STAR = re.compile(r'(?:^|[\s,.(])\*(?=[\s,)]|$)')


def _select_lists(s):
    """(the list, the rest of its statement) of each SELECT a text holds, a subquery's among them."""
    for m in SELECT.finditer(s):
        j, depth = m.end(), 0
        while j < len(s):
            ch = s[j]
            if ch == '(':
                depth += 1
            elif ch == ')':
                if depth == 0:
                    break
                depth -= 1
            elif depth == 0 and (ch == ';' or FROM.match(s, j)):
                break
            j += 1
        end = s.find(';', j)
        yield s[m.end():j], s[j:end if end >= 0 else len(s)]


def _uncounted(lst):
    """A select list with what each COUNT( ) holds taken out: a count shows no value of what it counts."""
    out, i = [], 0
    for m in COUNT.finditer(lst):
        if m.start() < i:
            continue
        out.append(lst[i:m.start()])
        j, depth = m.end(), 1
        while j < len(lst) and depth:
            depth += {'(': 1, ')': -1}.get(lst[j], 0)
            j += 1
        i = j
    return ''.join(out) + lst[i:]


def _named(text_, name):
    return re.search(rf'(?<![\w$]){re.escape(name)}(?![\w$])', text_, re.I) is not None


def secret_column(operand, command, ctx):
    """Refusal or None: a query that selects a column the operand names, but to count it."""
    s = str(command or '')
    for lst, rest in _select_lists(s):
        plain = _uncounted(lst)
        star = STAR.search(plain) is not None
        for spec in (str(x) for x in _listed(operand.get('columns'))):
            table_, _dot, col = spec.rpartition('.')
            if table_ and not _named(rest, table_):
                continue                                 # a column of another table
            if _named(plain, col):
                return Refusal(f"a query selects `{spec}`, a column the instruction names, and does more than count it",
                               INSTEAD['column'])
            if star:
                return Refusal(f"a query selects every column (`*`) of a table that may hold `{spec}`, a column the "
                               f"instruction names", INSTEAD['column'])
    return None


# ----------------------------------------------------------------------------------------------- credential-file
DESCRIBERS = {'ls', 'stat', 'wc', 'file', 'du', 'test', '[', 'cksum', 'sum', 'md5sum', 'shasum', 'sha1sum', 'sha224sum',
              'sha256sum', 'sha384sum', 'sha512sum', 'b2sum', 'lsattr', 'getfacl'}
SEARCHERS = {'grep', 'egrep', 'fgrep', 'zgrep', 'rg', 'ag'}
SEARCH_VALUED = 'efmABCDdgt'
SEARCH_SAYS_NO_LINE = ('--count', '--files-with-matches', '--files-without-match', '--quiet', '--silent')


def _segments(p):
    s = str(p).replace('\\', '/')
    s = re.sub(r'^[^/=]*=(?=.)', '', s) if s.startswith('-') else s     # `--file=<path>`: the path it names
    s = re.sub(r'^[A-Za-z0-9._@-]+:(?=/)', '', s)                        # `host:/path`, as scp and rsync name one
    return [x for x in s.split('/') if x not in ('', '.', '~', '$HOME', '${HOME}')]


def _tail_of(short, long_):
    """True where the parts `short` (patterns) match the end of `long_`."""
    return 0 < len(short) <= len(long_) and all(
        fnmatch.fnmatchcase(lp, sp) for sp, lp in zip(short, long_[len(long_) - len(short):]))


def _names_file(t, f):
    """A word names a file where its path, past the root or home it may start at, is the file's, or ends it — each part
    matched as a pattern where it is one (`*`, `?`, `[…]`). An absolute word names an absolute file only whole."""
    ws, fs = _segments(t), _segments(f)
    if not ws or not fs:
        return False
    word_abs = _absolute(re.sub(r'^[A-Za-z0-9._@-]+:(?=/)', '', str(t)))
    if word_abs and _absolute(f):
        return len(ws) == len(fs) and _tail_of(ws, fs)
    if word_abs:                                     # the file named from a home this door cannot read
        return len(fs) <= len(ws) and all(fnmatch.fnmatchcase(fp, wp) for wp, fp in zip(ws[len(ws) - len(fs):], fs))
    return _tail_of(ws, fs) or (str(f).startswith('~') and _tail_of(fs, ws))


def _above(t, f):
    """True where an absolute word names a folder above the file."""
    ws, fs = _segments(t), _segments(f)
    return _absolute(t) and _absolute(f) and 0 < len(ws) < len(fs) and all(
        fnmatch.fnmatchcase(fp, wp) for wp, fp in zip(ws, fs))


def _searches_whole(name, rest):
    if name in ('rg', 'ag'):
        return True
    flags = ''.join(_flags(t, SEARCH_VALUED) for t in rest if t.startswith('-') and not t.startswith('--'))
    return name in SEARCHERS and ('r' in flags or 'R' in flags or '--recursive' in rest
                                  or '--dereference-recursive' in rest)


def _only_describes(name, rest):
    """True where a command says only a file's shape: its listing, size, kind, mode or checksum, or a search's count or
    the names it matches in."""
    if name in DESCRIBERS:
        return True
    if name in SEARCHERS:
        flags = ''.join(_flags(t, SEARCH_VALUED) for t in rest if t.startswith('-') and not t.startswith('--'))
        return bool(set(flags) & set('clLq')) or any(t in SEARCH_SAYS_NO_LINE for t in rest)
    return False


def credential_file(operand, command, ctx):
    """Refusal or None: a command that would print a file the operand names, beyond describing its shape."""
    files = [str(x) for x in _listed(operand.get('files'))]
    for a in acts(command, ctx.get('host'), ctx.get('cwd'), ctx.get('home')):
        h = head(a.cmd)
        if h is None:
            continue
        name = _name(a.cmd.words[h]) or text(a.cmd.words[h])
        if name == 'ssh':
            continue                                 # its words are the other host's command, an act of their own
        rest = [text(w) for w in a.cmd.words[h + 1:]]
        for f in files:
            if any(_names_file(t, f) for t in rest) or (_searches_whole(name, rest) and any(_above(t, f) for t in rest)):
                if not _only_describes(name, rest):
                    return Refusal(f"`{name}` would print {f}, a file the instruction names as holding credentials",
                                   INSTEAD['credential'])
    return None


# ------------------------------------------------------------------------------------- own-worktree, no-memory-write
def own_worktree(operand, path, ctx):
    """Refusal or None: a session's write into a working copy of the garden other than its own worktree."""
    wt = ctx.get('worktree')
    if not path or not wt:
        return None                                  # no write, or no session the door knows this agent works in
    p, w = norm(path), norm(wt)
    if under(p, w):
        return None
    for copy in _listed(ctx.get('copies')):
        if under(p, norm(copy)):
            return Refusal(f"{path} is in {copy}, another working copy of the garden; this session's own is {wt}",
                           INSTEAD['worktree'].replace('<worktree>', str(wt)))
    return None


def _in_folder(p, pattern):
    """True where the path lies in a folder the pattern matches (`*` any name), or is that folder."""
    ends = [k for k, ch in enumerate(p) if ch == '/' and k] + [len(p)]
    return any(fnmatch.fnmatchcase(p[:k], pattern) for k in ends)


def no_memory_write(operand, path, ctx):
    """Refusal or None: a write into a folder the harness keeps as its memory."""
    if not path:
        return None
    p = norm(path)
    for folder in _listed(ctx.get('memory')):
        if _in_folder(p, norm(folder)):
            return Refusal(f"{path} is in the harness's memory folder ({folder}), which no other agent reads and no "
                           f"commit records", INSTEAD['memory'])
    return None


CHECKS = {'one-text-one-parser': ('command', lambda operand, command, _ctx: one_text_one_parser(operand, command)),
          'shell-is': ('shell', lambda operand, shell, _ctx: shell_is(operand, shell)),
          'process-command-line': ('command', process_command_line),
          'secret-column': ('command', secret_column),
          'credential-file': ('command', credential_file),
          'own-worktree': ('path', own_worktree),
          'no-memory-write': ('path', no_memory_write)}
CONTEXT = ('host', 'cwd', 'home', 'worktree', 'copies', 'memory')     # what a vector gives as the door would


def table(law):
    return getattr(law, 'guards', None) or {}


def refusal(law, guard, operand, command=None, shell=None, path=None, **ctx):
    """Refusal or None: the guard `guard` of the law, under `operand`, over what its row reads of the act — the command,
    the harness's shell, or the path a write targets — with what the door gives beside it (`CONTEXT`)."""
    row = table(law).get(guard)
    if row is None or guard not in CHECKS:
        return Refusal(f"`{guard}` is no guard of the law (core/law/guards.yaml)", None)
    reads, fn = CHECKS[guard]
    return fn(operand or {}, {'command': command, 'shell': shell, 'path': path}[reads], ctx)


def operand_problems(law, row, operand, where):
    """[(where, message)]: an instruction's operand, as its guard takes it — each attribute it declares and no other,
    the required ones present, a code of the registry it names, a pattern it gives matched."""
    from core import lines
    takes = row.get('takes') or {}
    if operand is None:
        operand = {}
    out = lines.attrs_problems(where, operand, {'attrs': takes})
    if not isinstance(operand, dict):
        return out
    for k, spec in takes.items():
        spec = spec if isinstance(spec, dict) else {}
        dom = spec.get('in')
        if k not in operand:
            continue
        many = str(spec.get('many')) == 'true'           # a list of values, or one value alone
        values = operand[k] if many and isinstance(operand[k], list) else [operand[k]]
        if many and not values:
            out.append((f"{where}.{k}", f"names none: {str(spec.get('meaning') or '')[:160]}"))
        if not isinstance(dom, dict):
            continue
        for n, x in enumerate(values):
            w, v = (f"{where}.{k}[{n}]" if many and isinstance(operand[k], list) else f"{where}.{k}"), str(x)
            if isinstance(x, (dict, list)):
                out.append((w, f"{v!r} is one value, written as text"))
                continue
            if dom.get('pattern') and not re.match(str(dom['pattern']), v):
                out.append((w, f"{v!r} is not written as {dom['pattern']}"))
            if dom.get('registry'):
                try:
                    codes = {str(r.get(dom.get('take') or 'code')) for r in law.std.knowledge.rows(dom['registry'])}
                except Exception:
                    codes = None
                if codes is not None and v not in codes:
                    out.append((w, f"{v!r} is no {dom.get('take') or 'code'} of `{dom['registry']}`"))
    return out


CONTRADICTORY = {'obligatory': 'omissible', 'omissible': 'obligatory', 'forbidden': 'permitted', 'permitted': 'forbidden'}

# AN INSTRUCTION, as the door reads it: its guard, the stance its verb says, its operand, where it is (`<bean>#<id>`),
# what it is of in the gardener's words (the `can` it names), and whether the gardener said it or it is the seed's
Instruction = collections.namedtuple('Instruction', 'guard stance operand where says seed')


def holding(law, instructions):
    """{guard: [Instruction]}: for each guard of the law an instruction names, the instructions that hold it — those in
    its stance — or [] where every one that names it says the contradictory, which lifts it."""
    out = {}
    for name, row in table(law).items():
        named = [i for i in instructions if i.guard == name]
        if named:
            out[name] = [i for i in named if i.stance == row.get('stance')]
    return out


def problems(law):
    """[(where, message)]: the table closed — a function a row and a row a function, each row's stance a position of
    the permission square, its `reads` what its function reads — and each row's vectors holding."""
    out, rows = [], table(law)
    for name, row in rows.items():
        w = f"core/law/guards.yaml {name}"
        if name not in CHECKS:
            out.append((w, "has no function in core/guards.py: a guard is applied, or it is not a row"))
            continue
        if row.get('stance') not in CONTRADICTORY:
            out.append((w, f"stance {row.get('stance')!r} is no position of the permission square"))
        if row.get('reads') != CHECKS[name][0]:
            out.append((w, f"reads {row.get('reads')!r}, and its function reads the act's {CHECKS[name][0]}"))
        for n, v in enumerate(row.get('vectors') or []):
            if not isinstance(v, dict) or str(v.get('refused')) not in ('true', 'false'):
                out.append((f"{w} vectors[{n}]", "is a mapping that says whether it is `refused`, true or false"))
                continue
            got = refusal(law, name, v.get('operand') or {}, command=v.get('command'),
                          shell=(v.get('shell'), v.get('version'), None) if 'shell' in v else None, path=v.get('path'),
                          **{k: v[k] for k in CONTEXT if k in v})
            if (got is not None) != (v['refused'] == 'true'):
                out.append((f"{w} vectors[{n}]", f"is {'refused' if got else 'let through'}, and the law says it is "
                                                 f"{'refused' if v['refused'] == 'true' else 'let through'}"
                                                 + (f": {got.found}" if got else '')))
    for name in CHECKS:
        if name not in rows:
            out.append(('core/law/guards.yaml', f"core/guards.py applies `{name}`, which is no row of the table"))
    return out
