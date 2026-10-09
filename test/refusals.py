#!/usr/bin/env python3
"""What the core's gate refuses, and that it REFUSES rather than crashes (v1 part 12: today's suite, ported to the core).

A refusal is the gate's whole answer to a person: what is wrong, and what to write instead. A traceback is no answer —
the commit is blocked with nothing said, and every other finding of the run is lost with it. Each case here is a value
today's gate once took, or once died on, written as a garden of the core would meet it; each must be refused by name
by the core's gate (`core/check.py`, the hook's `--staged` too), and nothing may end in a traceback.

  the manifest  judged as itself: a gardener naming no bean, or none; `garden:` or `extends:` missing; a name out of
                kebab-case; a release nobody made; a key the manifest has not; front matter that is a list or a word
                (and the same for VOCAB.md and a bean) — and a fresh garden, and an untagged one, still pass
  VOCAB.md      rows of the wrong shape, a profile the law does not offer, a garden's own system
                whose pattern does not compile
  a bean        no front matter, YAML that does not parse, `statements` that are not a list, a statement that is not
                one verb and its roles, an id or a kind that is not one word, a title that is not text, a header key of
                today's words — each by name
  numbers       what YAML 1.1 reads as a number nobody wrote (`010`, `0x64`, `1:30`, `1_000`, `!!int 010`), a count
                past the forty digits a side every reader holds exactly — and forty digits, and `0.50`, pass
  days          a day its calendar does not have (a 30 Esfand of a common year too), a year past four digits, a
                position written as a list or a mapping
  keys          a key YAML 1.1 reads as a boolean, written as a role; a key written twice
  text          a control character in a value or a key — an escape that drives a terminal, a NUL a backslash made, a
                line feed in a value written on one line — named as U+XXXX and never echoed; a block scalar holds lines
  encodings     a bean with a byte-order mark and CRLF line ends passes; one in UTF-16 or a Windows code page is refused,
                saying what it looks like and to save it as UTF-8 — a bean and a VOCAB.md alike
  the readers   bin/rules.py over a VOCAB.md that does not read lists the law's rules, never a traceback

What today's gate refused only at a commit — a journal line some readers split, a typed heading, a private-key block in
any staged file — the core's commit refuses too, held by test/core_save.py; test/ported.yaml says where each of
today's promises went.

Run: python3 test/refusals.py   (0 = green)
"""
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'test'))
import grow  # noqa: E402

FAILS = []
TRACEBACKS = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:900]))
    if not cond:
        FAILS.append(name)


T = tempfile.mkdtemp(prefix='core-refusals-')
G = os.path.join(T, 'garden-r')


def path(p):
    return os.path.join(G, p)


def write(p, t):
    os.makedirs(os.path.dirname(path(p)), exist_ok=True)
    with open(path(p), 'wb') as fh:
        fh.write(t if isinstance(t, bytes) else t.encode('utf-8'))


def gate(*a):
    r = grow.run(sys.executable, os.path.join(G, 'core', 'check.py'), *(a or ('.',)), cwd=G)
    if 'Traceback' in r.out:
        TRACEBACKS.append((a, r.out[-600:]))
    return r


def judged(files, staged=False):
    """The gate's verdict with `files` written over the garden, which is put back after."""
    before = {f: open(path(f), 'rb').read() if os.path.exists(path(f)) else None for f in files}
    try:
        for f, t in files.items():
            write(f, t)
        if staged:
            grow.run('git', 'add', '-A', cwd=G)
            return gate('--staged')
        return gate()
    finally:
        for f, t in before.items():
            if t is None:
                os.remove(path(f))
            else:
                write(f, t)
        if staged:
            grow.run('git', 'reset', '-q', cwd=G)


def refused(name, files, *says, staged=False, rule=None):
    r = judged(files, staged)
    lines = [ln for ln in r.out.splitlines() if ln.strip()]
    hit = [ln for ln in lines if all(s in ln for s in says) and (rule is None or ln.split()[0] == rule)]
    check(name, r.returncode == 1 and hit and 'Traceback' not in r.out, r.out[-700:])
    return r


