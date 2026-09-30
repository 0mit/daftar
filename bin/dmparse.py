#!/usr/bin/env python3
"""dmparse — the ONE front-matter splitter for daftar (v2 P0).

Why this file exists: every tool used to split a document with `text.split('---', 2)`, which cuts on
the FIRST occurrence of three dashes ANYWHERE — including inside a YAML value, a table rule, an em-dash
run, or a `----` separator in the body. That silently truncated documents (the `----` truncation class).
Here the fences are LINE-ANCHORED: a fence is a whole line that is exactly `---` (trailing spaces/tabs
and a CR are tolerated). Front-matter is what lies between fence #1 (which must open the document) and
fence #2. Everything after fence #2 is body, verbatim.

One owner of a fact: dmcheck.py and dmmerge.py both import this — the parsing rule lives here only.
"""
import collections
import re
import os, sys


# THE TOOLS SPEAK UTF-8 ON EVERY PLATFORM. On Windows a Python whose output goes to a pipe — which is how an agent runs a
# tool — encodes in the ANSI code page, and the first `—` or Persian letter in a finding ends the run in a traceback.
# Every tool imports this module, so it is set once here, and only where the stream is not UTF-8 already.
# ...AND READ UTF-8. git, and a tool run as a child, print UTF-8, and a Python before 3.15 (PEP 686) decodes a child's
# output in that same code page: a Persian gardener's bean read back from git failed in subprocess's reader thread. So
# every subprocess call that reads text names `encoding='utf-8'` — with `errors='replace'` where the tool shows, scans
# or judges what it read, strict where it acts on it as a path or writes it back — and test/journal.py holds every
# call to it.
for _s in (sys.stdout, sys.stderr):
    try:
        if _s is not None and (getattr(_s, 'encoding', '') or '').lower().replace('-', '') != 'utf8':
            _s.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, ValueError):
        pass
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dmform

FENCE = re.compile(r'^---[ \t]*\r?$', re.M)
BOM = '﻿'


def split_front_matter(text):
    """(front_matter_text, body) for a fenced document, else (None, text).

    The opening fence must be the document's first line (a UTF-8 BOM is tolerated). The closing fence
    is the next line that is exactly `---`. Byte-for-byte compatible with the old naive split on every
    well-formed document: the returned front-matter starts at the newline after fence #1, and the body
    starts immediately after the three dashes of fence #2 (i.e. it keeps its leading newline).
    """
    if text.startswith(BOM):
        text = text[len(BOM):]
    m1 = FENCE.match(text)                      # anchored at offset 0: fence #1 opens the document
    if not m1:
        return None, text
    m2 = FENCE.search(text, m1.end())
    if not m2:
        return None, text
    return text[m1.end():m2.start()], text[m2.end():]


IDENTITY_ORDER = re.compile(r'^by-([a-z0-9_-]+\??(?:\+[a-z0-9_-]+\??)*)$')


def identity_fields(order):
    """`merge.order` read as a member identity: [(field, may_be_absent), ...], or None for an order that
    names no identity (`none`, `cidr`, ...).

    `by-role` is one field; `by-protocol+system+at+port?` is four, and the trailing `?` says an entry may
    lack `port` — its absence is then part of the identity rather than a reason to guess one (std-vocab@8.0).
    Here because the gate checks the declaration and the merge applies it, and two parsers of one grammar
    are two grammars."""
    m = IDENTITY_ORDER.match(str(order or ''))
    if not m:
        return None
    return [(f.rstrip('?'), f.endswith('?')) for f in m.group(1).split('+')]


def duplicate_keys(text):
    """[(dotted_path, first_line, repeat_line)] for every key written twice in one mapping, at any depth.

    YAML keeps the LAST value and discards the first without a word, so a duplicated key is a value lost at
    parse time, which no check on the parsed document can see. Read from the node graph, before that loss.
    Lines are 1-based within `text`."""
    if _yaml is None:
        raise RuntimeError("PyYAML required")
    out = []

    def walk(node, path):
        if isinstance(node, _yaml.MappingNode):
            seen = {}
            for k, v in node.value:
                name = k.value if isinstance(k, _yaml.ScalarNode) else '?'
                here = f"{path}.{name}" if path else name
                if isinstance(k, _yaml.ScalarNode):
                    if (k.tag, k.value) in seen:
                        out.append((here, seen[(k.tag, k.value)], k.start_mark.line + 1))
                    seen[(k.tag, k.value)] = k.start_mark.line + 1
                walk(v, here)
        elif isinstance(node, _yaml.SequenceNode):
            for i, v in enumerate(node.value):
                walk(v, f"{path}[{i}]")

    walk(_yaml.compose(text, Loader=LOADER), '')
    return out


# HOW AN ANCHOR IS COMPARED (std-vocab 9.0). A term that governs an anchor may declare `compare_form`; identity is
# then judged on that form. HERE, because the gate (uniqueness) and the merge (which beans are one object) must
# compare the same way — v0.5.0 taught only the gate, and two gardens holding `SYN-0042` and `syn-0042` still
# merged into two objects.
COMPARE_FORMS = {'upper-trim': lambda v: re.sub(r'\s+', '', v).upper()}


# HOW A FORM IS CHECKED WHEN A TOOL ALREADY CHECKS IT COMPLETELY (std-vocab 18.2). A system row states its form as a
# `pattern`, or names a check here with `checked_by`. A pattern for an IP address is a second, weaker copy of a validator
# the standard library has carried for years — the one written for 18.1 had to be tightened the day it was compared
# with it. HERE, beside COMPARE_FORMS and for the same reason: the gate and the merge must judge a form the same way.
def _ip_form(version):
    import ipaddress

    def check(v):
        v = str(v)
        try:
            parsed = ipaddress.ip_interface(v) if '/' in v else ipaddress.ip_address(v)
        except ValueError:
            return False
        # ONE spelling: the library's own. `2001:DB8::1` and `2001:0db8:0:0:0:0:0:1` are the address `2001:db8::1`.
        return parsed.version == version and str(parsed) == v
    return check


FORM_CHECKS = {'ipaddress-v4': _ip_form(4), 'ipaddress-v6': _ip_form(6)}


def law_match(pattern, value):
    """A value against a pattern OF THE LAW — the one way every tool matches one. ASCII only (std-vocab 16.0: in Python
    `\\d` matches every Unicode digit, and `۲۰۲۶-۰۹-۲۰` is not a second spelling of a date). And a pattern that ends in
    `$` ends at the END OF THE VALUE: Python's `$` also matches before a final newline, so `count: "100\\n"` passed the
    gate while a reader that matched the whole value refused it — two readers of one pattern, disagreeing."""
    p, v = str(pattern), str(value)
    m = re.match(p, v, re.ASCII)
    if m and p.endswith('$') and not p.endswith('\\$') and m.end() != len(v):
        return None
    return m


