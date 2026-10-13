#!/usr/bin/env python3
"""A reader's way of reading as a bean, for backup and for carrying to another machine — and back, losing nothing
(assets/view/lib/view_prefs.py `to_bean`, `from_bean`, `export`, `import`; the view profile's form `reader_preferences`).
The host's own file stays the source of truth: a reader's preferences are kept with their account on each machine,
never in a garden, and a bean of them is a file a person carries, which a garden holds only if a person puts it there.

  the law      the type `locale_tag` (a BCP 47 tag with its Unicode extension); the view profile's tables `date_styles`
               and `currency_displays` (Intl's own words, the ones view_prefs keeps) and its form `reader_preferences`,
               which a `draw` holds (`preferences`): the bean draws its reader's way of reading
  both ways    preferences → bean → preferences is the same, every key, an unset key staying unset; bean → preferences →
               bean is the same text; a tag written out of order or case goes out in its canonical form
  refused      a bean whose tag CLDR has no type for, one of no reader, one that is no preferences — each by name
  the host     view_serve's configuration: Sam's preferences exported to a bean, the file's own preferences cleared, the
               bean imported back — the account as it was, its password hash and every other key untouched, nothing
               printed of it; a bean of another reader refused, the file unchanged
  the gate     in a garden taking the view profile, an exported bean saved through the gate; one holding a day's style no
               table has, refused by name; in a garden that does not take the view profile, refused as the view's

A garden of the core is grown (test/grow.py), Sam its gardener, a reader beside them.

Run: python3 test/view_prefs_bean.py   (0 = green)
"""
import json, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, 'assets', 'view', 'lib'), os.path.join(ROOT, 'test')]
import grow  # noqa: E402
import view_prefs  # noqa: E402

PY = sys.executable
FAILS, TRACES = [], []
READER = 'p-0a1b2c3d'
FULL = {'locale': 'en-u-ca-persian-fw-sat-hc-h12-nu-latn-tz-usnyc', 'date': 'full', 'currency': 'name'}


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-1500:]))
    if not cond:
        FAILS.append(name)


def run(*a, cwd=None):
    r = subprocess.run(list(a), capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=cwd, env=grow.ENV)
    out = r.stdout + r.stderr
    if 'Traceback' in out:
        TRACES.append(out[-1200:])
    return r.returncode, out


def put(root, rel, text):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)


# ------------------------------------------------------------------ the law
from core.check import garden_law  # noqa: E402
L = garden_law(ROOT)
import yaml  # noqa: E402
lines = yaml.safe_load(open(os.path.join(ROOT, 'core', 'law', 'lines.yaml'), encoding='utf-8'))
tag_type = next((t for t in lines.get('types') or [] if t.get('type') == 'locale_tag'), None)
check("the law has the type `locale_tag`: a BCP 47 tag with its Unicode extension, by a pattern that takes every "
      "canonical tag view_prefs writes and refuses one with another extension",
      tag_type is not None and all(re.fullmatch(tag_type['pattern'], t) for t in (
          'fa', 'fa-u-ca-persian-nu-arabext', 'pt-BR', 'sr-Latn-RS-u-nu-latn', FULL['locale'],
          view_prefs.check({'locale': 'EN-u-NU-latn-CA-persian'})[0]['locale']))
      and not re.fullmatch(tag_type['pattern'], 'en-t-ru') and not re.fullmatch(tag_type['pattern'], 'en-u-xx-yes'),
      tag_type)
view = (getattr(L, 'profiles', {}) or {}).get('view') or {}
check("the view profile takes the tables `date_styles` and `currency_displays` — Intl's own words, the ones view_prefs "
      "keeps — and the form `reader_preferences`",
      {'date_styles', 'currency_displays'} <= set(view.get('tables') or []) and 'reader_preferences' in (view.get('forms') or [])
      and L.tables.get('date_styles') == list(view_prefs.DATE) and L.tables.get('currency_displays') == list(view_prefs.CURRENCY),
      (view.get('tables'), view.get('forms'), L.tables.get('date_styles'), L.tables.get('currency_displays')))
form = (L.forms or {}).get('reader_preferences') or {}
draw = L.verbs.get('draw') or {}
check("the form holds the garden it was set in, the tag, the day's style and the currency's naming; a `draw` holds it "
      "(`preferences`), beside a page and a drawing",
      set((form.get('attrs') or {})) == {'garden', 'locale', 'date', 'currency'}
      and ((draw.get('qualifiers') or {}).get('preferences') or {}).get('form') == 'reader_preferences'
      and 'preferences' in ((draw.get('choice') or {}).get('one_of') or []), (form, draw))

