#!/usr/bin/env python3
"""The guides in statements (core/guide/), proved through the core's gate and held to what today's guides say.

Grows a garden from the seed (seed/germinate.sh) and adopts the core while it is empty: GARDEN.md's pin moves to the
core in one RULE-CHANGE, and core/install.py makes the core's gate the pre-commit hook. Then it commits every example of
core/guide/ in the order a reader meets them — README.md's first beans, its VOCAB.md row and the gardener's line, saved
by the very command README.md shows; each recipe of COOKBOOK.md and WELCOME.md with its VOCAB.md rows; FORMS.md's forms
and its forms for what nobody said — each through bin/dmsave.py and the core's gate (core/check.py --staged), and checks
each commit is made. A bean a page shows again as another page showed it is not committed twice.

Then it holds each example to what today's guide said of the same bean. Today's examples are grown through today's gate
and translated into statements, as test/core_rehearse.py does; for every bean both gardens hold, each value today's
example wrote is found in the guide's bean (or the bean it names is linked to it by a statement), and each verb the
translation gave it is one the guide's bean uses — but for the differences listed below, each with its reason. A
difference listed and no longer met is reported too, so the list stays true.
"""
import os, re, shlex, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from core import check as core_check, engine, read  # noqa: E402
import core_rehearse  # noqa: E402 — today's examples grown through today's gate

FAILS = []
PY = sys.executable
GUIDE = os.path.join(ROOT, 'core', 'guide')
BLOCK = re.compile(r'<!-- (example|unsaid|example-front-matter|example-statements|example-check): ([^ ,>]+)[^>]*-->\n```[a-z]*\n(.*?)\n```',
                   re.S)
KNOWING = ('say', 'read', 'derive', 'make')

# WHAT TODAY'S EXAMPLES WROTE THAT IS NO FACT OF THE WORLD: the form today's law asked for, which the core derives or
# drops. A value is the form's where its key is one of these, or it is one of these words.
FORM_KEYS = {'provenance', 'genos', 'nature', 'status', 'class', 'establishing', 'key', 'unit', 'system', 'kind', 'as_of',
             'openness'}
SQUARE = {'required': 'obligatory', 'permitted': 'permitted', 'forbidden': 'forbidden', 'omissible': 'omissible'}
STAMPED = re.compile(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}[+-]\d{2}:\d{2}$')    # a moment the save wrote in place of `now`
ACTS = {'asserted-by-human': 'say', 'stated-in-document': 'say', 'observed': 'read', 'inferred': 'derive',
        'generated-by-tool': 'derive'}           # a provenance's `src` is the act that knows it (core/law/core.yaml)
FORM_WORDS = {'true', 'false', 'now', '', 'self', 'legal', 'technical', 'experience', 'financial', 'holder', 'owner',
              'bean', 'crown', 'parties', 'outside'}
