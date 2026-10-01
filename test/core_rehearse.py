#!/usr/bin/env python3
"""The core's rehearsal on the release's own examples: the beans the guides show, grown into a garden today's gate
accepts, then translated into statements — nothing lost, and the core's engine passing.

Grows a garden (seed/germinate.sh) and commits seed/README.md's first beans and the gardener's line, then each recipe of
seed/COOKBOOK.md and seed/WELCOME.md in the order of the pages with its VOCAB.md fragment, journalled through
bin/dmjournal.py and judged by today's gate, as test/germinate.py does; then seed/FORMS.md's forms and its forms for
what nobody said. So every bean here is one today's law accepts. It translates the garden into a copy
(core/translate.py) and checks that every value of every bean is placed and found where it was put, that the core's
engine passes the copy, and that the forms the guides teach — a person, a host, money between two people, an agreement
paid in instalments, an event, another person's garden — each became statements.
"""
import os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from core import read  # noqa: E402

FAILS = []
PY = sys.executable
EX = re.compile(r'<!-- example: ((?:beans|mappings|extracts)/[a-z0-9-]+\.(?:md|tsv)) -->\n```(?:markdown|tsv)\n(.*?)\n```', re.S)
FRAG = re.compile(r'<!-- example-front-matter: VOCAB\.md -->\n```yaml\n(.*?)\n```', re.S)
STAMPED = re.compile(r'(\b(?:as_of|observed):[ \t]*)\d{4}-\d{2}-\d{2}\b')


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:1500]))
    if not cond:
        FAILS.append(name)


def run(*a, cwd=None):
    return subprocess.run(list(a), capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=cwd)


def page(name):
    with open(os.path.join(ROOT, 'seed', name), encoding='utf-8') as fh:
        return fh.read()


T = tempfile.mkdtemp(prefix='dmcorereh-')
G, C = os.path.join(T, 'examples'), os.path.join(T, 'copy')


def commit(name, body):
    run(PY, os.path.join(G, 'bin', 'dmjournal.py'), 'human (test)', name[:60], '--body', body, cwd=G)
    run('git', 'add', '-A', cwd=G)
    return run('git', '-c', 'user.name=t', '-c', 'user.email=t@x', 'commit', '-qm', name, cwd=G)


def write(path, text):
    p = os.path.join(G, path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text + '\n')


