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


def read(path):
    """(front_matter_text, body) read from a file on disk."""
    with open(path, encoding='utf-8') as fh:
        return split_front_matter(fh.read())


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


def loads(text):
    """Parse YAML the one way this garden parses it. Semantically identical to yaml.safe_load."""
    if _yaml is None:
        raise RuntimeError("PyYAML required")
    return _yaml.load(text, Loader=LOADER)