def split_coding(value):
    """(scheme, code) of a CODING (`value_types[coding]`, 29.0): a code written with the scheme it is a code of,
    `<scheme>:<code>`. The first colon ends the scheme, whose name has none; a code may hold one. (None, None) for
    anything else — a reader that meets another spelling reads no code there, and the gate says why."""
    if isinstance(value, str) and ':' in value:
        s, c = value.split(':', 1)
        if s and c and law_match(r'^[a-z0-9][a-z0-9-]*$', s):
            return s, c
    return None, None


def in_form(row, value):
    """True when `value` is written in the ONE form the system row declares: by the check it names, else by its
    pattern. None when the row declares no form at all (`pattern: none`, deliberately)."""
    if not isinstance(row, dict):
        return None
    if row.get('checked_by'):
        chk = FORM_CHECKS.get(row['checked_by'])
        return None if chk is None else bool(chk(value))
    pat = row.get('pattern')
    if pat in (None, 'none'):
        return None
    return bool(law_match(pat, value))


def form_said(row):
    """How a row's form is described to a person who got it wrong."""
    return f"checked by {row['checked_by']}" if row.get('checked_by') else repr(row.get('pattern'))


# A PATH INTO WHAT BEANS HOLD (`value_types[field_path]`, 24.0): read here and nowhere else. A segment is a key, or `*` for
# every key of a map or entry of a list, with `[<attr>=<value>]` for the entries holding that value; `.` goes in, `>` follows
# a ref to the bean it names and goes on there; `<bean>:` first starts at another bean; `@occurrence` is a word of its own.
Segment = collections.namedtuple('Segment', 'bean key star match follow')
_PATH_BEAN = re.compile(r'([a-z0-9][a-z0-9-]*):', re.ASCII)
_PATH_SEG = re.compile(r'(\*|[a-z0-9_][a-z0-9_-]*)(?:\[([a-z_][a-z0-9_]*)=([^\]\s]+)\])?', re.ASCII)


def path_read(text):
    """The segments of a field path, in order — or ValueError, saying where it stops being one (`path_problem`)."""
    if text == '@occurrence':
        return [Segment(None, '@occurrence', False, None, False)]
    if not isinstance(text, str) or not text:
        raise ValueError("a path is text, and not empty")
    i, out, bean, follow = 0, [], None, False
    m = _PATH_BEAN.match(text)
    if m:
        bean, i = m.group(1), m.end()
    while True:
        m = _PATH_SEG.match(text, i)
        if not m:
            raise ValueError(f"at character {i + 1}: a key, `*`, or a key with `[<attr>=<value>]` is wanted"
                             + (f", not {text[i:i + 8]!r}" if i < len(text) else ", and the path ends"))
        out.append(Segment(bean if not out else None, m.group(1), m.group(1) == '*',
                           (m.group(2), m.group(3)) if m.group(2) else None, follow))
        i = m.end()
        if i == len(text):
            return out
        if text[i] not in '.>':
            raise ValueError(f"at character {i + 1}: `.` goes in and `>` follows a ref — {text[i]!r} does neither")
        follow, i = text[i] == '>', i + 1


def path_problem(text):
    """None when `text` is a field path; else what is wrong with it, in words."""
    try:
        path_read(text)
    except ValueError as e:
        return str(e)
    return None


def anchor_compare_form(terms, key):
    """The compare form the vocabulary declares for anchor `key`, or None. `terms`: term dicts with `schema`."""
    for t in terms:
        v = dmform.attribute_form(t, t.get('schema') if isinstance(t, dict) else None)['value']
        if v.get('governs_anchor') == key and v.get('compare_form') in COMPARE_FORMS:
            return v['compare_form']
    return None


def compare_anchor(terms, key, value):
    """`value` as identity compares it: in the declared compare form, else unchanged (as a string)."""
    form = anchor_compare_form(terms, key)
    return COMPARE_FORMS[form](str(value)) if form else str(value)


def garden_id(root):
    """A GARDEN'S IDENTITY (std-vocab 21.0, `garden_id`): the first twelve hex digits of the root of its first-parent
    history — the commit it germinated from — or None outside a git repository and in a shallow clone, which cannot
    see its root. HERE, because the gate (`dmcheck.own_garden_id`), the merge (which garden a bare minted name belongs
    to) and the proposals between gardens (`dmpropose`) must read one identity the same way, and dmcheck cannot be
    imported outside a garden."""
    import subprocess
    try:
        r = subprocess.run(['git', '-C', root, 'rev-list', '--first-parent', '--max-parents=0', 'HEAD'],
                           capture_output=True, text=True, encoding='utf-8', timeout=5)
        roots = r.stdout.split()
        shallow = subprocess.run(['git', '-C', root, 'rev-parse', '--is-shallow-repository'],
                                 capture_output=True, text=True, encoding='utf-8', timeout=5).stdout.strip()
        return roots[-1][:12] if r.returncode == 0 and roots and shallow != 'true' else None
    except Exception:
        return None


class NotUTF8(UnicodeDecodeError):
    """A document that is not UTF-8, refused BY NAME. Windows PowerShell 5.1 writes a file in the machine's code page
    (`Set-Content`) or in UTF-16 (`>`, `Out-File`), and a traceback naming a byte and no file told a person with a
    hundred beans nothing: not which one, nor what to do. Still a UnicodeDecodeError, so a caller that catches one
    catches this; its text says what the file looks like and how to save it."""

    def __init__(self, path, raw, err):
        super().__init__(err.encoding, err.object, err.start, err.end, err.reason)
        self.path, self.looks = path, _looks_like(raw, err.start)

    def __str__(self):
        return f"not UTF-8 — it looks like {self.looks}: save it as UTF-8"


def _looks_like(raw, at):
    """What a file that is not UTF-8 most likely is, from its first bytes."""
    import codecs
    if raw.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return "UTF-16 (what PowerShell's `>` and `Out-File` write)"
    half = raw[:400]
    if half and max(half[0::2].count(0), half[1::2].count(0)) * 4 >= len(half):
        return "UTF-16 with no byte-order mark"
    return (f"a Windows code page such as 1252 (byte 0x{raw[at]:02x} at {at}; what Windows PowerShell 5.1's "
            f"`Set-Content` writes)")


