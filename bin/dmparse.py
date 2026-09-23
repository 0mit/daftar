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
import re
import os, sys


# THE TOOLS SPEAK UTF-8 ON EVERY PLATFORM. On Windows a Python whose output goes to a pipe — which is how an agent runs a
# tool — encodes in the ANSI code page, and the first `—` or Persian letter in a finding ends the run in a traceback.
# Every tool imports this module, so it is set once here, and only where the stream is not UTF-8 already.
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
                           capture_output=True, text=True, timeout=5)
        roots = r.stdout.split()
        shallow = subprocess.run(['git', '-C', root, 'rev-parse', '--is-shallow-repository'],
                                 capture_output=True, text=True, timeout=5).stdout.strip()
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
# gate is spawned ~115 times by test/golden.py — so the whole suite was pure-Python YAML parsing.
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
# `law_carrier.invariant_no_silent_fallback`, where falling back would substitute a DIFFERENT rule.
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


def loads(text):
    """Parse YAML the one way this garden parses it. Semantically identical to yaml.safe_load."""
    if _yaml is None:
        raise RuntimeError("PyYAML required")
    return _yaml.load(text, Loader=LOADER)


# ---- A GARDEN'S VOCABULARY, READ IN ITS OWN SHAPE -----------------------------------------------------------------
# VOCAB.md is written by hand, and what the interpreter iterates must be a list, what it looks a row up by a name, what it
# prints a word, and a pattern it matches one Python compiles. So each block of it, and each ENTRY of a block, is read in
# its own shape or not at all: an entry of another shape is refused by name and left unread. A list where a name belongs
# ended the gate in a traceback, `local_terms: [5]` passed as though it said something, and a pattern that does not
# compile ended the run at the first value matched against it. ONE definition, read by the gate (which refuses what this
# leaves out) and by dmrules (which lists no rule of it), so the two never disagree about what a garden's vocabulary says.
VOCAB_BLOCKS = (('local_terms', list), ('local_kinds', list), ('vacancies', list), ('extends_profiles', list),
                ('registry_files', list), ('registry_links', list), ('registry_additions', dict),
                ('identity_policy', dict))
_NAME_KEYS = ('shape', 'key_form', 'path', 'values_from', 'must_equal_kind_attr', 'entry_form_from_kind_attr',
              'facet_parity_with', 'required_on_targets_of', 'governs_anchor', 'value_form', 'value_pattern',
              'canonical_note', 'compare_form', 'on_sequence')
_LIST_KEYS = ('cells', 'values', 'values_add', 'entry_one_of', 'entry_must_match')
_MAP_KEYS = ('attrs', 'alt_form', 'expiry', 'sums', 'value_in_registry')
_IN_NAMES = ('registry', 'registry_from', 'take', 'type', 'system', 'key_of', 'form_of', 'keyed_by', 'aspect', 'quantity')
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


def _attrs_problem(attrs, at):
    """What is wrong with the shape of a schema's `attrs` (and the entries nested in one), or None."""
    if not isinstance(attrs, dict):
        return f"`{at}` is a mapping of attribute to record, not {type(attrs).__name__}"
    for a, rec in attrs.items():
        d = rec.get('in') if isinstance(rec, dict) else None
        if not isinstance(d, dict):
            continue                        # a record with no domain the language offers is refused by name later
        for k in _IN_NAMES:
            if d.get(k) is not None and not _is_text(d[k]):
                return f"`{at}.{a}.in.{k}` names one {k}, written as text — not {type(d[k]).__name__}"
        if 'pattern' in d and regex_problem(d['pattern']):
            return f"`{at}.{a}.in.pattern` {regex_problem(d['pattern'])}"
        if d.get('bean_id') is not None and not (isinstance(d['bean_id'], dict) and isinstance(d['bean_id'].get('kinds') or [], list)):
            return f"`{at}.{a}.in.bean_id` is a mapping {{ kinds: [<kind>, ...] }}, its kinds a list"
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


def kind_problem(k):
    """What is wrong with the shape of one `local_kinds` entry, or None."""
    if not isinstance(k, dict):
        return f"is a mapping {{kind, of_nature, meaning, …}}, not {type(k).__name__}"
    if not _is_text(k.get('kind')):
        return f"names its kind as text (`kind: <name>`), not {type(k.get('kind')).__name__}"
    for a, v in k.items():
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
    keep('local_kinds', kind_problem, 'kind')
    keep('vacancies', vacancy_problem, 'at')
    keep('extends_profiles', lambda p: None if _is_text(p) else f"names a profile as text, not {type(p).__name__}", '')
    keep('registry_files', lambda r: None if isinstance(r, dict) and all(_is_text(r.get(k)) for k in ('registry', 'file'))
         else "is a mapping {registry, file, key}, each named as text", 'registry')
    keep('registry_links', lambda r: None if isinstance(r, dict) and all(_is_text(r.get(k)) for k in ('from', 'to', 'field', 'take'))
         else "is a mapping {from, to, field, take}, each named as text", 'from')
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
            _why = "`minted` is a mapping {qualified_by, pattern, form, form_kind, meaning}, each written as text"
        if _why is None and isinstance(_idp.get('minted'), dict):
            _why = next((f"`minted.{k}` {regex_problem(_idp['minted'][k])}" for k in ('pattern', 'form')
                         if _idp['minted'].get(k) is not None and regex_problem(_idp['minted'][k])), None)
        if _why:
            out.append(f"VOCAB.md: identity_policy {_why} — the law's identity policy is read until it is")
            vocab['identity_policy'] = None
    return out


def restated_rows(vocab, name):
    """(rows, refusals) for a registry the garden restates whole under its own name: rows None when it restates none, or
    restates it as something other than a list of rows (refused by name — the law's rows then stand)."""
    if vocab.get(name) is None:
        return None, []
    if not isinstance(vocab[name], list):
        return None, [f"VOCAB.md: `{name}` restates a registry as a list of rows, not {type(vocab[name]).__name__} — "
                      f"it is left unread until it is one"]
    return rows_read(name, vocab[name])
