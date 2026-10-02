"""read — a document's front matter, every key and value read as a string (core spec §2, choice 10).

YAML 1.1 reads the key `on:` as the boolean true and `2026-10-01` as a date object, and a reader that resolves types
makes a value the writer did not write. So the core reads with PyYAML's BaseLoader: every scalar is a str, every
mapping a dict and every sequence a list, and what a value means is the engine's to say by the role it fills. No new
dependency. The fences are dmparse's (line-anchored, the one splitter), and a key written twice is refused before the
parse can drop the first (dmparse.duplicate_keys)."""
import os
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'bin'))
import dmparse  # noqa: E402 — the one splitter of a front matter, and the one finder of a key written twice


class Unread(ValueError):
    """A document this reader will not read: no front matter, YAML that does not parse, or a key written twice."""


def loads(text, what='the document'):
    """The YAML `text` with every scalar a str. Unread for YAML that does not parse, or a key written twice."""
    try:
        dups = dmparse.duplicate_keys(text)
    except yaml.YAMLError as e:
        raise Unread(f"{what} does not parse as YAML: {_said(e)}") from None
    if dups:
        path, first, again = dups[0]
        raise Unread(f"{what}: `{path}` is written twice (lines {first} and {again}), and YAML would keep only the last")
    try:
        return yaml.load(text, Loader=yaml.BaseLoader)
    except yaml.YAMLError as e:
        raise Unread(f"{what} does not parse as YAML: {_said(e)}") from None


def _said(e):
    return ' '.join(str(e).split())[:200]


def document(path):
    """(front matter, body) of a fenced document: the front matter read by `loads`, the body as written."""
    try:
        with open(path, 'rb') as fh:
            raw = fh.read()
        text = raw.decode('utf-8').replace('\r\n', '\n').replace('\r', '\n')
    except OSError as e:
        raise Unread(f"{path} cannot be read: {e}") from None
    except UnicodeDecodeError as e:                      # said by what the file looks like, and how to save it
        raise Unread(f"{path} is {dmparse.NotUTF8(path, raw, e)}") from None
    head, body = dmparse.split_front_matter(text)
    if head is None:
        raise Unread(f"{path} has no front matter: a document opens with a line `---`, and closes its front matter "
                     f"with another")
    data = loads(head, path)
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise Unread(f"{path}: its front matter is a {type(data).__name__}, not a mapping of keys")
    return data, body


def data(path):
    """A YAML data file of the law (core.yaml, verbs.yaml), read as `loads` reads a front matter."""
    with open(path, encoding='utf-8') as fh:
        out = loads(fh.read(), path)
    if not isinstance(out, dict):
        raise Unread(f"{path} is not a mapping of keys")
    return out