def read(path):
    """(front_matter_text, body) read from a file on disk, as UTF-8 — a byte-order mark dropped, line ends read as text
    mode reads them. A file that is not UTF-8 raises NotUTF8, which says what it looks like."""
    with open(path, 'rb') as fh:
        raw = fh.read()
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError as e:
        raise NotUTF8(path, raw, e) from None
    return split_front_matter(text.replace('\r\n', '\n').replace('\r', '\n'))


# ---- TEXT, AS A READER SEES IT ------------------------------------------------------------------------------------
# A character that ends a line or drives a terminal: C0, DEL, C1 (NEL and the 8-bit CSI among them) and the Unicode
# line and paragraph separators. Printed raw, one moves the cursor, erases what was written, or hides what follows —
# so a value a document holds is printed with each of them spelt out, never sent to the terminal.
_CTRL = re.compile('[\x00-\x1f\x7f-\x9f  ]')


def escaped(s):
    """`s` as it may be printed: every character `_CTRL` names spelt `\\xNN` or `\\uNNNN`."""
    return _CTRL.sub(lambda m: (f"\\x{ord(m.group(0)):02x}" if ord(m.group(0)) < 0x100 else
                                f"\\u{ord(m.group(0)):04x}"), str(s))


def said(line):
    """A tool's own line of output: its line feeds kept, every other such character in it spelt out."""
    return '\n'.join(escaped(x) for x in str(line).split('\n'))


def control_characters(text, category='Cc', but=('\t',), lines_in='block'):
    """[(dotted path, character, scalar style, is_key)] for every character of Unicode general category `category`
    in a key or a scalar of the YAML `text` — but those in `but`, and a line feed in a scalar whose style `lines_in`
    names (`block`: `|` or `>`, the scalars whose lines are lines on the page). Read from the NODE GRAPH, because only
    there is a scalar's style known: `"a\\nb"` and a block of two lines load as the same string."""
    import unicodedata
    if _yaml is None:
        raise RuntimeError("PyYAML required")
    block = ('|', '>') if lines_in == 'block' else ()
    out, seen = [], set()

    def scalar(node, path, is_key):
        if node.value.isprintable() and category[:1] in ('C', 'Z'):
            return                              # no character of an Other or Separator category: nothing to look up
        for ch in sorted(set(node.value)):
            if unicodedata.category(ch) == category and ch not in but and not (ch == '\n' and node.style in block):
                out.append((path, ch, node.style, is_key))

    def walk(node, path):
        if id(node) in seen:
            return                              # an alias names a node already walked
        seen.add(id(node))
        if isinstance(node, _yaml.MappingNode):
            for k, v in node.value:
                name = escaped(k.value) if isinstance(k, _yaml.ScalarNode) else '?'
                here = f"{path}.{name}" if path else name
                if isinstance(k, _yaml.ScalarNode):
                    scalar(k, here, True)
                else:
                    walk(k, here)
                walk(v, here)
        elif isinstance(node, _yaml.SequenceNode):
            for i, v in enumerate(node.value):
                walk(v, f"{path}[{i}]")
        elif isinstance(node, _yaml.ScalarNode):
            scalar(node, path, False)

    root = _yaml.compose(text, Loader=LOADER)
    if root is not None:
        walk(root, '')
    return out


# --- the ONE loader ------------------------------------------------------------------------------
# MEASURED 2026-08-07, not assumed: `yaml.safe_load` accounted for 4.2 s of the gate's 4.6 s, and the
# gate is spawned ~115 times by test/golden.py (the maintainers' corpus test, not shipped here) — so
# the whole suite was pure-Python YAML parsing.
# libyaml's CSafeLoader is 13.3x faster on this corpus and produces IDENTICAL objects for all 72
# documents (verified by comparing both loaders' output document by document, with the comparison
# itself first shown able to detect a difference).
#
# It lives HERE because dmparse is already "the one front-matter splitter — everything uses it,
# nothing reimplements it". A second copy of the loader choice in each tool is a second copy of a
# decision, and this repo has paid for that shape before.
#
# The fallback is NOT a silent one: where libyaml is absent the pure-Python loader is correct and
# merely slow, which is a performance difference and not a difference in law. That is the opposite of
# the one-path rule (MODEL.md, The journal and the gate), where falling back would substitute a DIFFERENT rule.
try:
    import yaml as _yaml
    LOADER = _yaml.CSafeLoader
    FAST = True
except (ImportError, AttributeError):        # PyYAML built without libyaml
    try:
        import yaml as _yaml
        LOADER = _yaml.SafeLoader
    except ImportError:
        _yaml = None
        LOADER = None
    FAST = False

# A NUMBER IS WHAT WAS WRITTEN (std-vocab 21.0). YAML 1.1 reads a plain scalar as an integer in five spellings nobody
# writes a count in: `010` is eight (octal), `0x64` a hundred, `0b11` three, `1:30` ninety (base sixty) and `1_000` a
# thousand. So `count: 010` passed the gate as a whole number and every reader agreed on 8 XTS — an amount nobody wrote,
# and nobody told. The loader resolves a plain scalar to an integer ONLY in plain decimal; every other spelling loads as
# the text it is, and the law's patterns (`value_types[count]`, a share's) then refuse it by name. Floats, booleans,
# dates and nulls resolve as before.
PLAIN_INT = re.compile(r'^[-+]?(0|[1-9][0-9]*)$')
if LOADER is not None:
    _INT_TAG = 'tag:yaml.org,2002:int'

    class _Loader(LOADER):
        pass
    # a fresh table owned by the subclass, so the library's own loaders keep YAML 1.1 for anyone else in the process
    _Loader.yaml_implicit_resolvers = {k: [(tag, rx) for tag, rx in v if tag != _INT_TAG]
                                       for k, v in LOADER.yaml_implicit_resolvers.items()}
    _Loader.add_implicit_resolver(_INT_TAG, PLAIN_INT, list('-+0123456789'))

    # ...and an EXPLICIT `!!int` asks the same question. The resolver above only decides what an untagged scalar is;
    # `count: !!int 010` names the tag itself, and the library's constructor then reads the text in YAML 1.1's octal,
    # hex, base sixty and underscore forms — 8, 100, 90, 1000 — whether the text was quoted or not. So the tag builds an
    # integer only from plain decimal; any other text stays the text it is, as the same text untagged does, and the
    # law's patterns refuse it by name. (fullmatch: a quoted `"12\n"` is not twelve.)
    def _construct_int(loader, node):
        text = loader.construct_scalar(node)
        return int(text) if PLAIN_INT.fullmatch(text) else text
    _Loader.add_constructor(_INT_TAG, _construct_int)

    # A YAML SET (`!!set { a }`) is no shape a garden writes: the law's values are one text, a list or a mapping, and
    # a set is none of them — held by nothing, hashable by nothing, and a traceback in every reader that asks "is this
    # one of the positions". Refused where it is read, by name, so every tool reads the same thing.
    def _construct_set(loader, node):
        raise _yaml.constructor.ConstructorError(None, None, "a YAML set (`!!set`) is no shape a garden writes — "
                                                "write a list", node.start_mark)
    _Loader.add_constructor('tag:yaml.org,2002:set', _construct_set)
    LOADER = _Loader