# WHERE THE GUIDE SAYS IT OTHERWISE, ON PURPOSE: (bean, value or verb) -> why.
DIFFERS = {
    ('*', 'can'): "the translator writes a clause as `can`; the guide writes it as the core does, `obligatory` (or another "
                  "position of the permission square) of the statement it asks, through the agreement",
    ('dinner-at-sams', 'host'): "today's `refs` named the host by `rel: host`; the core says it with `answer` as law and "
                                "`attend`",
    ('dinner-at-sams', 'present'): "today's `rel: present` is the core's `attend`",
    ('call-with-ali', 'host'): "as for the dinner",
    ('call-with-ali', 'present'): "as for the dinner",
    ('call-with-ali', 'which day the call was'): "today's open question is the note on the `be` it is about, and the "
                                                 "body's prose",
    ('*', 'time'): "an extent's `of: time` names the frame; the core writes the extent itself, `<start>/<end>`",
    ('card-statement-2026-09', 'sha256:9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08'):
        "the namespace `sha-256` gives the name, so the name is the bare digest",
    ('card-statement-2026-09', '1790928000000'): "a capture's moment is its `read` act's, which the save writes",
    ('nginx', 'the nginx project'): "the owner outside is a being, the bean nginx-project",
    ('rack-a', 'location'): "what a capacity is for is the `as` of the `be` that takes room in it",
    ('bee-coop', 'observations'): "a grant's part is the verb that took today's term: the hives' readings, `measure`",
    ('bee-coop', 'located_at'): "a grant's part narrowed by its `as`: where a hive stands, `be.location`",
    ('submission-pack', 'agency-noor:translation-asked'): "a reading of another bean is `<bean>#<id>`",
    ('submission-pack', 'agency-noor:rights-papers'): "as for `translation-asked`: `agency-noor#rights-papers`",
    ('hive-orchard-1', 'hive-orchard-1:observations.mites-june'): "the core takes a statement by its id, `mites-june`",
    ('hive-orchard-1', 'hive-orchard-1:observations.second-count'): "the core takes a statement by its id, `second-count`",
    ('salt-road-heron', 'written'): "the words are the document salt-road-signed, the agreement's `through`",
    ('phone-loan', 'spoken'): "the words were spoken on the call: the agreement is `through` call-with-ali",
    ('laptop', 'Lenovo'): "the maker is a bean, `lenovo`, the namespace of its serials and where the hands were",
    ('lale-employment', 'leave.*'): "a reading reads a verb's statements, `entries: leave`, not the entries of a term",
    ('agency-noor', 'courses.home'): "a course is a `be` as order: the reading asks for `be.id` home and a `move` that "
                                     "reached `walk-placing#contracted`",
    ('agency-noor', 'courses.abroad'): "as for `courses.home`, `be.id` abroad",
    ('agency-noor', 'transactions.*'): "the payments are the bean's `pay` statements, `entries: pay`",
    ('agency-noor', 'day'): "a payment's day is the `at` of its `pay`",
    ('bee-coop', 'consent.bean'): "a member is who `agree`s to the co-op as a member: the co-op's `agree` statements",
    ('candle-supply', 'candle-beeswax:series.burn'): "a series is named as the statement that records it, "
                                                    "`candle-beeswax#burn`",
    ('candle-supply', 'candle-paraffin:series.burn'): "as for the beeswax candle's, `candle-paraffin#burn`",
}


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:1500]))
    if not cond:
        FAILS.append(name)


def run(*a, cwd=None):
    return subprocess.run(list(a), capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=cwd)


def guide(name):
    with open(os.path.join(GUIDE, name), encoding='utf-8') as fh:
        return fh.read()


def sections(name):
    """The page's sections (by `## `), each [(marker, path, text)] in the order of the page."""
    return [BLOCK.findall(sec) for sec in guide(name).split('\n## ')]


def head(path):
    """The front matter of a document as read (every value a string), or {}."""
    return read.document(path)[0] if os.path.isfile(path) else {}


def leaves(x, key=None):
    """(key, value) for every leaf of a front matter, its key the nearest one above it."""
    if isinstance(x, dict):
        for k, v in x.items():
            yield from leaves(v, k)
    elif isinstance(x, list):
        for v in x:
            yield from leaves(v, key)
    else:
        yield key, str(x)


def verbs(path):
    return [next(iter(s)) for s in head(path).get('statements') or [] if isinstance(s, dict) and s]


# THE DOORS AND THE NAMES, before any garden: one text wherever an agent's tool looks for it, the door for an assistant
# with no shell saying so first, and no tool or file named that the release does not hold
skill = re.sub(r"^---\n.*?\n---\n\s*", "", guide('SKILL.md'), count=1, flags=re.S)
check("core/guide/AGENTS.md and SKILL.md are one text: the skill is its front matter and then AGENTS.md, byte for byte",
      skill == guide('AGENTS.md') and len(skill) > 500, f"{len(skill)} vs {len(guide('AGENTS.md'))} bytes")
top = "\n".join(guide('WELCOME.md').splitlines()[:12])
check("core/guide/WELCOME.md says in its first lines that its reader cannot run the gate, and that what it reads is data",
      "cannot run the gate" in top and "cannot write to the ledger" in top and "data" in top, top[:300])
