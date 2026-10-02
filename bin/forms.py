#!/usr/bin/env python3
"""forms — the forms a writer copies, derived from the cookbook's recipes by the law. They carry no fact.

    python3 bin/forms.py            # write seed/FORMS.md's recipe blocks from seed/COOKBOOK.md's
    python3 bin/forms.py --check    # exit 1 if they differ from that derivation (test/docs.py runs this)

WHY. An agent copies the SHAPE it is shown, faithfully, and fills every position the shape has. Measured on a local
model over 18 runs of one task in which nobody said a single day: every run that wrote a date wrote one nobody said —
121 of them, 102 in `accepted`, `agreed` and `day` — taken from the nearest date in view: the example's own
(2026-09-17), the machine's today, even the gardener's stamp in `beans/<gardener>.md`. The forms said in words "copy
no value from here" and "today is not the day it happened"; the model read them and wrote the dates anyway. A rule in
prose is read and not applied at the spot; a shape is applied. So the shape carries the rule.

THE DERIVATION. The recipes stay stories in the cookbook — Sam, Ali, their camera and their days — because a person
learns from a story. The forms are the same blocks, with every fact nobody could have told the reader taken out by
what the LAW says of the role a moment fills, never by a list kept here (the four rules below `core_form_of`). The
prose around the blocks is FORMS.md's own and is not touched.

"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import parse as dmparse  # noqa: E402 — the one loader, and UTF-8 streams on every platform

# The rows of the flow law this tool checks, and the fixture that shows it (`bin/pass.py --flows` computes the guard).
GUARDS = {
    'law-derived': {'checks': "every form the guide shows is derived from the law, and `--check` refuses one that is not",
                    'proof': 'test/docs.py', 'label': "seed/FORMS.md holds the shapes of six recipes"},
}

ROOT = os.path.dirname(HERE)
FORMS, COOKBOOK = (os.path.join(ROOT, 'seed', f) for f in ('FORMS.md', 'COOKBOOK.md'))
DAY = r'\d{4}-\d{2}-\d{2}'


def _sections(t):
    return {s.split('\n', 1)[0]: s for s in t.split('\n## ')[1:]}


BLOCK = re.compile(r'(?:^<!-- [^\n]*-->\n)?^```[^\n]*\n.*?^```$', re.S | re.M)


# ---- the forms, by the core's law ------------------------------------------------------------------------------------
# In statements the shape carries the rule, by the verbs' rows: a statement line is `- <verb>: { <role>: <filler>, … }`,
# and a moment in it
#   1. at a knowing act's `at` (core.yaml `knowing`: say, read, derive, make) is `now`: the save writes the moment;
#   2. inside a `name`'s `as` (an identity) is cut: an identity is not dated;
#   3. in a role the verb REQUIRES (its row's `required`) keeps the example's value, since a form without it is refused,
#      and the line says at its end that the value is the example's, and the one to write is the moment someone said;
#   4. in a role the verb does not require is left out of the form, and the line says so: a role nobody said is left
#      out (the core has no empty value), and a copy then records exactly that nobody said it.
_STATEMENT = re.compile(r'^(\s*- )([a-z][a-z0-9-]*):(\s*)\{(.*)\}(\s*)(#.*)?$')
_FILLER = r'("(?:[^"\\]|\\.)*"|\[[^\]]*\]|[^,}]+)'


def core_law(root=ROOT):
    sys.path.insert(0, root)
    from core.law import Law
    return Law.load(root=root if os.path.isdir(os.path.join(root, 'core', 'law')) else None)


def core_form_of(block, L):
    """A block of the cookbook as the form a writer copies: each statement line's moments by the four rules above."""
    out = []
    for line in block.split('\n'):
        m = _STATEMENT.match(line)
        if not m or m.group(2) not in L.verbs:
            out.append(line)
            continue
        verb, body, said = m.group(2), m.group(4), []
        req = {str(r) for r in L.verbs[verb].get('required') or []}
        for role, filler in re.findall(r'\b([a-z_]+):\s*' + _FILLER, body):
            if not re.search(DAY, filler):
                continue
            if role == 'at' and verb in L.knowing:
                body = body.replace(f"{role}: {filler}", f"{role}: now", 1)
            elif verb == 'name' and role == 'as':
                body = body.replace(filler, re.sub(r'-?' + DAY, '', filler), 1)
            elif role in req:
                said.append(f"{role}: the example's — write the moment someone said")
            else:
                body = re.sub(r'(,\s*)?\b' + role + r':\s*' + re.escape(filler.strip()) + r'(\s*,\s*)?',
                              lambda m: ', ' if m.group(1) and m.group(2) else '', body, count=1)
                said.append(f"{role}: left out unless said")
        new = f"{m.group(1)}{verb}:{m.group(3)}{{{body}}}"
        old_note = (m.group(6) or '').lstrip('# ').strip()
        notes = [n for n in [old_note] if n and n not in '; '.join(said)] + [n for n in said if n not in old_note]
        out.append(new + ('   # ' + '; '.join(notes) if notes else ''))
    return '\n'.join(out)


def core_derive(forms_text, cookbook_text, L):
    """The core's FORMS.md with each recipe section's blocks replaced by the forms of the core's cookbook's, in order;
    the forms' own blocks (what nobody said) held to the same rules."""
    ck = _sections(cookbook_text)
    head, *secs = forms_text.split('\n## ')
    for i, sec in enumerate(secs):
        name = sec.split('\n', 1)[0]
        if name not in ck:
            secs[i] = BLOCK.sub(lambda m: core_form_of(m.group(0), L), sec)
            continue
        want = [core_form_of(b, L) for b in BLOCK.findall(ck[name])]
        have = BLOCK.findall(sec)
        if len(want) != len(have):
            raise SystemExit(f"forms: seed/FORMS.md's '{name}' holds {len(have)} blocks and the cookbook's "
                             f"{len(want)} — the sections no longer match; copy the recipe's blocks into it again")
        pieces, at = [], 0
        for m, new in zip(BLOCK.finditer(sec), want):
            pieces += [sec[at:m.start()], new]
            at = m.end()
        secs[i] = ''.join(pieces) + sec[at:]
    return '\n## '.join([head] + secs)


def _pairs():
    """(the forms' path, its text, the text derived) of the guides this tree carries, by the core's law."""
    out = []
    if os.path.isfile(FORMS) and os.path.isfile(COOKBOOK):
        forms = open(FORMS, encoding='utf-8').read()
        out.append((FORMS, forms, core_derive(forms, open(COOKBOOK, encoding='utf-8').read(), core_law())))
    return out


def main(argv):
    bad = 0
    for path, forms, new in _pairs():
        rel = os.path.relpath(path, ROOT).replace(os.sep, '/')
        if '--check' in argv:
            if new != forms:
                print(f"forms: {rel}'s recipe blocks are not the forms of the cookbook's — run: python3 bin/forms.py",
                      file=sys.stderr)
                bad = 1
            continue
        if new != forms:
            open(path, 'w', encoding='utf-8', newline='\n').write(new)
            print(f'forms: {rel} written from the cookbook, by the law')
        else:
            print(f'forms: {rel} is already the forms of the cookbook')
    return bad


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