def overlay_term(base, over):
    """Garden-local overlay on a Tier-0 term: local keys win, `schema` merges key-by-key.

    `schema.values_add: [...]` APPENDS to the Tier-0 enum instead of replacing it, so a garden adds one value
    without restating (and then having to account for) every value Tier-0 already offers."""
    out = dict(base)
    for k, v in over.items():
        if k == 'schema' and isinstance(v, dict) and isinstance(base.get('schema'), dict):
            out['schema'] = {**base['schema'], **v}
            # `attrs` merges PER ATTRIBUTE (13.0): a garden that adds one attribute to a Tier-0 term, or gives one
            # a domain, must not thereby restate — and then own — every attribute the standard already declares.
            if isinstance(v.get('attrs'), dict) and isinstance(base['schema'].get('attrs'), dict):
                out['schema']['attrs'] = {**base['schema']['attrs'],
                                          **{a: {**(base['schema']['attrs'].get(a) or {}), **(r or {})}
                                             for a, r in v['attrs'].items()}}
            if isinstance(v.get('cells'), list) and isinstance(base['schema'].get('cells'), list):
                out['schema']['cells'] = list(base['schema']['cells']) + list(v['cells'])
        else:
            out[k] = v
    _s = out.get('schema')
    if isinstance(_s, dict) and _s.get('values_add'):
        _s['values'] = list(_s.get('values') or []) + [x for x in _s['values_add'] if x not in (_s.get('values') or [])]
    return out


def profile_overlays(law, names=None):
    """[(profile, overlay)] of the profiles named — every profile the law offers where `names` is None — in the law's order:
    what each ADDS to a term of the core (28.1). One reader, so the gate, the rules and the catalogue read one list."""
    out = []
    profs = law.get('profiles') if isinstance(law, dict) and isinstance(law.get('profiles'), dict) else {}
    for pn, prof in profs.items():
        if names is not None and pn not in names or not isinstance(prof, dict):
            continue
        for o in prof.get('overlays') or []:
            if isinstance(o, dict) and isinstance(o.get('term'), str):
                out.append((pn, o))
    return out


def extend_term(base, over):
    """A profile's overlay on a core term (28.1): what it ADDS, merged — its attributes beside the term's, its `sums` rules
    after the term's, its `cells` after the term's, and the genos it requires the term on beside the term's own (29.0: a
    codebase carries a location where the `code` profile is extended). It rewrites nothing: an attribute the term already
    states is the caller's to refuse, never merged over. Returns the term as the garden that extends the profile reads it."""
    out = dict(base)
    sch = dict(base.get('schema') or {}) if isinstance(base.get('schema'), dict) else {}
    osch = over.get('schema') if isinstance(over.get('schema'), dict) else {}
    if isinstance(osch.get('attrs'), dict):
        sch['attrs'] = {**(sch.get('attrs') or {}), **{a: r for a, r in osch['attrs'].items() if a not in (sch.get('attrs') or {})}}
    for k in ('sums', 'cells'):
        if osch.get(k) is not None:
            mine = sch.get(k)
            mine = [] if mine is None else (list(mine) if isinstance(mine, list) else [mine])
            sch[k] = mine + (list(osch[k]) if isinstance(osch[k], list) else [osch[k]])
    if isinstance(osch.get('required_on_gene'), list):
        mine = sch.get('required_on_gene') if isinstance(sch.get('required_on_gene'), list) else []
        sch['required_on_gene'] = list(mine) + [g for g in osch['required_on_gene'] if g not in mine]
    out['schema'] = sch
    return out


def loads(text):
    """Parse YAML the one way this garden parses it. Semantically identical to yaml.safe_load."""
    if _yaml is None:
        raise RuntimeError("PyYAML required")
    return _yaml.load(text, Loader=LOADER)


# ---- A COMMENT IN A FRONT MATTER, AND WHAT IT SITS ON (24.0: the law carries no story) ----------------------------------
# A `#` begins a comment where it is outside quotes, at a line's start or after a blank, and outside a block scalar
# (`|`, `>`), whose lines are the value's text. What a comment sits on is the item on its line, or, for a comment on a
# line of its own, the item on the next line that holds one; named as bin/dmwhy.py keys a reason: `a.b[x].c`, a list's
# item by the first scalar it holds. One reader, so the gate and the upgrade find the same comments.
TITLE = re.compile(r'^\s*# == [^=]+ ==\s*$')


def comment_start(line):
    """The column a comment begins at in one YAML line, or -1. Quotes are read as YAML reads them: a quote opens a
    quoted scalar only where a scalar begins (after `: `, `- `, `[`, `{`, `,`, or at the line's start), so `it's here
    # note` holds a comment; in double quotes a backslash escapes the next character (`"a \" # b"` holds none); in
    single quotes `''` is a quote, and a backslash is itself."""
    q, i, n = None, 0, len(line)
    while i < n:
        ch = line[i]
        if q == '"':
            if ch == '\\':
                i += 2
                continue
            if ch == '"':
                q = None
        elif q == "'":
            if ch == "'":
                if i + 1 < n and line[i + 1] == "'":
                    i += 2
                    continue
                q = None
        elif ch in "\"'":
            before = line[:i].rstrip()
            if (i == 0 or line[i - 1] in ' \t[{,') and (not before or before[-1] in ':-[{,?'):
                q = ch
        elif ch == '#' and (i == 0 or line[i - 1] in ' \t'):
            return i
        i += 1
    return -1