# ------------------------------------------------------------------ both ways
to_bean, from_bean = getattr(view_prefs, 'to_bean', None), getattr(view_prefs, 'from_bean', None)
if not (to_bean and from_bean):
    check("view_prefs writes a reader's preferences as a bean and reads them back (`to_bean`, `from_bean`)", False,
          'this release has no to_bean / from_bean')
    print(f"\nview_prefs_bean: {len(FAILS)} failed")
    sys.exit(1)
cases = [FULL, {'locale': 'fa-u-ca-persian-nu-arabext'}, {'date': 'short'}, {'currency': 'narrowSymbol', 'date': 'medium'}, {}]
same, again = [], []
for p in cases:
    text = to_bean(p, READER, garden='0123456789ab')
    got = from_bean(text)
    same.append(got['prefs'] == view_prefs.check(p)[0] and got['reader'] == READER and got['garden'] == '0123456789ab')
    again.append(to_bean(got['prefs'], got['reader'], garden=got['garden']) == text)
check("preferences → bean → preferences: the same, every key, an unset key staying unset, the reader and the garden "
      "kept", all(same), same)
check("bean → preferences → bean: the same text", all(again), again)
messy = to_bean({'locale': 'EN-u-NU-latn-CA-persian'}, READER)
check("a tag written out of order or case goes out in its canonical form",
      from_bean(messy)['prefs'] == {'locale': 'en-u-ca-persian-nu-latn'} and from_bean(messy)['garden'] is None, messy)


def refused(text):
    try:
        from_bean(text)
    except view_prefs.Refused as e:
        return str(e)
    return None


bad_tag = to_bean({'locale': 'fa-u-nu-arabext'}, READER).replace('nu-arabext', 'nu-nosuchdigits')
check("refused by name: a tag CLDR has no type for, a bean that names no reader, a bean that is no preferences",
      'nosuchdigits' in (refused(bad_tag) or '')
      and 'reader' in (refused(to_bean(FULL, READER).replace(f'of: [{READER}]', 'of: []')) or '')
      and 'preferences' in (refused('---\nbean: x\nkind: document\ntitle: "x"\nstatements:\n  - say: { by: sam, at: now }\n---\nx\n') or ''),
      (refused(bad_tag), refused('---\nbean: x\nkind: document\n---\nx\n')))
try:
    view_prefs.to_bean({'date': 'tiny'}, READER)
    wrote_bad = True
except view_prefs.Refused:
    wrote_bad = False
check("...and nothing is written of preferences that are not (a day's style no table has)", not wrote_bad)

