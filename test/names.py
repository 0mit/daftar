#!/usr/bin/env python3
"""The law's words in its readers' languages (core/law/core.yaml `layers[names]`, seed/names/<language>.tsv), as a page
shows them: every verb, every role, every qualifier a verb's row declares, the keys beside the roles, every kind, the
header's keys, and the attributes of the forms a sheet draws — each named in every language the tables carry, the
languages siblings, each row in its form; and the view reads them, so a sheet is in its reader's language.

  the tables   the nine files name the same items in the same order; each row is `item, name, roots, status, by`, its
               status `proposed` or `confirmed`, no tab inside a cell and no bidi control anywhere; each new item names
               a part of the law that exists — a verb of its rows, a role, a qualifier some verb declares, a key beside
               the roles, a kind, a header key, an attribute of a form; every verb and every role the law has is named;
               and within a language no two of them share a name
  the view     `view_engraved.names(<lang>)` gives a language's names by their group, and nothing for a language no
               table carries (no language stands in for another); a sheet drawn for a Persian reader heads a payment
               `پرداخت` and labels its payer `از سوی`, and one drawn for an English reader `pay` and `by`

Run: python3 test/names.py   (0 = green)
"""
import json, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, 'test')]
FAILS = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-1500:]))
    if not cond:
        FAILS.append(name)


import yaml  # noqa: E402
from core.law import Law  # noqa: E402
from core import engine  # noqa: E402

L = Law.load()
CORE = yaml.safe_load(open(os.path.join(ROOT, 'core', 'law', 'core.yaml'), encoding='utf-8'))
NAMES = os.path.join(ROOT, 'seed', 'names')
LANGS = sorted(f[:-4] for f in os.listdir(NAMES) if f.endswith('.tsv'))
BIDI = re.compile('[\u061c\u200e\u200f\u202a-\u202e\u2066-\u2069]')
GROUPS = ('verbs', 'roles', 'qualifiers', 'beside_roles', 'kinds', 'header', 'forms')

rows = {}
for lang in LANGS:
    with open(os.path.join(NAMES, f'{lang}.tsv'), encoding='utf-8') as fh:
        rows[lang] = [ln.split('\t') for ln in fh.read().splitlines()]

# ------------------------------------------------------------------ the tables
items = {lang: [r[0] for r in rs[1:]] for lang, rs in rows.items()}
first = items[LANGS[0]]
check(f"the {len(LANGS)} tables name the same items in the same order: siblings, no language a lesser copy",
      all(items[lang] == first for lang in LANGS), {lang: len(items[lang]) for lang in LANGS})
bad = [(lang, i, r) for lang, rs in rows.items() for i, r in enumerate(rs[1:], 2)
       if len(r) != 5 or r[3] not in ('proposed', 'confirmed') or not r[1].strip() or BIDI.search('\t'.join(r))]
check("each row is item, name, roots, status, by — its status proposed or confirmed, a name, no bidi control",
      not bad, bad[:5])

verbs = set(L.verbs)
roles = {r['role'] for r in CORE['roles']}
quals = {q for row in L.verbs.values() for q in (row.get('qualifiers') or {})}
beside = {b['key'] for b in CORE['beside_roles']}
kinds = set(L.kinds)
header = set(engine.HEADER) - {'bean', 'statements'}


def names_a_part(item):
    g, _s, w = item.partition(':')
    if g == 'forms':
        f, _d, a = w.partition('.')
        rec = (L.forms or {}).get(f) or {}
        return a in (rec.get('attrs') or rec.get('entries') or {})
    return w in {'verbs': verbs, 'roles': roles, 'qualifiers': quals, 'beside_roles': beside, 'kinds': kinds,
                 'header': header}.get(g, set())


new = [i for i in first if i.split(':', 1)[0] in GROUPS]
check("each item of the page's groups names a part of the law that exists — a verb, a role, a qualifier some verb "
      "declares, a key beside the roles, a kind, a header key, an attribute of a form",
      new and all(names_a_part(i) for i in new), [i for i in new if not names_a_part(i)][:8])
named = set(new)
check("every verb and every role the law has is named, so no sheet shows one in the law's word alone",
      {f'verbs:{v}' for v in verbs} | {f'roles:{r}' for r in roles} <= named,
      sorted(({f'verbs:{v}' for v in verbs} | {f'roles:{r}' for r in roles}) - named)[:10])
dup = {}
for lang, rs in rows.items():
    seen = {}
    for r in rs[1:]:
        if r[0].split(':', 1)[0] in GROUPS:
            seen.setdefault(r[1], []).append(r[0])
    dup[lang] = {n: i for n, i in seen.items() if len(i) > 1}
check("within a language no two of them share a name", not any(dup.values()), {k: v for k, v in dup.items() if v})