def comments(head):
    """[(line, column, text, [paths])] of every comment in a front matter's text, section titles (`# == x ==`) left out;
    `paths` runs from the finest item the comment sits on to its top-level key. [] where the text does not parse."""
    if _yaml is None:
        raise RuntimeError("PyYAML required")
    try:
        root = _yaml.compose(head, Loader=LOADER)
    except _yaml.YAMLError:
        return []
    spans, block = [], set()

    def walk(node, path):
        if isinstance(node, _yaml.ScalarNode):
            if node.style in ('|', '>'):
                block.update(range(node.start_mark.line + 1, node.end_mark.line + (1 if node.end_mark.column else 0)))
            return
        if isinstance(node, _yaml.MappingNode):
            for k, v in node.value:
                p = f"{path}.{k.value}" if path else str(k.value)
                spans.append((k.start_mark.line, v.end_mark.line, p))
                walk(v, p)
        elif isinstance(node, _yaml.SequenceNode):
            for item in node.value:
                ident = next((v.value for _k, v in (item.value if isinstance(item, _yaml.MappingNode) else [])
                              if isinstance(v, _yaml.ScalarNode)), item.value if isinstance(item, _yaml.ScalarNode) else '')
                p = f"{path}[{ident}]"
                spans.append((item.start_mark.line, item.end_mark.line, p))
                walk(item, p)
    if root is not None:
        walk(root, '')
    lines = head.split('\n')
    content = [i for i, l in enumerate(lines) if l.strip() and i not in block
               and (comment_start(l) < 0 or l[:comment_start(l)].strip())]

    def paths(at):
        here = [s for s in spans if s[0] <= at <= max(s[1], s[0])] or [s for s in spans if s[0] == at]
        if not here:
            return []
        start = max(s[0] for s in here)
        best = min((s for s in here if s[0] == start), key=lambda s: len(s[2]))[2]    # the line's own item
        out, p = [], best
        while p:
            out.append(p)
            p = re.sub(r'(\.[^.\[\]]+|\[[^\]]*\])$', '', p) if re.search(r'[.\[]', p) else ''
        return out
    found = []
    for i, l in enumerate(lines):
        c = comment_start(l) if i not in block else -1
        if c < 0 or TITLE.match(l):
            continue
        on = i if l[:c].strip() else next((j for j in content if j > i), next((j for j in reversed(content) if j < i), None))
        found.append((i, c, l[c:].lstrip('#').strip(), paths(on) if on is not None else []))
    return found


# ---- A TABLE: ROWS OF CELLS, READ AND WRITTEN HERE AND NOWHERE ELSE (std-vocab `value_types[rows]`) ------------------
# A series holds its rows as a table — a header line, then one line per row, the cells separated by one tab — inline in
# a bean as a block scalar (`rows: |`), or in a file of its own. ONE READER AND ONE WRITER, both here (D46): the gate,
# bin/dmseq.py, the merge and the proposals read a table only through `table_read`, and whatever re-emits a bean writes
# one only through `table_dumper`. PyYAML will not write a tab inside a block scalar, even asked to: it double-quotes the
# string, and a merged chart became one escaped line — the same value, and a page nobody can read. So the dumper chooses
# the block itself for a value that IS a table, and writes it back byte for byte.
#
# THE FORM IS FIXED SO THAT NOTHING CHANGES IT: every line ends in a line feed alone; no line is empty; no cell is empty
# and none begins or ends in a space — a value nobody read is written as a gap token, never left blank — so no line
# ends in whitespace, and an editor that trims trailing whitespace changes nothing. What a cell MEANS (a count, a
# position, a code, a gap) is the channel's, read by bin/dmseq.py against the law; this reads only the form.
class TableError(ValueError):
    """A table not in its one form, refused by name: the line and what is wrong with it."""


def table_problems(text):
    """[what is wrong] with `text` as a table, or [] — the form only, never what a cell means."""
    if not isinstance(text, str):
        return [f"a table is text — a header line and one line per row, written as a block (`|`) — not {type(text).__name__}"]
    out = []
    if '\r' in text:
        out.append("a line ends in a carriage return: every line of a table ends in a line feed alone")
    lines = text.split('\n')
    if lines and lines[-1] == '':
        lines = lines[:-1]
    if not lines:
        return out + ["it is empty: a table has a header line, naming its columns"]
    head = lines[0].split('\t')
    for j, h in enumerate(head):
        if not h or h != h.strip():
            out.append(f"the header's column {j + 1} is {'empty' if not h else repr(h) + ', with a space at an end'}: "
                       f"a column is named, and its name is one word")
    _seen = set()
    for h in head:
        if h in _seen:
            out.append(f"the header names the column {h!r} twice: a table is read by its header's names")
        _seen.add(h)
    for i, line in enumerate(lines[1:], start=2):
        if line == '':
            out.append(f"line {i} is empty: a row that holds nothing is not a row — a value nobody read is a gap token")
            continue
        cells = line.split('\t')
        if len(cells) != len(head):
            out.append(f"line {i} holds {len(cells)} cell(s) and the header names {len(head)} column(s): a row has "
                       f"one cell per column, a tab between two")
            continue
        for j, c in enumerate(cells):
            if c == '':
                out.append(f"line {i}, column {head[j]!r} is an empty cell: a value nobody read is written as a gap "
                           f"token, never left blank")
            elif c != c.strip():
                out.append(f"line {i}, column {head[j]!r} begins or ends in a space: {c!r}")
        if len(out) > 20:
            out.append("… and more")
            break
    return out


def table_read(text):
    """(header, rows) of a table in its one form: the column names, and each row as a list of its cells, as text. Raises
    TableError naming what is wrong — the first thing — when it is not in its form."""
    bad = table_problems(text)
    if bad:
        raise TableError(bad[0])
    lines = text.split('\n')
    if lines[-1] == '':
        lines = lines[:-1]
    return lines[0].split('\t'), [line.split('\t') for line in lines[1:]]


def table_write(header, rows):
    """A table in its one form, from its column names and its rows of cells: what `table_read` reads back, byte for byte.
    Raises TableError for a cell that has no form here — empty, holding a tab or a line break, or spaced at an end."""
    out = []
    for n, row in enumerate([list(header)] + [list(r) for r in rows]):
        cells = [str(c) for c in row]
        for c in cells:
            if c == '' or c != c.strip() or '\t' in c or '\n' in c or '\r' in c:
                raise TableError(f"{'the header' if n == 0 else f'row {n}'} holds {c!r}: a cell is one word or value, "
                                 f"never empty, holding no tab or line break")
        out.append('\t'.join(cells))
    text = '\n'.join(out) + '\n'
    bad = table_problems(text)
    if bad:
        raise TableError(bad[0])
    return text


def is_table(value):
    """True when `value` is a table in its one form, of two lines or more — a header and a row, however many columns:
    the text `table_dumper` writes back as a block, whatever its style was when it was read."""
    return isinstance(value, str) and '\n' in value.rstrip('\n') and not table_problems(value)


def table_dumper(base):
    """A YAML dumper, from `base`, that writes every value that is a table (`is_table`) as a block scalar, byte for
    byte — the only change it makes. Where a table is a key, or inside a flow collection, it is left to the base, which
    quotes it: a table is written as a value in block style."""
    class _TableDumper(base):
        def choose_scalar_style(self):
            v = self.event.value
            if not self.flow_level and not self.simple_key_context and is_table(v):
                if self.analysis is None:
                    self.analysis = self.analyze_scalar(v)
                return '|'
            return super().choose_scalar_style()
    return _TableDumper


