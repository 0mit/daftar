#!/usr/bin/env python3
"""The profiles and the view asset in a garden of the core (v1 part 11): a profile taken from the core, and a page of
drawings in statements, judged by the core's gate, drawn by its asset and written back by its author mode — the same page
today's words draw.

Builds what it needs, as test/core_write.py does: a release of the core made from this tree (v1.0.0, its
seed/GARDEN.md.template pinning `core@`), and a release in today's words (this tree as it ships). Then:

  the law        core/law/profiles.yaml is what std-vocab generates: each profile with the verbs whose home it is, each of
                 today's terms and overlays of it named where it went, its vacancies at their places; the law holds
  germinate      a garden of the core grows taking the view profile (VOCAB.md `profiles`), its asset with it; a profile
                 the law does not offer is refused, and nothing is made
  the gate       the cookbook's page in statements is saved through the core's gate; rule `profile` refuses a verb of a
                 profile the garden does not take, an attribute a profile adds, a drawing its page does not name, a
                 drawing its page names that is not there, and a value a drawing names that it does not hold
  the asset      view.py check agrees, elements and report draw, dmview.py is the same tool; import writes only the
                 `draw` a selection changes, through bin/safe.py, journalled and read back, and its commit passes the gate;
                 a second import has nothing to write; render --keep keeps a document bean of statements
  upgrade        --extend takes a profile up (VOCAB.md `profiles`, its entry a RULE-CHANGE); --retract of the profile the
                 page draws by is refused by the gate, every file put back
  translation    today's cookbook page, grown through today's gate and translated, is drawn the same: check says the same,
                 and the report's drawings — their stages, values, elements and cards — its order, reference, lenses
                 and units are today's, but for the law's own words (a card's fact is the verb that says it now)

Run: python3 test/core_view.py   (0 = green; about two minutes)
"""
import json, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'bin'))
from core import read  # noqa: E402
from core.law import Law  # noqa: E402
import dmparse, dmpass  # noqa: E402

FAILS = []
PY = sys.executable


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:1500]))
    if not cond:
        FAILS.append(name)


class R:
    def __init__(self, p):
        self.returncode, self.out = p.returncode, p.stdout + p.stderr


def run(*a, cwd=None):
    e = dict(os.environ, GIT_AUTHOR_NAME='sam', GIT_AUTHOR_EMAIL='sam@x', GIT_COMMITTER_NAME='sam',
             GIT_COMMITTER_EMAIL='sam@x')
    return R(subprocess.run(a, capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=cwd or G, env=e))


def text(path, root=None):
    with open(os.path.join(root or G, path), encoding='utf-8') as fh:
        return fh.read()


