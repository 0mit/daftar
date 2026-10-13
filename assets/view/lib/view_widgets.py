#!/usr/bin/env python3
"""view_widgets — the widgets (lib/widgets/*.js) as ONE CLASSIC SCRIPT, for a page that is one file.

The widgets are ES modules: a host that serves files (daftard) imports them as they are, each from its own URL. A page
that is one file — the offline report, read from any disk, and the page `view serve` sends — cannot import one module
from another, so this writes them into one classic script: each module in a function of its own, its imports bound to
the modules written before it, its exports returned, every module under `window.daftarWidgets[<name>]`. The renderers
of the engraved archetypes (`view_queue.js`, `view_timeline.js`, `view_flows.js`, `view_books.js`, `view_sheet.js`) are classic scripts
too, and take the widgets from there — so one renderer, unchanged, runs in either kind of page.

The transform reads only the three forms the widgets are written in, and REFUSES anything else, naming the line:
    import { a, b as c } from './x.js';     import * as n from './x.js';
    export const|let|function|class NAME …   export { A as b };
test/view_handplace.py holds what each module exports here to what node imports of it. No module system, no build
step: it is done each time a page is written, from the files the release holds.
"""
import os, re

HERE = os.path.dirname(os.path.abspath(__file__))
WIDGETS = os.path.join(HERE, 'widgets')
ORDER = ('safe', 'settings', 'locale', 'number', 'exact', 'money', 'moment', 'text', 'name', 'choice', 'being', 'recurrence',
         'form', 'place', 'prefs')
_IMPORT = re.compile(r"^import\s+(?:\{([^}]*)\}|\*\s+as\s+([A-Za-z_$][\w$]*))\s+from\s+'\./([a-z]+)\.js';\s*$")
_DECL = re.compile(r"^export\s+(?:const|let|function\*?|class)\s+([A-Za-z_$][\w$]*)")
_LIST = re.compile(r"^export\s+\{([^}]*)\}\s*;\s*$")
_NAME = re.compile(r'^[A-Za-z_$][\w$]*$')


class Unread(ValueError):
    """A line of a widget this transform does not read: the page is not written, and the line is named."""


def module(name, src, known):
    """(the module as a function body, its exports {exported name: local name}) — or Unread."""
    body, exports = [], {}
    for n, ln in enumerate(src.split('\n'), 1):
        if ln.startswith('import '):
            m = _IMPORT.match(ln)
            if not m or m.group(3) not in known:
                raise Unread(f"widgets/{name}.js line {n}: an import this page cannot bind: {ln.strip()[:120]}")
            if m.group(2):
                body.append(f"const {m.group(2)} = M[{m.group(3)!r}];")
            else:
                parts = []
                for p in (x.strip() for x in m.group(1).split(',') if x.strip()):
                    a, _s, b = p.partition(' as ')
                    if not _NAME.match(a.strip()) or (b and not _NAME.match(b.strip())):
                        raise Unread(f"widgets/{name}.js line {n}: {p!r} is no name")
                    parts.append(f"{a.strip()}: {b.strip()}" if b else a.strip())
                body.append(f"const {{ {', '.join(parts)} }} = M[{m.group(3)!r}];")
            continue
        if ln.startswith('export '):
            m = _DECL.match(ln)
            if m:
                exports[m.group(1)] = m.group(1)
                body.append(ln[len('export '):])
                continue
            m = _LIST.match(ln)
            if m:
                for p in (x.strip() for x in m.group(1).split(',') if x.strip()):
                    a, _s, b = p.partition(' as ')
                    exports[(b or a).strip()] = a.strip()
                continue
            raise Unread(f"widgets/{name}.js line {n}: an export this page cannot read: {ln.strip()[:120]}")
        body.append(ln)
    return '\n'.join(body), exports


def bundle():
    """The widgets as one classic script, defining `window.daftarWidgets`."""
    out = ["/* daftar's widgets (assets/view/lib/widgets/*.js), each module in a function of its own, written into one "
           "classic script by view_widgets.py */", "(function (root) {", "'use strict';", "var M = {};"]
    known = []
    for name in ORDER:
        with open(os.path.join(WIDGETS, name + '.js'), encoding='utf-8') as fh:
            body, exports = module(name, fh.read(), known)
        ret = ', '.join(f"{k!r}: {v}" for k, v in exports.items())
        out.append(f"M[{name!r}] = (function () {{\n{body}\nreturn {{ {ret} }};\n}})();")
        known.append(name)
    out.append("root.daftarWidgets = M;")
    out.append("})(typeof window !== 'undefined' ? window : this);")
    return '\n'.join(out) + '\n'


CSS = os.path.join(WIDGETS, 'widgets.css')


def css():
    """The widgets' style for a page of one file: the font face, which names a file beside it, left out — the reader's
    own fonts write every script there."""
    with open(CSS, encoding='utf-8') as fh:
        return re.sub(r'@font-face\{[^}]*\}', '', fh.read())