# ---- A GARDEN'S VOCABULARY, READ IN ITS OWN SHAPE -----------------------------------------------------------------
# VOCAB.md is written by hand, and what the interpreter iterates must be a list, what it looks a row up by a name, what it
# prints a word, and a pattern it matches one Python compiles. So each block of it, and each ENTRY of a block, is read in
# its own shape or not at all: an entry of another shape is refused by name and left unread. A list where a name belongs
# ended the gate in a traceback, `local_terms: [5]` passed as though it said something, and a pattern that does not
# compile ended the run at the first value matched against it. ONE definition, read by the gate (which refuses what this
# leaves out) and by dmrules (which lists no rule of it), so the two never disagree about what a garden's vocabulary says.
VOCAB_BLOCKS = (('local_terms', list), ('local_gene', list), ('vacancies', list), ('extends_profiles', list),
                ('registry_files', list), ('registry_forms', dict), ('registry_additions', dict),
                ('identity_policy', dict))
_NAME_KEYS = ('shape', 'key_form', 'path', 'values_from', 'must_equal_genos_attr', 'entry_form_from_genos_attr',
              'required_on_targets_of', 'governs_anchor', 'value_form', 'value_pattern',
              'canonical_note', 'compare_form', 'on_sequence')
_LIST_KEYS = ('cells', 'values', 'values_add', 'entry_one_of', 'entry_must_match')
_MAP_KEYS = ('attrs', 'alt_form', 'expiry', 'value_in_registry')
_IN_NAMES = ('registry', 'registry_from', 'take', 'type', 'system', 'key_of', 'form_of', 'aspect', 'quantity')
# The two verdicts the schema language names for a cell (`schema_language.cells`): `incoherent` an error, `in_breach` a
# warning. Any other word was read as `in_breach` — a misspelt `incoherent` warned where the law meant to refuse.
CELL_VERDICTS = ('incoherent', 'in_breach')


def _is_text(x):
    return isinstance(x, str) and bool(x.strip())


def _scalar(x):
    return not isinstance(x, (list, dict))


def regex_problem(pattern):
    """None when `pattern` is a regular expression `law_match` can match with (text, compiled as it compiles it); else
    what is wrong with it — the compiler's reason, never the pattern echoed."""
    if not isinstance(pattern, str):
        return f"is a regular expression written as text, not {type(pattern).__name__}"
    try:
        re.compile(pattern, re.ASCII)
    except (re.error, ValueError) as e:
        return f"is not a regular expression: {e}"
    return None


def _names_problem(v, one_or_list=False):
    """None when `v` is absent, or a list of attribute names (or, `one_or_list`, one name); else what it should be."""
    if v is None or (one_or_list and _is_text(v)) or (isinstance(v, list) and v and all(_is_text(x) for x in v)):
        return None
    return ("names one attribute, or a list of them, each as text" if one_or_list
            else "is a list of attributes, each named as text")


def _groups_problem(v):
    """None when `v` is absent or a list of GROUPS, each a list of two or more attribute names; else what it should be."""
    if v is None or (isinstance(v, list) and v and all(isinstance(g, list) and len(g) > 1 and all(_is_text(x) for x in g)
                                                       for g in v)):
        return None
    return "is a list of groups, each a list of two or more attributes named as text — `[[u, accuracy]]`"


def _attrs_problem(attrs, at):
    """What is wrong with the shape of a schema's `attrs` (and the entries nested in one), or None."""
    if not isinstance(attrs, dict):
        return f"`{at}` is a mapping of attribute to record, not {type(attrs).__name__}"
    for a, rec in attrs.items():
        d = rec.get('in') if isinstance(rec, dict) else None
        if not isinstance(d, dict):
            continue                        # a record with no domain the language offers is refused by name later
        for k in _IN_NAMES + (() if d.get('entries') is not None else ('keyed_by',)):
            if d.get(k) is not None and not _is_text(d[k]):
                return f"`{at}.{a}.in.{k}` names one {k}, written as text — not {type(d[k]).__name__}"
        # `keyed_by` beside `entries` may name several attributes (24.0), and beside `form_of` names one
        if d.get('entries') is not None:
            for k, _p in (('keyed_by', _names_problem(d.get('keyed_by'), one_or_list=True)),
                          ('one_of', _names_problem(d.get('one_of'))),
                          ('at_most_one_of', _groups_problem(d.get('at_most_one_of')))):
                if _p:
                    return f"`{at}.{a}.in.{k}` {_p}"
        if 'pattern' in d and regex_problem(d['pattern']):
            return f"`{at}.{a}.in.pattern` {regex_problem(d['pattern'])}"
        # `{ gene: [...] }` and nothing else (22.0: `kinds` until then) — a key it does not read would hold the id to no
        # genos at all, and say nothing
        if d.get('bean_id') is not None and not (isinstance(d['bean_id'], dict) and set(d['bean_id']) <= {'gene'}
                                                  and isinstance(d['bean_id'].get('gene') or [], list)):
            return f"`{at}.{a}.in.bean_id` is a mapping {{ gene: [<genos>, ...] }}, its gene a list"
        if d.get('where') is not None and not isinstance(d['where'], dict):
            return f"`{at}.{a}.in.where` is a mapping of a registry's field to the value it holds"
        if d.get('entries') is not None:
            _p = _attrs_problem(d['entries'], f"{at}.{a}.in.entries")
            if _p:
                return _p
    return None


def _cell_problem(c):
    """What is wrong with one cell of a schema (`{when, verdict | requires | expects, why}`), or None."""
    if not isinstance(c, dict) or not isinstance(c.get('when'), dict) or not c['when']:
        return "is a mapping {when: {<attr>: <value>, …}, verdict | requires: [...] | expects: [...], why}"
    for a, v in c['when'].items():
        if isinstance(v, dict) and not (list(v) == ['starts_with'] and _is_text(v['starts_with'])):
            return f"`when.{a}` is a value, a list of values or {{starts_with: <text>}} — not another mapping"
        if isinstance(v, list) and not all(_scalar(x) for x in v):
            return f"`when.{a}` is a list of values, each one value"
    said = [k for k in ('verdict', 'requires', 'expects') if c.get(k) is not None]
    if len(said) != 1:
        return (f"says one of `verdict`, `requires` or `expects` — "
                + (f"it says {len(said)}: {', '.join(said)}" if said else "it says none"))
    if c.get('verdict') is not None and c['verdict'] not in CELL_VERDICTS:
        return f"`verdict` is one of {list(CELL_VERDICTS)}" + (
            f", not {type(c['verdict']).__name__}" if not isinstance(c['verdict'], str) else '')
    for k in ('requires', 'expects'):
        if c.get(k) is not None and not (isinstance(c[k], list) and c[k] and all(_is_text(x) for x in c[k])):
            return f"`{k}` is a list of the attributes an entry in the cell must carry, each named as text"
    if c.get('why') is not None and not isinstance(c['why'], str):
        return f"`why` is text, not {type(c['why']).__name__}"
    return None


