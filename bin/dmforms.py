#!/usr/bin/env python3
"""dmforms — the forms a writer copies, derived from the cookbook's recipes by the law. They carry no fact.

    python3 bin/dmforms.py            # write seed/FORMS.md's recipe blocks from seed/COOKBOOK.md's
    python3 bin/dmforms.py --check    # exit 1 if they differ from that derivation (test/docs.py runs this)

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
  3. a calendar day inside an anchor's value (`event:dinner-at-sams-2026-09-12`) is cut: an identity is not dated.
The prose around the blocks is FORMS.md's own and is not touched.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dmparse  # noqa: E402 — the one loader, and UTF-8 streams on every platform
import dmform   # noqa: E402 — the one reader of how the law spells an attribute

ROOT = os.path.dirname(HERE)
FORMS, COOKBOOK, LAW = (os.path.join(ROOT, 'seed', f) for f in ('FORMS.md', 'COOKBOOK.md', 'std-vocab.md'))
STAMPS = ('as_of', 'observed')           # written by the tool from the clock; every other date is someone's word
DAY = r'\d{4}-\d{2}-\d{2}'


def said_dates():
    """{(term, attribute): the law's meaning, first clause} for every optional date attribute that is not a stamp."""
    law = dmparse.loads(dmparse.split_front_matter(open(LAW, encoding='utf-8').read())[0]) or {}
    out = {}
    for t in law.get('terms') or []:
        sch = t.get('schema') if isinstance(t, dict) else None
        if not isinstance(sch, dict):
            continue
        for attr, rec in (dmform.attribute_form(t.get('term'), sch).get('attrs') or {}).items():
            if rec.get('type') == 'date' and not rec.get('required') and attr not in STAMPS:
                meaning = re.split(r'(?<=[a-z])\. ', str(rec.get('meaning') or '').replace('optional: ', ''))[0].rstrip('.')
                out[(t.get('term'), attr)] = meaning
    return out


def form_of(block, said):
    """One cookbook block as the forms show it."""
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
                emptied.append(f"{attr}: {meaning}; empty unless said")
        line = re.sub(r'(\bas_of:) ?' + DAY + r'\b', r'\1 now', line)
        line = re.sub(r'(\bvalue: "[^"]*?)-' + DAY + '"', r'\1"', line)
        if emptied:
            line = re.sub(r'\s+$', '', line) + '   # ' + '; '.join(emptied)
        out.append(line)
    return '\n'.join(out)


def _sections(t):
    return {s.split('\n', 1)[0]: s for s in t.split('\n## ')[1:]}


BLOCK = re.compile(r'(?:^<!-- [^\n]*-->\n)?^```[^\n]*\n.*?^```$', re.S | re.M)


def derive(forms_text, cookbook_text, said):
    """FORMS.md with each recipe section's blocks replaced by the forms of the cookbook's, in order."""
    ck = _sections(cookbook_text)
    head, *secs = forms_text.split('\n## ')
    for i, sec in enumerate(secs):
        name = sec.split('\n', 1)[0]
        if name not in ck:              # the forms' own blocks (what nobody said): the same rules, on themselves
            secs[i] = BLOCK.sub(lambda m: form_of(m.group(0), said), sec)
            continue
        want = [form_of(b, said) for b in BLOCK.findall(ck[name])]
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


def main(argv):
    forms = open(FORMS, encoding='utf-8').read()
    new = derive(forms, open(COOKBOOK, encoding='utf-8').read(), said_dates())
    if '--check' in argv:
        if new != forms:
            print("dmforms: seed/FORMS.md's recipe blocks are not the forms of the cookbook's — run: python3 bin/dmforms.py",
                  file=sys.stderr)
            return 1
        return 0
    if new != forms:
        open(FORMS, 'w', encoding='utf-8', newline='\n').write(new)
        print('dmforms: seed/FORMS.md written from the cookbook, by the law')
    else:
        print('dmforms: seed/FORMS.md is already the forms of the cookbook')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