named = sorted({n for f in os.listdir(GUIDE) for n in re.findall(
    r"(?<![A-Za-z0-9_/.-])((?:bin|core|test|assets/[a-z]+/bin|assets/[a-z]+/templates)/[A-Za-z0-9_./-]+\.(?:py|sh|yaml))",
    guide(f))})
gone = [n for n in named if not os.path.isfile(os.path.join(ROOT, n))]
check(f"every tool and law file core/guide/ names exists ({len(named)} named)", not gone, gone)

T = tempfile.mkdtemp(prefix='dmcoreguides-')
G, TODAY, COPY = os.path.join(T, 'guides'), os.path.join(T, 'today'), os.path.join(T, 'copy')
written = {}                                 # path -> the text last written there, as the page shows it
added = set()                                # (path, text) of the statements a page added to a bean
waited = []                                  # the saves that waited for the minute to turn (bin/dmsave.py)


try:
    # A GARDEN, GROWN AND ADOPTING THE CORE WHILE IT IS EMPTY
    r = run('sh', os.path.join(ROOT, 'seed', 'germinate.sh'), G, cwd=ROOT)
    check("a garden germinates", r.returncode == 0, r.stdout + r.stderr)
    run('git', 'config', 'user.name', 'sam', cwd=G)
    run('git', 'config', 'user.email', 'sam@example.invalid', cwd=G)
    gp = os.path.join(G, 'GARDEN.md')
    gt = open(gp, encoding='utf-8').read()
    open(gp, 'w', encoding='utf-8', newline='\n').write(re.sub(r'(?m)^extends: std-vocab@[^ \n]*', 'extends: core@' + str(read.data(os.path.join(ROOT, 'core', 'law', 'core.yaml'))['version']), gt, count=1))
    r = run(PY, 'core/install.py', cwd=G)
    check("the garden takes the core's gate (core/install.py)", r.returncode == 0, r.stdout + r.stderr)
    r = run(PY, 'bin/dmsave.py', 'sam', 'RULE-CHANGE: the core adopted', '--body',
            '- action: RULE-CHANGE, GARDEN.md extends the core while the garden is empty; ratified by sam', cwd=G)
    check("the empty garden adopts the core: GARDEN.md's pin moves, in one RULE-CHANGE through the core's gate",
          r.returncode == 0, r.stdout + r.stderr)

    def apply(marker, path, text):
        """One block of a page, written into the garden as the page means it."""
        p = os.path.join(G, path)
        if marker in ('example', 'unsaid'):
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, 'w', encoding='utf-8', newline='\n') as fh:
                fh.write(text + '\n')
            written[path] = text
        elif marker == 'example-statements':          # statements added to a bean, at the end of its list
            added.add((path, text))
            t = open(p, encoding='utf-8').read()
            front, sep, body = t[4:].partition('\n---\n')
            with open(p, 'w', encoding='utf-8', newline='\n') as fh:
                fh.write('---\n' + front.replace('\ndetails:', '\n' + text + '\ndetails:', 1)
                         if '\ndetails:' in front else '---\n' + front + '\n' + text)
                fh.write(sep + body)
        elif path == 'VOCAB.md':
            core_rehearse.fragment(G, text)
        elif path == 'GARDEN.md':
            g = open(p, encoding='utf-8').read()
            for line in text.strip().split('\n'):
                g = re.sub(rf'(?m)^{re.escape(line.split(":", 1)[0])}:[^\n]*$', line.strip(), g, count=1)
            open(p, 'w', encoding='utf-8', newline='\n').write(g)

    def judged(path, text):
        """The gate's findings on the bean at `path` with the statements `text` added to it, nothing committed."""
        garden = engine.Garden.read(G)
        bid = os.path.basename(path)[:-3]
        if bid not in garden.beans:
            return [('form', bid, 'no such bean in the garden')]
        b = garden.beans[bid]
        h = dict(b.header)
        h['statements'] = list(b.statements) + list(read.loads(text) or [])
        garden.beans[bid] = engine.Bean(bid, b.path, h)
        return [f for f in engine.judge(core_check.garden_law(G), garden) if f[1].split('[')[0] == bid]

    def save(what, blocks):
        """The blocks of one section, saved in one commit through bin/dmsave.py and the core's gate."""
        new = [(m, p, t) for m, p, t in blocks if (m in ('example', 'unsaid') and written.get(p) != t)
               or (m == 'example-statements' and (p, t) not in added) or m == 'example-front-matter']
        new = [b for b in new if b[1] != 'log/journal.md']
        if not new:
            return None
        before = {p: verbs(os.path.join(G, p)) for _m, p, _t in new if p.startswith(('beans/', 'mappings/'))}
        sealed_before = {p: [r.get('id') for s in head(os.path.join(G, p)).get('statements') or [] if isinstance(s, dict)
                             for r in s.values() if isinstance(r, dict) and 'held' in r] for p in before}
        try:
            for b in new:
                apply(*b)
        except OSError as e:                          # a block a page writes into a bean that is not there
            return (False, str(e))
        out = []                                      # what a change takes out, said as its writer says it (rule kept)
        for p, was in before.items():
            now = verbs(os.path.join(G, p))
            out += [f"`{v}` taken out of [[{os.path.basename(p)[:-3]}]]" for v in sorted(set(was))
                    if was.count(v) > now.count(v)]
        held = []                                     # and what it seals, as bin/dmheld.py prints it (rule harm)
        for p in before:
            sealed = [r.get('id') for s in head(os.path.join(G, p)).get('statements') or [] if isinstance(s, dict)
                      for r in s.values() if isinstance(r, dict) and 'held' in r]
            held += [f"- held: {os.path.basename(p)[:-3]} {i} added" for i in sealed if i not in sealed_before.get(p, ())]
        named = sorted({os.path.basename(p)[:-3] for _m, p, _t in new if p.startswith(('beans/', 'mappings/'))})
        law = any(p in ('VOCAB.md', 'GARDEN.md') for _m, p, _t in new)
        body = '- action: ' + ('RULE-CHANGE: ' if law else '') + (', '.join(f"[[{b}]]" for b in named) or 'the law') \
            + ''.join(f"; {x}" for x in out) + ''.join(f"\n{x}" for x in held)
        before = run('git', 'rev-parse', 'HEAD', cwd=G).stdout
        r = run(PY, 'bin/dmsave.py', 'sam', what[:60], '--body', body, cwd=G)
        moved = run('git', 'rev-parse', 'HEAD', cwd=G).stdout != before
        if 'was saved in this minute already' in r.stderr:
            waited.append(what)
        return (r.returncode == 0 and moved, (r.stdout + r.stderr)[-1500:])

    # README.MD: THE FIRST BEANS, SAVED BY THE COMMAND THE PAGE SHOWS
    rm = [b for s in sections('README.md') for b in s]
    for b in rm:
        if b[1] != 'log/journal.md':
            apply(*b)
    cmd = next(t for m, p, t in rm if p == 'log/journal.md')
    r = run('sh', '-c', cmd.replace('python3 ', shlex.quote(PY) + ' ', 1), cwd=G)
    check("README.md's first beans, its namespace and the gardener's line commit through the core's gate, saved by the "
          "command the page shows", r.returncode == 0 and 'sam' in head(os.path.join(G, 'GARDEN.md')).get('gardener', ''),
          (r.stdout + r.stderr)[-1500:])

    # EACH RECIPE, IN THE ORDER OF THE PAGES, ONE COMMIT EACH
    for page in ('COOKBOOK.md', 'WELCOME.md', 'FORMS.md'):
        if not os.path.isfile(os.path.join(GUIDE, page)):
            check(f"core/guide/{page} is written", False, 'missing')
            continue
        done, failed, judged_n = 0, [], 0
        for i, blocks in enumerate(sections(page)):
            title = guide(page).split('\n## ')[i].split('\n', 1)[0].lstrip('# ')
            got = save(f"{page}: {title}", [b for b in blocks if b[0] != 'example-check'])
            for _m, p, t in [b for b in blocks if b[0] == 'example-check']:
                found = judged(p, t)
                judged_n += 1
                if found:
                    failed.append((f"{title}: the check on {p}", found))
            if got is None:
                continue
            if got[0]:
                done += 1
            else:
                failed.append((title, got[1]))
                run('git', 'reset', '-q', '--hard', cwd=G)
                run('git', 'clean', '-qfd', cwd=G)
        check(f"core/guide/{page}: each section's examples commit through the core's gate ({done}), and the "
              f"statements it shows for a bean pass beside it ({judged_n})", not failed and done >= 1, failed)

    check(f"the save waits for the minute to turn where it would save one bean twice in it, and the commit is made "
          f"({len(waited)}: {'; '.join(waited)[:200]})", len(waited) >= 1, waited)
    r = run(PY, 'core/check.py', cwd=G)
    beans = [f for d in ('beans', 'mappings') if os.path.isdir(os.path.join(G, d)) for f in os.listdir(os.path.join(G, d))]
    check(f"the garden of the guides' {len(beans)} beans passes the core's gate whole", r.returncode == 0
          and '— 0 error(s)' in r.stdout, r.stdout[-2000:])

    # WHAT TODAY'S GUIDES SAID OF THE SAME BEANS
    core_rehearse.grow_today(TODAY, check=lambda n, c, d='': None if c else check(f"today's examples: {n}", c, d))
    r = run(PY, os.path.join(ROOT, 'core', 'translate.py'), 'garden', TODAY, COPY)
    check("today's examples are grown and translated, as test/core_rehearse.py does", r.returncode == 0, r.stdout[-800:])
    lost, unused, stale_seen = {}, {}, set()
    for d in ('beans', 'mappings'):
        for f in sorted(os.listdir(os.path.join(G, d))) if os.path.isdir(os.path.join(G, d)) else []:
            bid, new = f[:-3], os.path.join(G, d, f)
            old, copy = os.path.join(TODAY, d, f), os.path.join(COPY, d, f)
            if not os.path.isfile(old):
                continue
            text = open(new, encoding='utf-8').read()
            values = {v for _k, v in leaves(head(new))}
            gone = []
            for k, v in leaves(head(old)):
                if k == 'src' or k == 'permission':
                    want = (ACTS if k == 'src' else SQUARE).get(v)
                    if want not in verbs(new):
                        gone.append(f"{k}: {v}, which is no `{want}` here")
                    continue
                if v in values or (k == 'at' and STAMPED.match(v)):
                    continue
                if k in FORM_KEYS or v in FORM_WORDS or v in text or (k == 'value' and v.endswith(f":{bid}")):
                    continue
                other = next((os.path.join(G, dd, v + '.md') for dd in ('beans', 'mappings')
                              if os.path.isfile(os.path.join(G, dd, v + '.md'))), None)
                if other and bid in open(other, encoding='utf-8').read():
                    continue                                  # the bean it names is linked to it from there
                key = (bid, v) if (bid, v) in DIFFERS else ('*', v) if ('*', v) in DIFFERS else None
                if key:
                    stale_seen.add(key)
                    continue
                gone.append(f"{k}: {v}")
            if gone:
                lost[bid] = gone
            mine = set(verbs(new))
            for v in set(verbs(copy)) - set(KNOWING) - mine:
                key = (bid, v) if (bid, v) in DIFFERS else ('*', v) if ('*', v) in DIFFERS else None
                if key:
                    stale_seen.add(key)
                else:
                    unused.setdefault(bid, []).append(v)
    check("each value today's examples wrote is in the guide's bean, or the bean it names is linked to it — but for the "
          "differences listed, each with its reason", not lost, lost)
    check("each verb the translation of today's examples gave a bean is one the guide's bean uses — but for the "
          "differences listed", not unused, unused)
    check("every difference listed is still met: the list says only what is so", set(DIFFERS) <= stale_seen,
          sorted(set(DIFFERS) - stale_seen))
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\ncore_guides: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