def term_problem(t):
    """What is wrong with the shape of one `local_terms` entry, or None."""
    if not isinstance(t, dict):
        return f"is a mapping {{term, meaning, schema?, …}}, not {type(t).__name__}"
    if not _is_text(t.get('term')):
        return f"names its term as text (`term: <name>`), not {type(t.get('term')).__name__}"
    for k in ('schema', 'merge', 'anchor'):
        if t.get(k) is not None and not isinstance(t[k], dict):
            return f"`{k}` is a mapping, not {type(t[k]).__name__}"
    _ck = t.get('context_keys')
    if _ck is not None and not (isinstance(_ck, list) and all(_is_text(x) for x in _ck)):
        return "`context_keys` is a list of the keys it is found at, each written as text"
    s = t.get('schema') or {}
    for k in _NAME_KEYS:
        if s.get(k) is not None and not isinstance(s[k], str):
            return f"`schema.{k}` is one word, written as text — not {type(s[k]).__name__}"
    if s.get('value_pattern') is not None and regex_problem(s['value_pattern']):
        return f"`schema.value_pattern` {regex_problem(s['value_pattern'])}"
    for k in _LIST_KEYS + tuple(x for x in s if str(x).startswith(('required_on_', 'only_on_'))):
        if s.get(k) is not None and not isinstance(s[k], list):
            return f"`schema.{k}` is a list, not {type(s[k]).__name__}"
        if k not in ('cells', 'entry_must_match') and not all(_scalar(x) for x in (s.get(k) or [])):
            return f"`schema.{k}` is a list of values, each one value — not a list or a mapping"
    for k in _MAP_KEYS:
        if s.get(k) is not None and not isinstance(s[k], dict):
            return f"`schema.{k}` is a mapping, not {type(s[k]).__name__}"
    # `sums` (28.1): one rule, a mapping — or several, a list of them
    _sm = s.get('sums')
    if _sm is not None and not (isinstance(_sm, dict) or (isinstance(_sm, list) and all(isinstance(x, dict) for x in _sm))):
        return f"`schema.sums` is a rule, a mapping — or a list of rules — not {type(_sm).__name__}"
    # 24.0: `at_most_one_of` a list of groups; `keyed_by` one attribute or several; `exclusive` {extent, being, role?}
    for k, _p in (('at_most_one_of', _groups_problem(s.get('at_most_one_of'))),
                  ('keyed_by', _names_problem(s.get('keyed_by'), one_or_list=True))):
        if _p:
            return f"`schema.{k}` {_p}"
    _ex = s.get('exclusive')
    if _ex is not None and not (isinstance(_ex, dict) and _is_text(_ex.get('extent')) and _is_text(_ex.get('being'))
                                and set(_ex) <= {'extent', 'being', 'role'} and (_ex.get('role') is None or _is_text(_ex['role']))):
        return "`schema.exclusive` is a mapping {extent: <attr>, being: <attr>, role?: <attr>}, each an attribute named as text"
    _alt = s.get('alt_form')
    if _alt is not None:
        if not _is_text(_alt.get('key')):
            return "`schema.alt_form.key` names the one key of the alternative form, as text"
        # {key, ref_fields}: beside its key, the form names the keys that hold a ref — each a list of names
        for _k, _v in _alt.items():
            if _k != 'key' and not (isinstance(_v, list) and all(_is_text(x) for x in _v)):
                return f"`schema.alt_form.{_k}` is a list of the keys that hold a ref, each named as text"
    for i, c in enumerate(s.get('cells') or []):
        _p = _cell_problem(c)
        if _p:
            return f"`schema.cells[{i}]` {_p}"
    return _attrs_problem(s['attrs'], 'schema.attrs') if s.get('attrs') is not None else None


def genos_problem(k):
    """What is wrong with the shape of one `local_gene` entry, or None."""
    if not isinstance(k, dict):
        return f"is a mapping {{genos, of_nature, meaning, …}}, not {type(k).__name__}"
    if not _is_text(k.get('genos')):
        return f"names its genos as text (`genos: <name>`), not {type(k.get('genos')).__name__}"
    for a, v in k.items():
        if a == 'alive_while' and isinstance(v, dict):
            # a genos's life: `{known, by}`, each said as text — the gate reads which of the law's four ways it is
            if not (set(v) <= {'known', 'by'} and all(_is_text(x) for x in v.values())):
                return "`alive_while` is a mapping {known, by}, each said as text"
            continue
        if isinstance(v, dict) or (isinstance(v, list) and not all(_is_text(x) for x in v)):
            return f"`{a}` is a word or a list of words"
    return None


def vacancy_problem(v):
    """What is wrong with the shape of one `vacancies` entry, or None. A reason off the declared list, or a missing
    `why`, is the reverse gate's to say: it reads a vacancy it can index."""
    if not isinstance(v, dict):
        return f"is a mapping {{at, position, reason, why}}, not {type(v).__name__}"
    if not _is_text(v.get('at')) or not _scalar(v.get('position')):
        return "says `at:` where, as text, and `position:` which, as one value"
    for k in ('reason', 'why'):
        if v.get(k) is not None and not isinstance(v[k], str):
            return f"says its `{k}:` as text, not {type(v[k]).__name__}"
    return None


def row_problem(row):
    """What is wrong with one row a garden writes into a registry, or None: a mapping of its fields, named by the first,
    as text — the name every table of the law is looked up by — and a `pattern` it declares is one `law_match` reads."""
    if not (isinstance(row, dict) and row and _is_text(row[next(iter(row))])):
        return f"is a row — a mapping of its fields, named by the first, as text — not {type(row).__name__}"
    return pattern_problem(row)


def pattern_problem(row):
    """`pattern` of a registry row, when it declares one, is a regular expression — or `none`, deliberately no form."""
    if isinstance(row, dict) and row.get('pattern') is not None and row['pattern'] != 'none' \
            and regex_problem(row['pattern']):
        return f"`pattern` {regex_problem(row['pattern'])}"
    return None