# ------------------------------------------------------------------ the view reads them
sys.path.insert(0, os.path.join(ROOT, 'assets', 'view', 'lib'))
import grow  # noqa: E402
T = tempfile.mkdtemp(prefix='names-')
try:
    rel = grow.release(os.path.join(T, 'release'))
    G = os.path.join(T, 'garden')
    r = grow.garden(rel, G, 'sam', '--gardener-name', 'Sam', '--profile', 'view')
    check("a garden grows taking the view profile", r.returncode == 0, r.out[-600:])
    with open(os.path.join(G, 'beans', 'camera.md'), 'w', encoding='utf-8') as fh:
        fh.write('---\nbean: camera\nkind: contract\ntitle: "camera"\nsummary: "a camera bought together"\nstatements:\n'
                 '  - say: { by: sam, at: now }\n  - own: { by: theone, of: self }\n'
                 '  - pay: { id: paid, by: sam, of: { count: "90.00", unit: XTS } }\n---\nA camera.\n')
    with open(os.path.join(G, 'beans', 'page.md'), 'w', encoding='utf-8') as fh:
        fh.write('---\nbean: page\nkind: service\ntitle: "page"\nsummary: "a page"\nstatements:\n'
                 '  - say: { by: sam, at: now }\n  - own: { by: sam, of: self }\n'
                 '  - be: { by: self, at: "uri:https://garden.example.org/", as: location }\n'
                 '  - draw: { id: camera, by: self, of: [camera], drawing: { label: Camera, archetype: sheet, purpose: "the camera", '
                 'outcome: "the camera", stages: [ { label: a, doer: b }, { label: c, doer: d }, { label: e, doer: f } ], '
                 'questions: [ { lens: orient, ask: "what?" } ], blind: [ { what: nothing } ] } }\n'
                 '  - draw: { id: page, by: self, of: [camera], page: { fields: [ { kind: contract, fact: pay, shown_from: understand } ] } }\n'
                 '---\nA page.\n')
    s = grow.run(sys.executable, 'bin/save.py', 'sam', 'a camera and its page', '--body', '- action: wrote [[camera]] and [[page]]', cwd=G)
    check("a camera and a page of its sheet are saved", s.returncode == 0, s.out[-800:])
    code = ("import json, sys; sys.path.insert(0, 'assets/view/lib'); import view_model as vm, view_engraved as ve; vm.init('.', 'page'); "
            "print(json.dumps({l: ve.names(l) for l in ('fa', 'en', 'sv', 'fa-IR')}, ensure_ascii=False))")
    s = grow.run(sys.executable, '-c', code, cwd=G)
    try:
        N = json.loads(s.out.strip().splitlines()[-1])
    except (ValueError, IndexError):
        N = {'error': s.out[-900:]}
    fa = (N.get('fa') or {})
    check("names('fa') gives the Persian of the law's words by their group: pay پرداخت, by از سوی, contract قرارداد",
          (fa.get('verbs') or {}).get('pay') == 'پرداخت' and (fa.get('roles') or {}).get('by') == 'از سوی'
          and (fa.get('kinds') or {}).get('contract') == 'قرارداد', N)
    check("...a reader's tag with its region reads its language's table, and a language no table carries gets nothing: "
          "no language stands in for another", ((N.get('fa') or {}).get('verbs') or {}).get('pay') and N.get('fa-IR') == N.get('fa')
          and isinstance(N.get('sv'), dict) and not any(N['sv'].values()), N)
    browser = next((b for b in ('chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable') if shutil.which(b)), None)
    DRIVE = """<script>
window.__errs = []; window.addEventListener('error', e => window.__errs.push(String(e.message)));
window.addEventListener('load', () => { let sheet = '';
 try { document.querySelector('.tab[data-t="camera"]').click(); document.querySelector('#lens button[data-l="understand"]').click();
  sheet = document.querySelector('#view .eg-sheet, #view .eg').innerText; } catch (e) { window.__errs.push('driver: ' + e.message); }
 const pre = document.createElement('pre'); pre.id = '__result'; pre.textContent = JSON.stringify({errs: window.__errs, sheet}); document.body.appendChild(pre); });
</script>"""
    import html as _html
    for lang, verb, role in (('fa', 'پرداخت', 'از سوی'), ('en', 'pay', 'by')):
        out = os.path.join(T, f'page-{lang}.html')
        s = grow.run(sys.executable, 'assets/view/bin/view.py', 'report', '--out', out, '--lang', lang, cwd=G)
        if not browser or s.returncode != 0:
            check(f"the report in {lang} is written", s.returncode == 0, s.out[-600:])
            continue
        dr = os.path.join(T, f'drive-{lang}.html')
        with open(dr, 'w', encoding='utf-8') as fh:
            fh.write(open(out, encoding='utf-8').read().replace('<head>', '<head>' + DRIVE, 1))
        p = subprocess.run([browser, '--headless=new', '--disable-gpu', '--no-sandbox', '--virtual-time-budget=6000', '--dump-dom',
                            'file://' + dr], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=120)
        m = re.search(r'<pre id="__result">(.*?)</pre>', p.stdout, re.S)
        res = json.loads(_html.unescape(m.group(1))) if m else {'errs': ['no result'], 'sheet': ''}
        check(f"a sheet drawn for a reader of {lang} heads the payment «{verb}» and labels its payer «{role}»",
              not res['errs'] and verb in res['sheet'] and role in res['sheet'], res)
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\nnames: {len(FAILS)} failed" + (": " + ", ".join(FAILS) if FAILS else ""))
sys.exit(1 if FAILS else 0)
