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
what the LAW says of the position, never by a list kept here:
  1. an optional date attribute of a term — the law's `in: { type: date }`, not required, and not a stamp (`as_of`,
     `observed`) — is shown EMPTY, with the law's own meaning of it as a comment at the end of the line. An empty
     value is a valid absence: the gate reads it as no value, and a copy left unfilled records exactly that nobody
     said the day. Nothing invalid is shown: a placeholder the gate refused would push a writer to fill it with
     something, and that something is the invented day;
  2. every `as_of:` of a provenance is `now` — the day of writing is the clock's, and `bin/dmjournal.py` (which
     `bin/dmsave.py` calls) writes the day of the heading it stamps in its place;
  3. a calendar day inside an anchor's value (`event:dinner-at-sams-2026-09-12`) is cut: an identity is not dated;
  4. a REQUIRED position someone said — a moment in a time system, `timing`'s `at` — cannot be shown empty, since the
     gate would refuse the form; it keeps the example's value, and the line says at its end that the value is the
     example's own, and the one to write is the moment someone said;
  5. where the law's meaning of such a date also writes the day nobody said in its long form (27.0: a sentence holding
     `{ system: … }`), the FIRST line of the page that empties it carries that sentence too — once, where a writer
     meets the position first, and not on every line after it, so the page stays short;
  6. except where the law says what an EMPTY value of the position records (29.2: `empty` in its record), because another
     rule reads it: an empty `accepted` records no acceptance, and so no consent (F2). There a copy left empty says
     something false whenever the act is known and only its day is not, so every line that empties it says, instead of
     'empty unless said', that a day nobody said is `event-anchored` (in full on the first line, as rule 5) and what
     empty records — measured in queue-44, where an agent copied the third form's `accepted:` empty, was refused eight
     times, and then wrote the day of the run.
The prose around the blocks is FORMS.md's own and is not touched.

TWO PAIRS (v1 part 9): until v1 part 13 a release carries the core's guides (core/guide/) beside today's, and each pair
is derived by the law it is written in — the core's by four rules of its own, below `core_form_of`.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dmparse  # noqa: E402 — the one loader, and UTF-8 streams on every platform
import dmform   # noqa: E402 — the one reader of how the law spells an attribute
import dmpass   # noqa: E402 — where a position's value may come from (`acts`, `origin`)

# The rows of the flow law this tool checks, and the fixture that shows it (`bin/dmpass.py --flows` computes the guard).
GUARDS = {
    'law-derived': {'checks': "every form the guide shows is derived from the law, and `--check` refuses one that is not",
                    'proof': 'test/docs.py', 'label': "seed/FORMS.md holds the shapes of six recipes"},
}

ROOT = os.path.dirname(HERE)
FORMS, COOKBOOK, LAW = (os.path.join(ROOT, 'seed', f) for f in ('FORMS.md', 'COOKBOOK.md', 'std-vocab.md'))
DAY = r'\d{4}-\d{2}-\d{2}'


def said_dates():
    """{(term, attribute): the law's meaning, first clause} for every optional date attribute whose origin is `act: said` —
    someone's word, not a reading of the clock or the world (bin/dmpass.py `Origins`)."""
    return _said_meanings()[0]


def unsaid_forms():
    """{(term, attribute): the sentence of the law's meaning that writes the day nobody said long} (rule 5)."""
    return _said_meanings()[1]


def empty_meanings():
    """{(term, attribute): what the law says an empty value of the position records} (rule 6)."""
    return _said_meanings()[2]


def _said_meanings():
    law = dmparse.loads(dmparse.split_front_matter(open(LAW, encoding='utf-8').read())[0]) or {}
    out, unsaid, empty, origins = {}, {}, {}, dmpass.Origins(law)
    for t in law.get('terms') or []:
        sch = t.get('schema') if isinstance(t, dict) else None
        if not isinstance(sch, dict):
            continue
        for attr, rec in (dmform.attribute_form(t.get('term'), sch).get('attrs') or {}).items():
            if (rec.get('type') == 'position' and not rec.get('required')
                    and origins.said(origins.of((sch.get('attrs') or {}).get(attr)))):
                sentences = re.split(r'(?<=[a-z])\. ', str(rec.get('meaning') or '').replace('optional: ', ''))
                out[(t.get('term'), attr)] = sentences[0].rstrip('.')
                longs = [x.rstrip('.') for x in sentences[1:] if '`{ system:' in x]
                if longs:
                    unsaid[(t.get('term'), attr)] = longs[0]
                if ((sch.get('attrs') or {}).get(attr) or {}).get('empty'):
                    empty[(t.get('term'), attr)] = str(sch['attrs'][attr]['empty']).rstrip('.')
    return out, unsaid, empty


def said_positions():
    """{(term, attribute)} of every REQUIRED position whose origin is `act: said`: a moment in a time system, which a form
    cannot show empty (rule 4)."""
    law = dmparse.loads(dmparse.split_front_matter(open(LAW, encoding='utf-8').read())[0]) or {}
    out, origins = set(), dmpass.Origins(law)
    for t in law.get('terms') or []:
        sch = t.get('schema') if isinstance(t, dict) else None
        if not isinstance(sch, dict):
            continue
        for attr, rec in (dmform.attribute_form(t.get('term'), sch).get('attrs') or {}).items():
            if (rec.get('required') and isinstance(rec.get('system_from'), dict)
                    and origins.said(origins.of((sch.get('attrs') or {}).get(attr)))):
                out.add((t.get('term'), attr))
    return out