def rows_read(where, rows):
    """(the rows read, the refusals): each row of a registry a garden writes, in its shape, or refused by name."""
    kept, out = [], []
    for i, r in enumerate(rows):
        why = row_problem(r)
        if why:
            _name = r[next(iter(r))] if isinstance(r, dict) and r and _is_text(r[next(iter(r))]) else None
            out.append(f"VOCAB.md: {where}" + (f" '{_name}'" if _name else f"[{i}]") + f" {why} — it is left unread "
                       f"until it is one")
        else:
            kept.append(r)
    return kept, out


def vocab_read(vocab):
    """Read a garden's VOCAB.md front matter (a mapping) in its own shape: each block, each entry of a block, each row it
    adds to a registry. What is not in its shape is taken OUT of `vocab`, in place, and the refusals are returned, each
    naming the entry and what it should be. A registry the garden restates whole is read where it is used
    (`restated_rows`), since a garden that restates none must not be told about one."""
    out = []
    for blk, shape in VOCAB_BLOCKS:
        if vocab.get(blk) is not None and not isinstance(vocab[blk], shape):
            out.append(f"VOCAB.md: `{blk}` is a {'list' if shape is list else 'mapping'}, not "
                       f"{type(vocab[blk]).__name__} — it is left unread until it is one")
            vocab[blk] = shape()

    def keep(block, problem, label):
        kept = []
        for i, row in enumerate(vocab.get(block) or []):
            why = problem(row)
            if why:
                _name = row.get(label) if isinstance(row, dict) and _is_text(row.get(label)) else None
                out.append(f"VOCAB.md: {block}" + (f" '{_name}'" if _name else f"[{i}]") + f" {why} — it is left "
                           f"unread until it is")
            else:
                kept.append(row)
        if vocab.get(block) is not None:
            vocab[block] = kept
    keep('local_terms', term_problem, 'term')
    keep('local_gene', genos_problem, 'genos')
    keep('vacancies', vacancy_problem, 'at')
    keep('extends_profiles', lambda p: None if _is_text(p) else f"names a profile as text, not {type(p).__name__}", '')
    keep('registry_files', lambda r: None if isinstance(r, dict) and all(_is_text(r.get(k)) for k in ('registry', 'file'))
         else "is a mapping {registry, file, key}, each named as text", 'registry')
    # a registry the garden holds of its own (`registry_files`) declares its form as the law's do (26.0)
    for _reg in list(vocab.get('registry_forms') or {}):
        _cols = vocab['registry_forms'][_reg]
        if not (isinstance(_cols, dict) and all(_is_text(c) and (v in ('required', 'optional') or isinstance(v, dict))
                                                for c, v in _cols.items())):
            out.append(f"VOCAB.md: `registry_forms.{_reg}` is a mapping of each column to `required`, `optional` or "
                       f"{{required?, in: {{registry, take}}?, acyclic?, rooted?, why?}} — it is left unread until it is one")
            vocab['registry_forms'].pop(_reg)
    for _reg in list(vocab.get('registry_additions') or {}):
        _rows = vocab['registry_additions'][_reg]
        if not isinstance(_rows, list):
            out.append(f"VOCAB.md: `registry_additions.{_reg}` is a list of rows, not {type(_rows).__name__} — it is "
                       f"left unread until it is one")
            _rows = []
        vocab['registry_additions'][_reg], _why = rows_read(f"registry_additions.{_reg}", _rows)
        out += _why
    # IDENTITY POLICY: a garden that restates it restates it whole, in its own shape — else the law's stands.
    _idp = vocab.get('identity_policy')
    if isinstance(_idp, dict):
        _why = next((f"`{k}` names one {k}, as text" for k in ('keyed_by', 'registry', 'anchor_key',
                     'applies_at_identity_status', 'establishing_family') if _idp.get(k) is not None and not _is_text(_idp[k])), None)
        if _why is None and _idp.get('anchor_attrs') is not None and not (
                isinstance(_idp['anchor_attrs'], list) and all(_is_text(x) for x in _idp['anchor_attrs'])):
            _why = "`anchor_attrs` is a list of the attributes an anchor may carry, each named as text"
        if _why is None and _idp.get('minted') is not None and not (isinstance(_idp['minted'], dict) and all(
                _is_text(v) for k, v in _idp['minted'].items() if k != 'meaning')):
            _why = "`minted` is a mapping {qualified_by, pattern, form, form_genos, meaning}, each written as text"
        if _why is None and isinstance(_idp.get('minted'), dict):
            _why = next((f"`minted.{k}` {regex_problem(_idp['minted'][k])}" for k in ('pattern', 'form')
                         if _idp['minted'].get(k) is not None and regex_problem(_idp['minted'][k])), None)
        if _why:
            out.append(f"VOCAB.md: identity_policy {_why} — the law's identity policy is read until it is")
            vocab['identity_policy'] = None
    return out


def registry_links(*laws):
    """Every column that names a row of another registry, as `{from, field, to, take, acyclic?, rooted?, why?}`: read from
    the laws' `registry_forms` (26.0, where a column says where its values come from), the law's first and a garden's
    after. One reading, so no tool keeps a list of links beside the law."""
    out = []
    for law in laws:
        for reg, cols in sorted(((law or {}).get('registry_forms') or {}).items()) if isinstance(law, dict) else ():
            for col, spec in (cols.items() if isinstance(cols, dict) else ()):
                _in = spec.get('in') if isinstance(spec, dict) else None
                if isinstance(_in, dict) and _is_text(_in.get('registry')) and _is_text(_in.get('take')):
                    out.append({'from': reg, 'field': col, 'to': _in['registry'], 'take': _in['take'],
                                **{k: spec[k] for k in ('acyclic', 'rooted', 'why') if spec.get(k) is not None}})
    return out


def registry_form(spec):
    """(required, the column's spec as a mapping) for one column of a registry's form: `required`, `optional`, or a
    mapping `{required?, in?, acyclic?, rooted?, why?}`."""
    if spec == 'required':
        return True, {}
    if spec == 'optional':
        return False, {}
    return bool(isinstance(spec, dict) and spec.get('required')), (spec if isinstance(spec, dict) else {})


def restated_rows(vocab, name):
    """(rows, refusals) for a registry the garden restates whole under its own name: rows None when it restates none, or
    restates it as something other than a list of rows (refused by name — the law's rows then stand)."""
    if vocab.get(name) is None:
        return None, []
    if not isinstance(vocab[name], list):
        return None, [f"VOCAB.md: `{name}` restates a registry as a list of rows, not {type(vocab[name]).__name__} — "
                      f"it is left unread until it is one"]
    return rows_read(name, vocab[name])