def passes(name, files):
    r = judged(files)
    check(name, r.returncode == 0 and '0 error(s)' in r.out, r.out[-700:])


try:
    REL = grow.release(os.path.join(T, 'release'))
    r = grow.garden(REL, G, 'sam')
    check(f"a garden of the core grows from this tree (core@{grow.VERSION}), kept by sam",
          r.returncode == 0 and os.path.isfile(path('beans/sam.md')), r.out[-600:])
    GM = open(path('GARDEN.md'), encoding='utf-8').read()
    VOC = open(path('VOCAB.md'), encoding='utf-8').read()
    B = ('---\nbean: x\nkind: document\ntitle: "x"\nstatements:\n  - say: { by: sam, at: "2026-10-01 10:00+03:00" }\n'
         '%s---\nThe x.\n')

    def bean(*statements):
        return {'beans/x.md': B % ''.join(f'  - {s}\n' for s in statements)}

    def header(h):
        return {'beans/x.md': '---\n' + h + 'statements:\n  - say: { by: sam, at: now }\n---\nx\n'}

    # ---- the manifest, judged as itself
    r = gate()
    check("a fresh garden's manifest passes as written, the release it runs included", r.returncode == 0, r.out[-400:])
    passes("...and `untagged <commit>`, what germinate writes from a checkout on no tag, is a release",
           {'GARDEN.md': GM.replace('daftar_release: "v1.0.0"', 'daftar_release: "untagged 1a2b3c4"')})
    refused("a gardener naming no bean is refused, saying a garden holds a bean for its gardener",
            {'GARDEN.md': GM.replace('gardener: sam', 'gardener: nobody')}, 'GARDEN.md', 'holds a bean for', rule='form')
    refused("a manifest naming no gardener is refused, saying what to write first",
            {'GARDEN.md': GM.replace('gardener: sam', 'gardener:')}, 'names no gardener', 'write their bean', rule='form')
    refused("a manifest with no `garden:` is refused", {'GARDEN.md': GM.replace('garden: garden-r\n', '')},
            '`garden:` is missing')
    refused("a manifest with no `extends:` is refused", {'GARDEN.md': GM.replace(f'extends: core@{grow.VERSION}\n', '')},
            '`extends:` is missing')
    refused("a garden name that is not kebab-case is refused",
            {'GARDEN.md': GM.replace('garden: garden-r\n', 'garden: My_Garden\n')}, 'kebab-case')
    refused("a release nobody made is refused, naming the forms a release takes",
            {'GARDEN.md': GM.replace('daftar_release: "v1.0.0"', 'daftar_release: "banana"')}, "a release's tag")
    refused("a key the manifest has not is refused (today's `seeds_from` among them)",
            {'GARDEN.md': GM.replace('gardener: sam', 'gardener: sam\nseeds_from: elsewhere')}, 'GARDEN.md', 'seeds_from')
    for shape, fm in (('a list', '- a\n- b'), ('a word', 'hello')):
        refused(f"a manifest whose front matter is {shape} is refused by name, not a traceback",
                {'GARDEN.md': f'---\n{fm}\n---\nx\n'}, 'GARDEN.md', 'not a mapping of keys')
        refused(f"...and so is a VOCAB.md whose front matter is {shape}", {'VOCAB.md': f'---\n{fm}\n---\nx\n'},
                'VOCAB.md', 'not a mapping of keys')
        refused(f"...and a bean whose front matter is {shape}", {'beans/x.md': f'---\n{fm}\n---\nx\n'},
                'beans/x.md', 'not a mapping of keys')

    # ---- VOCAB.md: the garden's own rows, each in its shape
    refused("VOCAB.md whose `kinds` is a word is refused: a list of rows", {'VOCAB.md': '---\nkinds: hello\n---\nx\n'},
            '`kinds` is a list of rows')
    refused("...and whose rows are words: a row is a mapping", {'VOCAB.md': '---\nkinds: [a, b]\n---\nx\n'},
            'a row of `kinds` is a mapping')
    refused("...and a kind with no nature is refused, naming the natures",
            {'VOCAB.md': '---\nkinds:\n  - { kind: kiln, vacant: "a case" }\n---\nx\n'}, 'kiln', 'body, sayable')
    refused("...`profiles` written as a word is refused: a list of the profiles, each by its name",
            {'VOCAB.md': '---\nprofiles: view\n---\nx\n'}, '`profiles` is a list')
    refused("...a profile the law does not offer is refused, naming those it does",
            {'VOCAB.md': '---\nprofiles: [astrology]\n---\nx\n'}, 'astrology', 'view')
    refused("...and a garden's own system whose pattern does not compile is refused, not a traceback",
            {'VOCAB.md': '---\nsystems:\n  - { system: shelf, dimension: place, pattern: "([" }\n---\nx\n'},
            'does not compile')

    # ---- a bean, in its form
    refused("a bean with no front matter is refused, saying how one opens", {'beans/x.md': 'just text\n'},
            'has no front matter')
    refused("a bean whose YAML does not parse is refused, naming where", {'beans/x.md': '---\nbean: [x\n---\nx\n'},
            'does not parse as YAML')
    for what, st in (('a mapping', 'statements: { say: { by: sam } }'), ('a word', 'statements: hello')):
        refused(f"`statements` written as {what} is refused: a list, each item one verb and its roles",
                {'beans/x.md': f'---\nbean: x\nkind: document\ntitle: x\n{st}\n---\nx\n'}, '`statements` is a list')
    for what, st in (('a word', 'hello'), ('two verbs', '{ mark: { by: sam, at: now }, pay: { by: sam } }'),
                     ('its roles a list', 'mark: [a, b]'), ('its roles a word', 'mark: hello')):
        refused(f"a statement that is {what} is refused: one verb and its roles", bean(st), 'one verb and its roles')
    refused("a statement's id written as a list is refused: one word", bean('mark: { id: [a], by: sam, at: now }'),
            'its id', 'one word')
    refused("a bean's id written as a list is refused: it names itself as its file does",
            header('bean: [x]\nkind: document\ntitle: x\n'), 'names itself as its file does')
    refused("a kind written as a list is refused by name, not a traceback", header('bean: x\nkind: [document]\ntitle: x\n'),
            '`kind` is one word')
    refused("a kind the law has not is refused", header('bean: x\nkind: spaceship\ntitle: x\n'), 'spaceship',
            'no kind of the law')
    refused("a title written as a mapping is refused: it is text", header('bean: x\nkind: document\ntitle: { a: b }\n'),
            '`title` is text')
    refused("a bean named otherwise than its file is refused", header('bean: y\nkind: document\ntitle: x\n'), '`bean: y`')
    refused("a bean in today's words is refused, naming what replaces them",
            {'beans/x.md': '---\nbean: x\ngenos: document\ntitle: x\n'
                           'provenance: { src: observed, by: sam, as_of: 2026-10-01 }\n---\nx\n'},
            'genos', 'provenance', 'a fact is a statement')
    refused("a role filled by a mapping no shape takes is refused", bean('mark: { by: { x: { y: z } }, at: now }'),
            '`by`', rule='valency')

    # ---- numbers: what YAML 1.1 reads as a number nobody wrote, and how long a count may be
    for spelling in ('010', '!!int 010', '0x64', '1:30', '1_000'):
        refused(f"a count written `{spelling}` is refused by name, never read as a number nobody wrote",
                bean(f'pay: {{ by: sam, of: {{ count: {spelling}, unit: XTS }} }}'), 'its count', rule='valency')
    refused("a count of forty-one digits is refused: past what every reader holds exactly",
            bean('pay: { by: sam, of: { count: "%s", unit: XTS } }' % ('1' * 41)), '41 digits', 'at most 40')
    passes("...and forty digits pass, and so does `0.50`",
           bean('pay: { by: sam, of: { count: "%s", unit: XTS } }' % ('1' * 40),
                'pay: { by: sam, of: { count: "0.50", unit: XTS } }'))
    refused("a count written as a list is refused", bean('pay: { by: sam, of: { count: [1], unit: XTS } }'), 'its count')
    refused("a share written `0x1` is refused: a bare number is a count in plain decimal digits",
            bean('pay: { id: p, by: sam, of: { count: "1", unit: XTS } }', 'bear: { by: ali, of: p, share: 0x1 }'),
            "'0x1'", 'plain decimal digits')
    refused("a currency written by its name is refused: a unit is UCUM's, a currency ISO 4217's",
            bean('pay: { by: sam, of: { count: "1", unit: dollar } }'), "'dollar'", 'ISO 4217')

    # ---- days
    refused("2026-02-30 is refused: not a day of the Gregorian calendar", bean('mark: { by: sam, at: 2026-02-30 }'),
            'not a day', rule='frame')
    refused("persian:1404-12-30 is refused: 1404 is a common year, and Esfand has 29 days",
            bean('mark: { by: sam, at: "persian:1404-12-30" }'), 'persian:1404-12-30', rule='frame')
    passes("...while 30 Esfand of a leap year, persian:1403-12-30, passes", bean('mark: { by: sam, at: "persian:1403-12-30" }'))
    refused("a year past four digits is in no system's form", bean('mark: { by: sam, at: "99999-01-01" }'),
            "in no system's form", rule='frame')
    refused("a position written as a list is refused: a role takes one filler",
            bean('mark: { by: sam, at: [2026-02-03, 2026-02-04] }'), 'one filler')
    refused("...and one written as a mapping: one string in its system's form", bean('mark: { by: sam, at: { x: 1 } }'),
            'one string', rule='frame')

    # ---- keys
    refused("a key YAML 1.1 reads as a boolean (`yes`) is read as written, and refused as no role the verb takes",
            bean('mark: { by: sam, at: now, yes: x }'), '`yes` is no role', rule='form')
    refused("a key written twice is refused before YAML keeps only the last",
            bean('mark: { by: sam, by: ali, at: now }'), 'written twice')

    # ---- text: a control character named, never echoed
    for name, esc, code in (("an escape that drives a terminal", '\\x1b[31m', 'U+001B'),
                            ("a NUL a backslash made", '\\0', 'U+0000'),
                            ("a line feed in a value written on one line", '\\n', 'U+000A')):
        r = refused(f"{name} is refused by name, as {code}",
                    bean(f'mark: {{ by: sam, at: now, note: "a{esc}b" }}'), code, rule='form')
        check("...and the refusal itself holds no control character", not any(c in r.out for c in '\x1b\x00'), repr(r.out[-200:]))
    passes("a block scalar holds lines, and a tab is text",
           bean('mark:\n      by: sam\n      at: now\n      note: |\n        one line\n        and another\twith a tab'))
    refused("a key holding a control character is refused", bean('mark: { by: sam, at: now, "no\\x07te": x }'),
            'U+0007')

    # ---- bidi: a code and a name a namespace gives hold no character of Unicode's Bidi_Control, which makes them read
    # as another (Trojan Source); free text keeps them as written
    r = refused("a code holding U+202E (RIGHT-TO-LEFT OVERRIDE) is refused by name",
                bean('can: { by: sam, of: "teach", as: "isco-08:25\\u202e22" }'), 'U+202E', 'Bidi_Control',
                rule='valency')
    check("...and the refusal never echoes it", '\u202e' not in r.out, repr(r.out[-200:]))
    refused("a name the mail namespace gives, holding U+2066 (LEFT-TO-RIGHT ISOLATE), is refused by name",
            bean('name: { by: mail, of: sam, as: "sam@exa\\u2066mple.org" }'), 'U+2066', 'Bidi_Control', rule='names')
    refused("...and one holding U+200F (RIGHT-TO-LEFT MARK), a mark of no explicit bidi class",
            bean('name: { by: mail, of: sam, as: "s\\u200fam@example.org" }'), 'U+200F', rule='names')
    # ---- the namespaces' checks: each a well-used validator's (python-stdnum's, the standard library's), never a copy
    refused("an ORCID iD whose check character is wrong is refused, saying what checks it",
            bean('name: { by: orcid, of: sam, as: "0000-0002-1825-0098" }'), 'orcid-checksum', rule='names')
    passes("...and ORCID's own example passes, beside a Wikidata item and a ROR id",
           bean('name: { by: orcid, of: sam, as: "0000-0002-1825-0097" }',
                'name: { by: wikidata, of: sam, as: "Q42" }'))
    refused("a ROR id whose checksum is wrong is refused", bean('name: { by: ror, of: sam, as: "05dxps056" }'),
            'ror-checksum', rule='names')
    refused("a DICOM UID under 2.25 past 128 bits is no UUID, and is refused",
            bean('name: { by: dicom-uid, of: sam, as: "2.25.%d" }' % 2 ** 128), 'uuid-integer', rule='names')
    refused("a Turkish identity number written in a bean is refused: a government number is kept only held",
            bean('name: { by: tr-tckn, of: sam, as: "10000000146" }'), 'tr-tckn', 'held', rule='harm')
    refused("...and an Iranian national code alike",
            bean('name: { by: ir-national-code, of: sam, as: "0012345678" }'), 'ir-national-code', 'held',
            rule='harm')
    passes("free text keeps them: a note holding U+200F, and a person's name holding ZWNJ (U+200C, no bidi control)",
           bean('mark: { by: sam, at: now, note: "\\u0633\\u0644\\u0627\\u0645\\u200f 12" }',
                'name: { by: sam, of: sam, as: "\\u0645\\u06cc\\u200c\\u062e\\u0648\\u0627\\u0647\\u0645" }'))

    # ---- encodings
    raw = (B % '').encode('utf-8')
    passes("a bean saved with a byte-order mark and CRLF line ends passes: a line end is no control character in text",
           {'beans/x.md': b'\xef\xbb\xbf' + raw.replace(b'\n', b'\r\n')})
    refused("a bean saved in UTF-16 is refused, saying what it looks like and to save it as UTF-8",
            {'beans/x.md': (B % '').encode('utf-16')}, 'UTF-16', 'save it as UTF-8')
    refused("...and one in a Windows code page", {'beans/x.md': (B % '  - mark: { by: sam, at: now, note: "café – x" }\n'
                                                                 ).encode('cp1252')}, 'code page', 'save it as UTF-8')
    refused("...and a VOCAB.md in UTF-16 alike", {'VOCAB.md': VOC.encode('utf-16')}, 'VOCAB.md', 'UTF-16')

    # ---- the commit's gate: the same refusals through the hook's --staged, never a traceback
    for name, files, says in (("a bean whose front matter is a list", {'beans/x.md': '---\n- a\n---\nx\n'}, 'not a mapping'),
                              ("a kind written as a list", header('bean: x\nkind: [document]\ntitle: x\n'), '`kind`'),
                              ("a bean in UTF-16", {'beans/x.md': (B % '').encode('utf-16')}, 'UTF-16'),
                              ("a pattern that does not compile",
                               {'VOCAB.md': '---\nsystems:\n  - { system: shelf, dimension: place, pattern: "([" }\n---\nx\n'},
                               'does not compile')):
        refused(f"--staged: {name} is refused at the commit too, by name", files, says, staged=True)

    # ---- the readers that read what the gate reads
    for what, vocab in (("does not read", '---\nhello\n---\nx\n'), ("is in UTF-16", VOC.encode('utf-16'))):
        before = open(path('VOCAB.md'), 'rb').read()
        write('VOCAB.md', vocab)
        r = grow.run(sys.executable, 'bin/rules.py', cwd=G)
        write('VOCAB.md', before)
        if 'Traceback' in r.out:
            TRACEBACKS.append(('rules', r.out[-600:]))
        check(f"bin/rules.py over a VOCAB.md that {what} lists the law's rules, never a traceback",
              'Traceback' not in r.out and 'valency' in r.out and 'consent' in r.out, r.out[-500:])

    check("NOTHING above ended in a traceback: every case is a refusal or a pass", not TRACEBACKS, TRACEBACKS[:2])
except Exception as e:  # noqa: BLE001 — a crash of the suite is a failure of it, said once
    import traceback
    check(f"the suite ran to its end ({type(e).__name__}: {e})", False, traceback.format_exc()[-900:])
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\nrefusals: {len(FAILS)} failed" + (": " + ", ".join(FAILS) if FAILS else ""))
sys.exit(1 if FAILS else 0)