def form_of(block, said, positions=frozenset(), unsaid=None, shown=None, empty=None):
    """One cookbook block as the forms show it. `shown` is the set, kept across the page, of the positions whose day
    nobody said has been written long already (rule 5)."""
    unsaid, empty = unsaid or {}, empty or {}
    shown = shown if shown is not None else set()
    out = []
    entry = re.match(r'<!-- example-entry: \S+ ([a-z_]+)\.', block)       # an entry shown alone names its term in its marker
    term = entry.group(1) if entry else None
    for line in block.split('\n'):
        top = re.match(r'([a-z_]+):', line)
        if top:
            term = top.group(1)
        emptied = []
        for (t, attr), meaning in said.items():
            if t != term:
                continue
            pat = re.compile(r'(\b' + attr + r':) ?' + DAY + r'\b')
            if pat.search(line):
                line = pat.sub(r'\1 ', line).replace(': ,', ': ,').replace(':  ', ': ')
                long_ = unsaid.get((t, attr)) if (t, attr) not in shown else None
                shown.add((t, attr))
                if (t, attr) in empty and unsaid.get((t, attr)):          # rule 6: on every line, and no 'unless'
                    emptied.append(f"{attr}: {meaning}" + (f" — {long_[0].lower()}{long_[1:]}" if long_ else
                                                           ", or unsaid, `event-anchored`") + f"; empty records {empty[(t, attr)]}")
                    continue
                emptied.append(f"{attr}: {meaning}; empty unless said" + (f" — {long_[0].lower()}{long_[1:]}" if long_ else ''))
        line = re.sub(r'(\bas_of:) ?' + DAY + r'\b', r'\1 now', line)
        line = re.sub(r'(\bvalue: "[^"]*?)-' + DAY + '"', r'\1"', line)
        for (t, attr) in positions:
            if t == term and re.search(r'\b' + attr + r': "?' + DAY, line):
                emptied.append(f"{attr}: the example's")
        if emptied:
            line = re.sub(r'\s+$', '', line) + '   # ' + '; '.join(emptied)
        out.append(line)
    return '\n'.join(out)


def _sections(t):
    return {s.split('\n', 1)[0]: s for s in t.split('\n## ')[1:]}


BLOCK = re.compile(r'(?:^<!-- [^\n]*-->\n)?^```[^\n]*\n.*?^```$', re.S | re.M)


def derive(forms_text, cookbook_text, said, positions=frozenset(), unsaid=None, empty=None):
    """FORMS.md with each recipe section's blocks replaced by the forms of the cookbook's, in order."""
    ck, shown = _sections(cookbook_text), set()
    head, *secs = forms_text.split('\n## ')
    for i, sec in enumerate(secs):
        name = sec.split('\n', 1)[0]
        if name not in ck:              # the forms' own blocks (what nobody said): the same rules, on themselves
            secs[i] = BLOCK.sub(lambda m: form_of(m.group(0), said, positions, unsaid, shown, empty), sec)
            continue
        want = [form_of(b, said, positions, unsaid, shown, empty) for b in BLOCK.findall(ck[name])]
        have = BLOCK.findall(sec)
        if len(want) != len(have):
            raise SystemExit(f"dmforms: '{name}' holds {len(have)} blocks and the cookbook's {len(want)} — the sections no "
                             f"longer match; copy the recipe's blocks into FORMS.md again")
        pieces, at = [], 0
        for m, new in zip(BLOCK.finditer(sec), want):
            pieces += [sec[at:m.start()], new]
            at = m.end()
        secs[i] = ''.join(pieces) + sec[at:]
    return '\n## '.join([head] + secs)


# ---- the core's guides (v1 part 9) ----------------------------------------------------------------------------------
# A release carries the core's guides beside today's until v1 part 13 puts them in their place (core/guide/), and each
# pair is derived by the law it is written in: today's by std-vocab, the core's by the core's law. In statements the same
# shape carries the rule, by the verbs' rows: a statement line is `- <verb>: { <role>: <filler>, … }`, and a moment in it
#   1. at a knowing act's `at` (core.yaml `knowing`: say, read, derive, make) is `now`: the save writes the moment;
#   2. inside a `name`'s `as` (an identity) is cut: an identity is not dated;
#   3. in a role the verb REQUIRES (its row's `required`) keeps the example's value, since a form without it is refused,
#      and the line says at its end that the value is the example's, and the one to write is the moment someone said;
#   4. in a role the verb does not require is left out of the form, and the line says so: a role nobody said is left
#      out (the core has no empty value), and a copy then records exactly that nobody said it.
CORE_FORMS, CORE_COOKBOOK = (os.path.join(ROOT, 'core', 'guide', f) for f in ('FORMS.md', 'COOKBOOK.md'))
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
            raise SystemExit(f"forms: core/guide/FORMS.md's '{name}' holds {len(have)} blocks and the cookbook's "
                             f"{len(want)} — the sections no longer match; copy the recipe's blocks into it again")
        pieces, at = [], 0
        for m, new in zip(BLOCK.finditer(sec), want):
            pieces += [sec[at:m.start()], new]
            at = m.end()
        secs[i] = ''.join(pieces) + sec[at:]
    return '\n## '.join([head] + secs)


def _pairs():
    """(the forms' path, its text, the text derived) of each pair of guides this tree carries, by the law it is in."""
    out = []
    if os.path.isfile(FORMS) and os.path.isfile(COOKBOOK) and os.path.isfile(LAW):
        forms = open(FORMS, encoding='utf-8').read()
        out.append((FORMS, forms, derive(forms, open(COOKBOOK, encoding='utf-8').read(), said_dates(),
                                         said_positions(), unsaid_forms(), empty_meanings())))
    if os.path.isfile(CORE_FORMS) and os.path.isfile(CORE_COOKBOOK):
        forms = open(CORE_FORMS, encoding='utf-8').read()
        out.append((CORE_FORMS, forms, core_derive(forms, open(CORE_COOKBOOK, encoding='utf-8').read(), core_law())))
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