def write(path, t, root=None):
    p = os.path.join(root or G, path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(t)


def clean(root=None):
    return run('git', 'status', '--porcelain', cwd=root).out.strip() == ''


def head(root=None):
    return run('git', 'rev-parse', 'HEAD', cwd=root).out.strip()


def save(what, body, root=None):
    return run(PY, 'bin/save.py', 'sam', what, '--body', body, cwd=root)


def gate(root=None):
    """The core's findings on the working tree: [(rule, where, message)] as core/check.py prints them."""
    r = run(PY, 'core/check.py', '.', cwd=root)
    return [ln for ln in r.out.splitlines() if ln and not ln.startswith('core check')]


def view(*a, root=None):
    return run(PY, 'assets/view/bin/view.py', *a, cwd=root)


def payload(root):
    """The page the report draws, as its runtime receives it."""
    code = ("import json, os, sys; sys.path.insert(0, os.path.join(%r, 'assets', 'view', 'lib')); import view_model as vm, "
            "view_report; p = vm.init(%r); assert not p, p; print(json.dumps(view_report.payload(), sort_keys=True, "
            "default=str))" % (root, root))
    r = run(PY, '-c', code, cwd=root)
    try:
        return json.loads(r.out.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return {'error': r.out[-1500:]}


def blocks(page, marker='example'):
    return dict(re.findall(rf'<!-- {marker}: ((?:beans|mappings)/[a-z0-9-]+\.md) -->\n```markdown\n(.*?)\n```', page, re.S))


T = tempfile.mkdtemp(prefix='core-view-')
REL, OLD, G = os.path.join(T, 'release'), os.path.join(T, 'release-today'), os.path.join(T, 'garden')
LAW = dmparse.loads(dmparse.split_front_matter(text('seed/std-vocab.md', ROOT))[0])

try:
    # ---- THE LAW: generated, every profile accounted
    gen = run(PY, 'core/translate.py', 'profiles', cwd=ROOT)
    check("law: core/law/profiles.yaml is what std-vocab generates", gen.returncode == 0
          and gen.out == text('core/law/profiles.yaml', ROOT), gen.out[:300])
    gen = run(PY, 'core/translate.py', 'terms', cwd=ROOT)
    tw = read.data(os.path.join(ROOT, 'core', 'law', 'terms.yaml')).get('terms') or []
    check(f"law: core/law/terms.yaml is what std-vocab generates, and names where each of today's {len(LAW['terms'])} "
          f"terms went", gen.returncode == 0 and gen.out == text('core/law/terms.yaml', ROOT)
          and [t['term'] for t in tw] == [t['term'] for t in LAW['terms']] and all(t.get('went') for t in tw), gen.out[:300])
    L = Law.load()
    P = read.data(os.path.join(ROOT, 'core', 'law', 'profiles.yaml'))
    homed = {p: sorted(v for v in L.verbs if L.home(v) == p) for p in L.profiles}
    check(f"law: the {len(L.profiles)} profiles are today's, each with the verbs whose home it is "
          f"({', '.join(f'{p} {len(v)}' for p, v in homed.items())})",
          sorted(L.profiles) == sorted(LAW['profiles'])
          and all(sorted(r.get('verbs') or []) == homed[r['profile']] for r in P['profiles']), homed)
    went = {r['profile']: set(r['went']) for r in P['profiles']}
    today = {p: {t['term'] for t in r.get('terms') or []} | {o['term'] for o in r.get('overlays') or []}
             for p, r in LAW['profiles'].items()}
    check("law: each of today's terms and overlays of a profile is named where it went",
          all({w.split('.')[0] for w in went[p]} >= today[p] for p in today), (went, today))
    vac = sum(len(r.get('vacancies') or []) + len(r.get('dropped') or []) for r in P['profiles'])
    check(f"law: each of a profile's {vac} vacancies is placed in the core or dropped with why — none lost — and the "
          f"law holds together with them",
          vac == sum(len(r.get('vacancies') or []) for r in LAW['profiles'].values()) and not L.problems(),
          L.problems()[:3])
    check("law: the lenses, archetypes and planes are the profiles' tables; a drawing's form holds its values, each "
          "one of the three kinds of live value",
          L.tables['lenses'] == [r['lens'] for r in LAW['view_lenses']] and len(L.tables['archetypes']) == 10
          and L.tables['planes'] == ['data', 'control', 'management']
          and L.form_attr('drawing', 'values.live') and 'live-series' in L.form_attr('drawing', 'values.live')['in'])

    # ---- THE RELEASES: the core's, made from this tree, and today's
    lang = dmpass.language(text('seed/LANGUAGE', ROOT))
    files = [f for f in dmpass.tracked(ROOT) if os.path.isfile(os.path.join(ROOT, f))]
    for rel, core in ((REL, True), (OLD, False)):
        for f in dmpass.kept(files, lang, dmpass.offered(LAW)):
            os.makedirs(os.path.join(rel, os.path.dirname(f)), exist_ok=True)
            shutil.copy2(os.path.join(ROOT, f), os.path.join(rel, f))
        if core:
            for f in ('GARDEN.md.template', 'VOCAB.md.template'):
                shutil.copy2(os.path.join(ROOT, 'core', 'guide', f), os.path.join(rel, 'seed', f))
        for c in (['git', 'init', '-q'], ['git', 'add', '-A'], ['git', 'commit', '-qm', 'a release'],
                  ['git', 'tag', 'v1.0.0']):
            run(*c, cwd=rel)

    # ---- GERMINATE: a garden of the core taking the view profile
    r = run(PY, os.path.join(REL, 'seed', 'germinate.py'), os.path.join(T, 'nothing'), '--gardener', 'sam',
            '--profile', 'drawing', cwd=T)
    check("germinate: a profile the core does not offer is refused, naming those it does, and nothing is made",
          r.returncode != 0 and 'view' in r.out and not os.path.exists(os.path.join(T, 'nothing')), r.out[-600:])
    r = run(PY, os.path.join(REL, 'seed', 'germinate.py'), G, '--gardener', 'sam', '--gardener-name', 'Sam',
            '--profile', 'view', cwd=T)
    vocab = read.document(os.path.join(G, 'VOCAB.md'))[0] if os.path.isfile(os.path.join(G, 'VOCAB.md')) else {}
    check("germinate: a garden of the core grows taking the view profile — VOCAB.md `profiles: [view]` — and the "
          "asset arrives with it", r.returncode == 0 and vocab.get('profiles') == ['view'] and 'core@' in text('GARDEN.md')
          and os.path.isfile(os.path.join(G, 'assets', 'view', 'bin', 'view.py')), r.out[-800:])
    if r.returncode != 0:
        raise SystemExit(1)

    # ---- THE GATE: the cookbook's page in statements
    ex = blocks(text('core/guide/COOKBOOK.md', ROOT))
    for p in ('beans/oven-a.md', 'beans/bakery-page.md'):
        write(p, ex[p] + '\n')
    os.makedirs(os.path.join(G, 'drawings'), exist_ok=True)
    shutil.copy2(os.path.join(G, 'assets', 'view', 'templates', 'drawings.py'), os.path.join(G, 'drawings', 'bakery.py'))
    r = save('the bakery, drawn', '- action: wrote [[oven-a]] and [[bakery-page]], the page of its drawings')
    check("gate: the cookbook's page — a `draw` of each drawing, the page's own naming them — is saved through the core's "
          "gate", r.returncode == 0 and clean(), r.out[-1200:])
    PAGE = text('beans/bakery-page.md')

    def refused(name, path, new, *words):
        before = text(path) if os.path.isfile(os.path.join(G, path)) else None
        write(path, new)
        got = [ln for ln in gate() if ln.startswith('profile')]
        if before is None:
            os.remove(os.path.join(G, path))
        else:
            write(path, before)
        check(f"gate: rule profile refuses {name}", got and all(any(w in ln for ln in got) for w in words), got or gate())
    refused("a verb of a profile the garden does not take, naming the profile and the line that takes it",
            'beans/oven-b.md', ex['beans/oven-a.md'].replace('oven-a', 'oven-b').replace('SN-OVEN-0042', 'SN-OVEN-0043')
            .replace('  - own:', '  - serve: { by: self, at: ["192.0.2.7", "tcp-port:80"], through: http }\n  - own:')
            + '\n', '`serve`', 'network', '`profiles: [network, view]`')
    refused("an attribute a profile adds to a core form, where the garden does not take it",
            'beans/oven-b.md', ex['beans/oven-a.md'].replace('oven-a', 'oven-b').replace('SN-OVEN-0042', 'SN-OVEN-0043')
            .replace('  - own:', '  - be: { by: self, at: "uri:https://bakery.example.org/oven", as: location, placed: '
                     '{ role: own-source } }\n  - own:') + '\n', '`role`', 'code')
    refused("a drawing its page does not name", 'beans/bakery-page.md', PAGE.replace(
        '  - draw: { id: page,', '  - draw: { id: loaves, by: self, of: [oven-a], drawing: { purpose: "p", outcome: "o", '
        'stages: [ { label: "s", doer: "d" } ], questions: [ { lens: orient, ask: "a?" } ], archetype: health-chain, '
        'blind: [ { what: "w" } ] } }\n  - draw: { id: page,'), 'loaves', 'does not name')
    refused("a drawing its page names that is not there", 'beans/bakery-page.md',
            PAGE.replace('of: [orders], page:', 'of: [orders, loaves], page:'), "'loaves' is no drawing")
    refused("a value its drawing names and its page does not hold", 'beans/bakery-page.md',
            PAGE.replace('archetype: health-chain,', 'archetype: health-chain, parts: [ { bind: oven-heat } ],'),
            "'oven-heat' is no value of this page")

    # ---- THE ASSET on statements
    r = view('check')
    check("asset: view.py check — the page and its drawings agree", r.returncode == 0 and 'agree' in r.out, r.out[-800:])
    r2 = run(PY, 'assets/view/bin/dmview.py', 'check')
    check("asset: dmview.py, today's name, is the same tool", r2.returncode == 0 and r2.out == r.out, r2.out[-400:])
    r = view('elements', 'orders')
    check("asset: a drawing's elements, the oven among them depicting its bean", r.returncode == 0
          and re.search(r'oven\s+node\s+oven-a', r.out), r.out[-600:])
    r = view('report', '--out', os.path.join(T, 'bakery.html'))
    p = payload(G)
    check("asset: report draws the page from its statements — its drawing, its order, its reference",
          r.returncode == 0 and os.path.isfile(os.path.join(T, 'bakery.html')) and p.get('order') == ['orders']
          and "Every order in stock is baked the same morning." in json.dumps(p['views']['orders'].get('story'))
          and [x['being'] for x in p.get('reference') or []] == ['oven-a'], (r.out[-400:], str(p)[:600]))
    was = head()
    write(os.path.join(T, 'sel.json'), json.dumps({'views': {'orders': {'outcome': "The orders leave the oven by eight."}}}),
          '/')
    r = view('import', os.path.join(T, 'sel.json'))
    diff = run('git', 'diff', was, 'HEAD', '--', 'beans').out
    changed = [ln for ln in diff.splitlines() if ln.startswith(('+  - ', '-  - '))]
    check("asset: import writes only the `draw` the selection changes, through bin/safe.py, known by a `say` of the "
          "gardener's that names it, and saves it through the core's gate",
          r.returncode == 0 and head() != was and clean() and len(changed) == 3
          and all(re.match(r'[-+]  - draw: \{ ?id: orders, by: self', ln) for ln in changed[:2])
          and 'by eight' in changed[1] and re.search(r'say: \{ ?by: sam, of: \[orders\], at: .?20', changed[2])
          and 'draw#orders' in text('log/journal.md').split('\n## ')[-1], (r.out[-600:], diff[-1200:]))
    r = view('import', os.path.join(T, 'sel.json'))
    check("asset: the same selection again has nothing to write", r.returncode == 0 and 'nothing to write' in r.out
          and clean(), r.out[-400:])
    r = view('check', '--garden', G)
    check("asset: the page read back from its statements still agrees", r.returncode == 0, r.out[-400:])

    # ---- UPGRADE: a profile taken up and put down
    was = head()
    r = run(PY, 'bin/dmupgrade.py', 'v1.0.0', '--from', REL, '--extend', 'network')
    entry = text('log/journal.md').split('\n## ')[-1]
    check("upgrade: --extend takes a profile up — VOCAB.md `profiles: [view, network]`, its entry a RULE-CHANGE",
          r.returncode == 0 and read.document(os.path.join(G, 'VOCAB.md'))[0].get('profiles') == ['view', 'network']
          and 'RULE-CHANGE' in entry and 'network' in entry, r.out[-1200:])
    run('git', 'checkout', '-q', '--', '.')
    run('git', 'clean', '-qfd')
    r = run(PY, 'bin/dmupgrade.py', 'v1.0.0', '--from', REL, '--retract', 'view')
    check("upgrade: --retract of the profile its page draws by is refused by the core's gate, every file put back",
          r.returncode != 0 and 'NOT UPGRADED' in r.out and 'profile' in r.out and clean() and head() == was
          and os.path.isfile(os.path.join(G, 'assets', 'view', 'bin', 'view.py')), r.out[-1200:])

    # ---- TRANSLATION: today's cookbook page, drawn the same from statements
    O, C = os.path.join(T, 'today'), os.path.join(T, 'today-core')
    r = run(PY, os.path.join(OLD, 'seed', 'germinate.py'), O, '--gardener', 'sam', '--profile', 'view', cwd=T)
    for p, x in blocks(text('seed/COOKBOOK.md', ROOT), 'view-example').items():
        write(p, x + '\n', O)
    os.makedirs(os.path.join(O, 'drawings'), exist_ok=True)
    shutil.copy2(os.path.join(O, 'assets', 'view', 'templates', 'drawings.py'), os.path.join(O, 'drawings', 'bakery.py'))
    s = run(PY, 'bin/dmsave.py', 'sam', 'the bakery, drawn', '--body', '- action: wrote [[oven-a]] and [[bakery-page]]',
            cwd=O)
    t = run(PY, 'core/translate.py', 'garden', O, C, cwd=ROOT)
    check("translation: today's cookbook page, saved through today's gate, translates with every value placed",
          r.returncode == 0 and s.returncode == 0 and t.returncode == 0 and '0 problem(s)' in t.out, (s.out[-400:], t.out[-800:]))
    for c in (['git', 'init', '-q'], ['git', 'add', '-A'], ['git', 'commit', '-qm', 'translated', '--no-verify']):
        run(*c, cwd=C)
    tp = read.document(os.path.join(C, 'beans', 'bakery-page.md'))[0]
    draws = [s['draw'] for s in tp.get('statements') or [] if 'draw' in s]
    check("translation: `views` is a `draw` of each drawing and `view` the page's own, naming them in order; nothing of "
          "the page is left in `details`",
          [d.get('id') for d in draws] == ['orders', 'page'] and draws[1].get('of') == ['orders']
          and not {'view', 'views', 'view_bindings', 'view_monitors'} & set(tp.get('details') or {}), draws)
    a, b = view('check', root=O), view('check', root=C)
    check("translation: check says of the translated page what it says of today's", a.returncode == 0
          and a.out == b.out, (a.out[-400:], b.out[-400:]))
    pa, pb = payload(O), payload(C)

    def unworded(x):
        """A payload less what the law words in its own way — a card's fact label, the act a card names — and what the
        garden's history draws: the commit, and what it last changed (one commit in the translated copy)."""
        if isinstance(x, dict):
            return {k: unworded(v) for k, v in x.items() if k not in ('provenance', 'commit', 'day', 'changed')}
        if isinstance(x, list):
            if len(x) == 2 and all(isinstance(v, str) for v in x):     # a card's row: [fact, what it says]
                return ['', x[1]]
            return [unworded(v) for v in x]
        return x
    same = [k for k in ('views', 'order', 'reference', 'levels', 'units', 'addresses', 'techcat', 'opens_on')
            if unworded(pa.get(k)) == unworded(pb.get(k))]
    check("translation: the report draws the same page — its drawings, order, reference, lenses, units and addresses — "
          "but for the law's own words", len(same) == 8 and 'error' not in pa and 'error' not in pb,
          (same, str(pa)[:300], str(pb)[:300]))
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\ncore_view: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
