"""guards — what an agent's own door checks before the agent acts: the law's closed table of guards (core/law/guards.yaml),
one function a row, each held to the row's vectors.

    from core import guards
    guards.refusal(law, 'one-text-one-parser', {}, command='bash -c ...')      # None, or a Refusal
    guards.refusal(law, 'shell-is', {'shell': 'bash', 'floor': '5.0'}, shell=('zsh', '5.9', '/bin/zsh'))
    guards.problems(law)                    # the table closed: a function a row, a row a function, every vector holds
    guards.operand_problems(law, row, x)    # an instruction's operand, as its guard takes it (rule `measured`)
    guards.holding(law, instructions)       # {guard: [Instruction]}: the guards an instruction holds, lifted or not

A guard reads one thing of the act, as its row says (`reads`): `command`, the text a shell is given, or `shell`, the
shell the agent's harness runs its commands in — (name, version, path), found by the harness's own rule, which is the
harness's and is read by the door that runs in it (bin/hook.py). What it finds is a Refusal: what was found, and what to
do instead, in plain words.

ONE TEXT, ONE PARSER. A command is read here as the shell the garden declares reads it (bash's grammar, which sh, zsh and
Git for Windows' bash share for everything the guard looks at): its simple commands, each a list of words, each word its
parts as they were quoted; what a substitution holds, `$( … )` or backquotes, read as a command line of its own; a
heredoc's body taken whole, never read for quotes. A command whose quotes, substitutions or heredocs do not close is
refused: the shell would read it otherwise than it was written, and a door that cannot read an act fails closed."""
import collections
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
    def __init__(self):
        self.words = []


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
        self.cmd, self.word = Command(), None
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
            self.word = None

    def end_cmd(self):
        self.end_word()
        if self.cmd.words:
            self.out.append(self.cmd)
        self.cmd = Command()

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
                    self.i += 1
                    while self.peek() and self.peek() in '<>&':
                        self.i += 1
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


CHECKS = {'one-text-one-parser': ('command', one_text_one_parser), 'shell-is': ('shell', shell_is)}


def table(law):
    return getattr(law, 'guards', None) or {}


def refusal(law, guard, operand, command=None, shell=None):
    """Refusal or None: the guard `guard` of the law, under `operand`, over the act's command or the harness's shell."""
    row = table(law).get(guard)
    if row is None or guard not in CHECKS:
        return Refusal(f"`{guard}` is no guard of the law (core/law/guards.yaml)", None)
    reads, fn = CHECKS[guard]
    return fn(operand or {}, command if reads == 'command' else shell)


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
        dom = (spec or {}).get('in') if isinstance(spec, dict) else None
        if k not in operand or not isinstance(dom, dict):
            continue
        v = str(operand[k])
        if dom.get('pattern') and not re.match(str(dom['pattern']), v):
            out.append((f"{where}.{k}", f"{v!r} is not written as {dom['pattern']}"))
        if dom.get('registry'):
            try:
                codes = {str(r.get(dom.get('take') or 'code')) for r in law.std.knowledge.rows(dom['registry'])}
            except Exception:
                codes = None
            if codes is not None and v not in codes:
                out.append((f"{where}.{k}", f"{v!r} is no {dom.get('take') or 'code'} of `{dom['registry']}`"))
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
                          shell=(v.get('shell'), v.get('version'), None) if 'shell' in v else None)
            if (got is not None) != (v['refused'] == 'true'):
                out.append((f"{w} vectors[{n}]", f"is {'refused' if got else 'let through'}, and the law says it is "
                                                 f"{'refused' if v['refused'] == 'true' else 'let through'}"
                                                 + (f": {got.found}" if got else '')))
    for name in CHECKS:
        if name not in rows:
            out.append(('core/law/guards.yaml', f"core/guards.py applies `{name}`, which is no row of the table"))
    return out