# ------------------------------------------------------------------ the host's own file, and the gate
T = tempfile.mkdtemp(prefix='prefs-bean-')
try:
    rel = grow.release(os.path.join(T, 'release'))
    G = os.path.join(T, 'garden')
    r = grow.garden(rel, G, 'sam', '--gardener-name', 'Sam', '--profile', 'view')
    check("a garden of the core grows taking the view profile, kept by Sam", r.returncode == 0, r.out[-600:])
    put(G, f'beans/{READER}.md', f'---\nbean: {READER}\nkind: person\ntitle: "{READER}"\nsummary: "a reader"\n'
        'statements:\n  - say: { by: sam, at: now }\n  - own: { by: theone, of: self }\n---\nA reader.\n')
    rc, out = run(PY, 'bin/save.py', 'sam', 'a reader', '--body', f'- action: wrote [[{READER}]]', cwd=G)
    check("the reader is saved", rc == 0, out[-800:])
    VS = os.path.join(G, 'assets', 'view', 'lib', 'view_prefs.py')
    cfg = os.path.join(T, 'host', 'serve.json')
    sys.path.insert(0, os.path.join(G, 'assets', 'view', 'lib'))
    import view_serve  # noqa: E402 — the host's own hash, so the file is as the host writes it
    host = {'listen': '127.0.0.1:8780', 'monitors': {}, 'history': '', 'tools': {},
            'users': {u: {'password': view_serve.hash_password('not-a-real-password'), 'orgs': ['*'], 'shared': False,
                          'beans': [], 'actions': True, 'bean': b} for u, b in (('sam', 'sam'), ('ada', READER))}}
    os.makedirs(os.path.dirname(cfg), exist_ok=True)
    with open(cfg, 'w', encoding='utf-8') as fh:
        json.dump(host, fh, indent=1)
    c = json.load(open(cfg, encoding='utf-8'))
    c['users']['sam'].update(FULL)
    c['users']['ada'].update({'locale': 'fa-u-nu-latn'})
    with open(cfg, 'w', encoding='utf-8') as fh:
        json.dump(c, fh, indent=1)
    before = json.load(open(cfg, encoding='utf-8'))
    out_bean = os.path.join(T, 'carried', 'sam.md')
    rc, out = run(PY, VS, 'export', '--config', cfg, '--user', 'sam', '--garden', G, '--out', out_bean, cwd=T)
    exported = open(out_bean, encoding='utf-8').read() if os.path.exists(out_bean) else ''
    check("export: Sam's preferences written to a bean, nothing of the account printed or written beside them",
          rc == 0 and from_bean(exported)['prefs'] == FULL and 'password' not in exported and 'password' not in out
          and (before['users']['sam'].get('password') or 'x') not in out, out[-600:])
    c = json.load(open(cfg, encoding='utf-8'))
    for k in ('locale', 'date', 'currency'):
        c['users']['sam'].pop(k, None)
    with open(cfg, 'w', encoding='utf-8') as fh:
        json.dump(c, fh, indent=1)
    rc, out = run(PY, VS, 'import', out_bean, '--config', cfg, cwd=T)
    after = json.load(open(cfg, encoding='utf-8'))
    check("import: the bean read back into the host's own file — the account as it was, every other key untouched "
          "(its password hash among them), the other account untouched, nothing printed of it",
          rc == 0 and after == before and 'password' not in out, (out[-400:], sorted(after['users']['sam'])))
    ada_bean = os.path.join(T, 'carried', 'ada.md')
    rc, out = run(PY, VS, 'export', '--config', cfg, '--user', 'ada', '--garden', G, '--out', ada_bean, cwd=T)
    rc, out = run(PY, VS, 'import', ada_bean, '--config', cfg, '--user', 'sam', cwd=T)
    check("a bean of another reader is refused for Sam's account, by name; the file unchanged",
          rc != 0 and READER in out and json.load(open(cfg, encoding='utf-8')) == before, out[-400:])
    # the gate: a bean a person puts in the garden
    bid = re.search(r'^bean: (\S+)', exported, re.M).group(1) if exported else 'none'
    shutil.copy(out_bean, os.path.join(G, 'beans', f'{bid}.md'))
    rc, out = run(PY, 'bin/save.py', 'sam', 'my way of reading, kept', '--body', f'- action: wrote [[{bid}]]', cwd=G)
    check("the gate: an exported bean, put in a garden taking the view profile, is saved", rc == 0 and '0 error' in out,
          out[-900:])
    with open(os.path.join(G, 'beans', f'{bid}.md'), encoding='utf-8') as fh:
        text = fh.read()
    put(G, f'beans/{bid}.md', text.replace('date: "full"', 'date: "tiny"').replace(FULL['locale'], 'en-u-nu-latn-ca-persian'))
    rc, out = run(PY, 'core/check.py', cwd=G)
    check("...one holding a day's style no table has, and a tag out of its canonical form, is refused, each by name",
          rc != 0 and "'tiny'" in out and 'en-u-nu-latn-ca-persian' in out, out[-900:])
    run('git', 'checkout', '--', '.', cwd=G)
    # a garden that does not take the view profile
    H = os.path.join(T, 'bare')
    r = grow.garden(rel, H, 'sam', '--gardener-name', 'Sam')
    shutil.copy(os.path.join(G, 'beans', f'{bid}.md'), os.path.join(H, 'beans', f'{bid}.md'))
    rc, out = run(PY, 'core/check.py', cwd=H)
    check("...and in a garden that does not take the view profile, refused as the view's", rc != 0 and 'view' in out,
          out[-900:])
finally:
    if TRACES:
        print("TRACEBACKS:\n" + "\n---\n".join(TRACES[:3]))
    shutil.rmtree(T, ignore_errors=True)

print(f"\nview_prefs_bean: {len(FAILS)} failed" + (": " + ", ".join(FAILS) if FAILS else ""))
sys.exit(1 if FAILS or TRACES else 0)