def fragment(frag):
    """A VOCAB.md fragment merged as test/germinate.py merges one: an empty key replaced, an opened key extended."""
    vp = os.path.join(G, 'VOCAB.md')
    v = open(vp, encoding='utf-8').read()
    for blk in [b for b in re.split(r'(?m)^(?=[a-z_]+:)', frag) if b.strip()]:
        key = blk.split(':', 1)[0]
        v = re.sub(rf'^{key}: \[\].*\n', '', v, count=1, flags=re.M)
        m = re.search(rf'(?m)^{key}:[ \t]*\n', v)
        if m:
            v = v[:m.end()] + blk.split('\n', 1)[1].rstrip('\n') + '\n' + v[m.end():]
        else:
            head, sep, rest = v.partition('\n---\n')
            v = head + '\n' + blk.rstrip('\n') + sep + rest
    with open(vp, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(v)


try:
    r = run('sh', os.path.join(ROOT, 'seed', 'germinate.sh'), G, cwd=ROOT)
    check("a garden germinates", r.returncode == 0, r.stdout + r.stderr)
    # THE FIRST BEANS AND THE GARDENER'S LINE, as seed/README.md teaches them
    rm = page('README.md')
    first = [(p, t) for p, t in EX.findall(rm) if p in ('beans/sam.md', 'beans/laptop.md')]
    for p, t in first:
        write(p, t)
    gline = re.findall(r'<!-- example-front-matter: GARDEN\.md -->\n```yaml\n(.*?)\n```', rm, re.S)
    gp = os.path.join(G, 'GARDEN.md')
    gt = open(gp, encoding='utf-8').read()
    for line in gline:
        gt = re.sub(r'(?m)^gardener:[^\n]*$', line.strip(), gt, count=1)
    open(gp, 'w', encoding='utf-8', newline='\n').write(gt)
    c = commit('first beans', '- action: RULE-CHANGE (GARDEN.md: its gardener); '
               + ', '.join(f"[[{os.path.basename(p)[:-3]}]]" for p, _t in first))
    check("seed/README.md's first beans and the gardener's line commit through today's gate", c.returncode == 0,
          (c.stdout + c.stderr)[-600:])
    # EACH RECIPE, in the order of the page, as test/germinate.py commits them
    done, failed = 0, None
    for doc in ('COOKBOOK.md', 'WELCOME.md'):
        for sec in page(doc).split('\n## '):
            beans, frags = EX.findall(sec), FRAG.findall(sec)
            changed = [p for p, x in beans if not os.path.isfile(os.path.join(G, p))
                       or STAMPED.sub(r'\1now', open(os.path.join(G, p), encoding='utf-8').read()) != x + '\n']
            if not changed and not frags:
                continue
            for p, t in beans:
                write(p, t)
            for f in frags:
                fragment(f)
            nas = os.path.join(G, 'beans', 'nas.md')
            if any('os: nas-os' in f for f in frags) and os.path.isfile(nas):    # the recipe's next step: the NAS uses it
                n = open(nas, encoding='utf-8').read()
                open(nas, 'w', encoding='utf-8').write(n.replace('provides_habitat: linux-baremetal\n',
                                                                 'provides_habitat: linux-baremetal\nos: nas-os\n', 1))
                changed.append('beans/nas.md')
            names = ', '.join(p if p.startswith('extracts/') else f"[[{os.path.basename(p)[:-3]}]]" for p in changed)
            name = f"{doc}: {sec.split(chr(10), 1)[0].lstrip('# ')}"
            c = commit(name, f"- action: {'RULE-CHANGE (VOCAB.md); ' if frags else ''}{names or 'VOCAB.md only'}")
            if c.returncode != 0:
                failed = (name, (c.stdout + c.stderr)[-600:])
                run('git', 'reset', '-q', '--hard', cwd=G)
                break
            done += 1
    check(f"seed/COOKBOOK.md's and seed/WELCOME.md's recipes commit through today's gate, one at a time ({done})",
          failed is None and done >= 10, failed)
    # SEED/FORMS.MD: its forms, and its forms for what nobody said
    fp = page('FORMS.md')
    forms = [(p, t) for p, t in EX.findall(fp)
             if not os.path.isfile(os.path.join(G, p))
             or STAMPED.sub(r'\1now', open(os.path.join(G, p), encoding='utf-8').read()) != t + '\n']
    unsaid = re.findall(r'<!-- unsaid: (beans/[a-z0-9-]+\.md), for [a-z0-9_, ]+ -->\n```markdown\n(.*?)\n```', fp, re.S)
    for p, t in forms + unsaid:
        write(p, t)
    ap = os.path.join(G, 'beans', 'ali.md')
    if os.path.isfile(ap):              # the name another garden minted, carried here unqualified (test/germinate.py)
        a = open(ap, encoding='utf-8').read()
        open(ap, 'w', encoding='utf-8', newline='\n').write(re.sub(r'value: "[0-9a-f]{12}/person:ali"', 'value: "person:ali"', a))
    c = commit('the forms', '- action: ' + ', '.join(f"[[{os.path.basename(p)[:-3]}]]" for p, _t in forms + unsaid)
               + ', and [[ali]] named here.')
    check(f"seed/FORMS.md's forms ({len(forms)} not shown before) and its {len(unsaid)} forms for what nobody said commit "
          f"through today's gate", c.returncode == 0 and len(unsaid) >= 3, (c.stdout + c.stderr)[-600:])

    # THE TRANSLATION
    n_beans = len([f for d in ('beans', 'mappings') if os.path.isdir(os.path.join(G, d))
                   for f in os.listdir(os.path.join(G, d)) if f.endswith('.md')])
    r = run(PY, os.path.join(ROOT, 'core', 'translate.py'), 'garden', G, C)
    last = r.stdout.strip().split('\n')[-1] if r.stdout.strip() else ''
    m = re.search(r'(\d+) values, (\d+) placed', last)
    check(f"the garden of the guides' {n_beans} beans is translated into statements with nothing lost: {last[11:150]}…",
          r.returncode == 0 and '— 0 problem(s)' in last and m and m.group(1) == m.group(2) and f"{n_beans} beans" in last,
          r.stdout[-1500:] + r.stderr)
    r = run(PY, os.path.join(ROOT, 'core', 'check.py'), C)
    check("the core's engine passes the translated garden", r.returncode == 0 and '— 0 error(s)' in r.stdout, r.stdout[-2000:])

    def verbs(bid):
        p = os.path.join(C, 'beans', bid + '.md')
        if not os.path.isfile(p):
            return []
        return [next(iter(s)) for s in read.document(p)[0].get('statements') or []]
    kinds = {}
    for f in os.listdir(os.path.join(C, 'beans')):
        kinds.setdefault(read.document(os.path.join(C, 'beans', f))[0].get('kind'), []).append(f[:-3])
    contracts = [verbs(b) for b in kinds.get('contract', [])]
    check("the guides' forms became statements: a person is owned by the crown, a host has a name and an owner, an "
          "agreement its parties' `agree`, money its `pay` and `bear`, an event its `be` at a time",
          'own' in verbs('sam') and {'name', 'own'} <= set(verbs('laptop'))
          and any('agree' in v for v in contracts) and any({'pay', 'bear'} <= set(v) for v in contracts)
          and all('be' in verbs(b) or 'agree' in verbs(b) for b in kinds.get('event', [])[:1]),
          {k: {b: verbs(b) for b in v[:3]} for k, v in kinds.items()})
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\ncore_rehearse: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
